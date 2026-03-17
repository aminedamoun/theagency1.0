"""Notification system — sends alerts to phone when tasks complete.

Supports:
1. ntfy.sh — zero setup, just subscribe to a topic URL on phone
2. Telegram Bot — create a bot, paste token + chat_id
3. In-app — browser Notification API
"""

import os
import json
import logging
import asyncio
from datetime import datetime

import httpx

logger = logging.getLogger("amine-agent")


# ---- Configuration ----

def _get_config() -> dict:
    """Load notification config from env or defaults."""
    return {
        "ntfy_enabled": os.getenv("NTFY_ENABLED", "true").lower() == "true",
        "ntfy_topic": os.getenv("NTFY_TOPIC", "dubai-prod-agent"),
        "ntfy_server": os.getenv("NTFY_SERVER", "https://ntfy.sh"),
        "telegram_enabled": os.getenv("TELEGRAM_BOT_TOKEN", "") != "",
        "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    }


# ---- Send Notifications ----

async def notify(title: str, message: str, priority: str = "default", tags: str = ""):
    """Send notification to all enabled channels including WhatsApp group."""
    config = _get_config()
    tasks = []

    if config["ntfy_enabled"]:
        tasks.append(_send_ntfy(config, title, message, priority, tags))

    if config["telegram_enabled"]:
        tasks.append(_send_telegram(config, title, message))

    # Always try to push to WhatsApp group (silently fails if bot not running)
    tasks.append(_send_whatsapp_group(title, message))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(f"[notify] {title}: {message[:80]}")


async def _send_whatsapp_group(title: str, message: str):
    """Send WhatsApp message via Meta Cloud API (works 24/7, no local bot needed)."""
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    owner_phone = os.getenv("WHATSAPP_OWNER_PHONE")

    if not token or not phone_id or not owner_phone:
        return  # WhatsApp Cloud API not configured

    url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
    text = f"🔔 *{title}*\n{message}"

    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(url, json={
                "messaging_product": "whatsapp",
                "to": owner_phone,
                "type": "text",
                "text": {"body": text},
            }, headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            })
    except Exception as e:
        logger.error(f"[notify] WhatsApp Cloud API failed: {e}")


async def _send_ntfy(config: dict, title: str, message: str, priority: str, tags: str):
    """Send via ntfy.sh — user subscribes at ntfy.sh/TOPIC on their phone."""
    url = f"{config['ntfy_server']}/{config['ntfy_topic']}"
    # ntfy uses JSON mode for unicode support (emojis in title/message)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                "topic": config['ntfy_topic'],
                "title": title,
                "message": message,
                "priority": 3 if priority == "default" else (5 if priority == "urgent" else 4 if priority == "high" else 2),
                "tags": (tags or "robot").split(","),
            })
    except Exception as e:
        logger.error(f"[notify] ntfy failed: {e}")


async def _send_telegram(config: dict, title: str, message: str):
    """Send via Telegram Bot API."""
    token = config["telegram_token"]
    chat_id = config["telegram_chat_id"]
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = f"🏢 *{title}*\n\n{message}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
    except Exception as e:
        logger.error(f"[notify] Telegram failed: {e}")


# ---- Pre-built notification triggers ----

async def notify_task_completed(task_title: str, agent_name: str):
    await notify(
        title="Task Completed ✅",
        message=f"{agent_name} finished: {task_title}",
        priority="default",
        tags="white_check_mark",
    )


async def notify_video_ready(filename: str):
    await notify(
        title="Video Ready 🎬",
        message=f"New video generated: {filename}",
        priority="default",
        tags="movie_camera",
    )


async def notify_report_ready(filename: str):
    await notify(
        title="Report Ready 📄",
        message=f"PDF report generated: {filename}",
        priority="default",
        tags="page_facing_up",
    )


async def notify_email_sent(to: str, subject: str):
    await notify(
        title="Email Sent 📧",
        message=f"To: {to}\nSubject: {subject}",
        priority="low",
        tags="email",
    )


async def notify_content_published(platform: str, content_type: str):
    await notify(
        title="Content Published 🚀",
        message=f"{platform} {content_type} is now live!",
        priority="high",
        tags="rocket",
    )


async def notify_custom(title: str, message: str):
    await notify(title=title, message=message)
