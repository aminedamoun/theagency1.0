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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Request, Response, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import hashlib, secrets

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

# ── Authentication ────────────────────────────────────────────────────────────
AUTH_EMAIL = os.getenv("AUTH_EMAIL", "info@dubaiprod.com")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "agency2026")
_active_sessions: set[str] = set()


def _check_auth(request: Request) -> bool:
    token = request.cookies.get("session_token")
    return token in _active_sessions if token else False


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Login — THE AGENCY 1.0</title>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;background:#020509;font-family:'Segoe UI',system-ui,sans-serif;color:#fff}
body{display:flex;align-items:center;justify-content:center}
.login-box{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
  border-radius:16px;padding:48px 40px;width:380px;backdrop-filter:blur(20px)}
.login-box h1{font-size:22px;font-weight:600;margin-bottom:6px;
  background:linear-gradient(135deg,#c9a84c,#ffe08a);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.login-box p{font-size:13px;color:rgba(255,255,255,0.4);margin-bottom:28px}
label{display:block;font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:6px;text-transform:uppercase;letter-spacing:1px}
input{width:100%;padding:12px 14px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
  border-radius:8px;color:#fff;font-size:14px;margin-bottom:18px;outline:none;transition:border 0.2s}
input:focus{border-color:rgba(201,168,76,0.5)}
button{width:100%;padding:13px;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;
  background:linear-gradient(135deg,#c9a84c,#b8943f);color:#020509;transition:opacity 0.2s}
button:hover{opacity:0.9}
.error{color:#ff6b6b;font-size:13px;margin-bottom:14px;display:none}
</style>
</head>
<body>
<div class="login-box">
  <h1>THE AGENCY 1.0</h1>
  <p>Enter your credentials to access the platform</p>
  <div class="error" id="err">Invalid email or password</div>
  <form method="POST" action="/login">
    <label>Email</label>
    <input type="email" name="email" required placeholder="your@email.com" autocomplete="email">
    <label>Password</label>
    <input type="password" name="password" required placeholder="••••••••" autocomplete="current-password">
    <input type="hidden" name="next" value="{next_url}">
    <button type="submit">Sign In</button>
  </form>
</div>
</body></html>"""


@app.get("/login")
async def login_page(request: Request, next: str = "/spaces"):
    if _check_auth(request):
        return RedirectResponse(url=next)
    return HTMLResponse(LOGIN_PAGE.replace("{next_url}", next))


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    email = form.get("email", "")
    password = form.get("password", "")
    next_url = form.get("next", "/spaces")

    if email == AUTH_EMAIL and password == AUTH_PASSWORD:
        token = secrets.token_hex(32)
        _active_sessions.add(token)
        response = RedirectResponse(url=next_url, status_code=302)
        response.set_cookie("session_token", token, httponly=True, max_age=86400 * 7, samesite="lax")
        logger.info(f"[auth] Login success: {email}")
        return response

    html = LOGIN_PAGE.replace("{next_url}", next_url).replace('display:none', 'display:block')
    return HTMLResponse(html, status_code=401)


@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        _active_sessions.discard(token)
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_token")
    return response


def _protected_page(page_path: str):
    async def handler(request: Request):
        if not _check_auth(request):
            return RedirectResponse(url=f"/login?next={request.url.path}")
        return HTMLResponse((STATIC_DIR / page_path).read_text())
    return handler


# ── Public routes ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    intro = STATIC_DIR / "intro.html"
    return HTMLResponse(intro.read_text())


@app.get("/intro")
async def intro():
    page = STATIC_DIR / "intro.html"
    return HTMLResponse(page.read_text())


# ── Protected routes (require login) ─────────────────────────────────────────

@app.get("/spaces")
async def spaces(request: Request):
    if not _check_auth(request):
        return RedirectResponse(url="/login?next=/spaces")
    return HTMLResponse((STATIC_DIR / "spaces.html").read_text())


@app.get("/platform")
async def platform(request: Request):
    if not _check_auth(request):
        return RedirectResponse(url="/login?next=/platform")
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


app.add_api_route("/space/leads", _protected_page("space-leads.html"), methods=["GET"])
app.add_api_route("/space/content", _protected_page("space-content.html"), methods=["GET"])
app.add_api_route("/space/creative", _protected_page("space-creative.html"), methods=["GET"])
app.add_api_route("/space/dashboard", _protected_page("space-dashboard.html"), methods=["GET"])
app.add_api_route("/space/email", _protected_page("space-email.html"), methods=["GET"])
app.add_api_route("/space/creative-choice", _protected_page("space-creative-choice.html"), methods=["GET"])
app.add_api_route("/space/sheets", _protected_page("space-sheets.html"), methods=["GET"])
app.add_api_route("/space/video", _protected_page("space-video.html"), methods=["GET"])


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
