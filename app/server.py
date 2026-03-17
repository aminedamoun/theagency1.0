"""Dubai Prod Agent — FastAPI backend."""

import asyncio
import json
import logging
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.logger import setup_logger
from app.database import init_db
from app.api import router as api_router

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("[db] Database initialized")
    yield


app = FastAPI(title="Dubai Prod Agent", lifespan=lifespan)
app.include_router(api_router)

STATIC_DIR = Path(__file__).parent / "static"
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    intro = STATIC_DIR / "intro.html"
    return HTMLResponse(intro.read_text())


@app.get("/intro")
async def intro():
    page = STATIC_DIR / "intro.html"
    return HTMLResponse(page.read_text())


@app.get("/spaces")
async def spaces():
    page = STATIC_DIR / "spaces.html"
    return HTMLResponse(page.read_text())


@app.get("/platform")
async def platform():
    index = STATIC_DIR / "index.html"
    return HTMLResponse(index.read_text())


@app.get("/space/leads")
async def space_leads():
    page = STATIC_DIR / "space-leads.html"
    return HTMLResponse(page.read_text())


@app.get("/space/content")
async def space_content():
    page = STATIC_DIR / "space-content.html"
    return HTMLResponse(page.read_text())


@app.get("/space/creative")
async def space_creative():
    page = STATIC_DIR / "space-creative.html"
    return HTMLResponse(page.read_text())


@app.get("/space/dashboard")
async def space_dashboard():
    page = STATIC_DIR / "space-dashboard.html"
    return HTMLResponse(page.read_text())


@app.get("/space/email")
async def space_email():
    page = STATIC_DIR / "space-email.html"
    return HTMLResponse(page.read_text())


@app.get("/space/creative-choice")
async def space_creative_choice():
    page = STATIC_DIR / "space-creative-choice.html"
    return HTMLResponse(page.read_text())


@app.get("/space/sheets")
async def space_sheets():
    page = STATIC_DIR / "space-sheets.html"
    return HTMLResponse(page.read_text())


@app.get("/space/video")
async def space_video():
    page = STATIC_DIR / "space-video.html"
    return HTMLResponse(page.read_text())


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    dest = UPLOADS_DIR / safe_name
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    logger.info(f"[upload] Saved: {dest}")
    return {"filename": safe_name, "path": str(dest)}


async def handle_command(message: str, websocket: WebSocket):
    msg = message.strip()
    await websocket.send_json({"type": "typing", "content": ""})

    try:
        # Everything goes through the brain — it has tools for all actions
        # Only keep /browse separate because it takes long and needs status updates
        if msg.startswith("/browse "):
            task = msg[8:].strip()
            if not task:
                await websocket.send_json({"type": "reply", "content": "Usage: /browse <task>"})
                return
            from browser.agent import run_browser_task
            await websocket.send_json({"type": "status", "content": "Launching browser..."})
            result = await run_browser_task(task)
            await websocket.send_json({"type": "reply", "content": result})

        elif msg.startswith("/send "):
            parts = msg[6:].strip().split("|")
            if len(parts) < 3:
                await websocket.send_json({
                    "type": "reply",
                    "content": "Usage: /send to@email.com | Subject | Body text"
                })
                return
            to, subject, body = parts[0].strip(), parts[1].strip(), parts[2].strip()
            preview = f"**To:** {to}\n**Subject:** {subject}\n\n{body}"
            await websocket.send_json({
                "type": "confirm",
                "content": f"Send this email?\n\n{preview}",
                "action": "send_email",
                "data": {"to": to, "subject": subject, "body": body},
            })

        elif msg.startswith("/organize "):
            path = msg[10:].strip()
            from files.organizer import scan_directory as scan_dir, plan_organization, show_plan
            recursive = "--recursive" in path
            path = path.replace("--recursive", "").strip()
            scan = await asyncio.to_thread(scan_dir, path, recursive)
            actions = plan_organization(scan)
            plan_text = show_plan(actions)
            await websocket.send_json({
                "type": "confirm",
                "content": plan_text,
                "action": "organize",
                "data": {"path": path, "recursive": recursive},
            })

        else:
            # Everything else goes to the AI brain
            await _chat_reply(msg, websocket)

    except Exception as e:
        logger.error(f"[agent] Error: {e}")
        await websocket.send_json({"type": "error", "content": f"Error: {str(e)}"})


async def _chat_reply(message: str, websocket: WebSocket):
    from agents.brain import chat
    reply = await chat(message)
    await websocket.send_json({"type": "reply", "content": reply})


async def _agent_chat_reply(message: str, agent_key: str, websocket: WebSocket):
    from agents.brain import chat_agent, AGENTS
    if agent_key not in AGENTS:
        await websocket.send_json({"type": "error", "content": f"Unknown agent: {agent_key}"})
        return
    a = AGENTS[agent_key]
    await websocket.send_json({"type": "agent_typing", "agent": agent_key, "name": a["name"]})
    try:
        reply = await chat_agent(message, agent_key)
        await websocket.send_json({"type": "agent_reply", "content": reply, "agent": agent_key})
    except Exception as e:
        logger.error(f"[agent_chat] {agent_key} error: {e}")
        await websocket.send_json({"type": "agent_reply", "content": f"Sorry, I encountered an error: {str(e)}", "agent": agent_key})


async def _meeting_reply(message: str, websocket: WebSocket):
    from agents.brain import chat_meeting
    await websocket.send_json({"type": "meeting_typing"})
    try:
        reply = await chat_meeting(message)
        await websocket.send_json({"type": "meeting_reply", "content": reply})
    except Exception as e:
        logger.error(f"[meeting] error: {e}")
        await websocket.send_json({"type": "meeting_reply", "content": f"*Meeting disrupted — error: {str(e)}*"})


async def handle_confirm(data: dict, websocket: WebSocket):
    action = data.get("action")
    action_data = data.get("data", {})

    try:
        if action == "organize":
            from files.organizer import organize_directory
            log = await asyncio.to_thread(
                organize_directory,
                action_data["path"],
                action_data.get("recursive", False),
                confirm_callback=lambda _: True,
            )
            await websocket.send_json({"type": "reply", "content": "\n".join(log)})

        elif action == "send_email":
            from email_agent.sender import send_email
            sent = await asyncio.to_thread(
                send_email,
                to=action_data["to"],
                subject=action_data["subject"],
                body=action_data["body"],
                confirm_callback=lambda _: True,
            )
            if sent:
                await websocket.send_json({"type": "reply", "content": "Email sent successfully!"})
            else:
                await websocket.send_json({"type": "reply", "content": "Failed to send email."})

    except Exception as e:
        await websocket.send_json({"type": "error", "content": f"Error: {str(e)}"})


# Track all connected clients for push updates
_ws_clients: set[WebSocket] = set()


async def push_refresh(event: str = "data_changed"):
    """Push a refresh signal to all connected clients."""
    dead = set()
    for ws_client in _ws_clients:
        try:
            await ws_client.send_json({"type": "refresh", "event": event})
        except Exception:
            dead.add(ws_client)
    _ws_clients -= dead


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    logger.info(f"[ws] Client connected ({len(_ws_clients)} total)")
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                asyncio.create_task(handle_command(data["content"], websocket))
            elif data.get("type") == "agent_chat":
                asyncio.create_task(_agent_chat_reply(data["content"], data["agent"], websocket))
            elif data.get("type") == "meeting":
                asyncio.create_task(_meeting_reply(data["content"], websocket))
            elif data.get("type") == "confirm_yes":
                await handle_confirm(data, websocket)
            elif data.get("type") == "confirm_no":
                await websocket.send_json({"type": "reply", "content": "Cancelled."})

    except WebSocketDisconnect:
        _ws_clients.discard(websocket)
        logger.info(f"[ws] Client disconnected ({len(_ws_clients)} total)")
