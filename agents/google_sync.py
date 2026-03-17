"""Google Drive + Sheets sync for Dubai Prod Agent.

When a workflow completes:
  1. Upload voiceovers, images, and mixed audio to a Google Drive project folder
  2. Append a fully-formatted row to the 📋 Content Library tab
  3. All links, scripts, captions, hashtags — auto-filled

Setup: run `python scripts/setup_google.py` once to authenticate.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("amine-agent")

UPLOADS_DIR      = Path(__file__).resolve().parent.parent / "uploads"
CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "config" / "google_credentials.json"
TOKEN_FILE       = Path(__file__).resolve().parent.parent / "config" / "google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Matches the 18 columns in 📋 Content Library (built by setup_google.py)
CONTENT_LIBRARY_TAB = "📋 Content Library"

COLUMNS = [
    "#", "Client", "Title / Idea", "Sources", "Platform", "Type",
    "Script", "Caption", "Hashtags",
    "Date Created", "Publish Date", "Status",
    "Cover Image", "Video", "Voiceover", "Final Audio", "Drive Folder", "Notes"
]


# ============================================================
# CREDENTIALS
# ============================================================

def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "Google credentials not found. "
                    "Save config/google_credentials.json then run: python scripts/setup_google.py"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.parent.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def is_configured() -> bool:
    return TOKEN_FILE.exists() and CREDENTIALS_FILE.exists()


# ============================================================
# GOOGLE DRIVE
# ============================================================

def _drive_service():
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=_get_credentials())


def _get_or_create_folder(service, name: str, parent_id: str = None) -> str:
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    logger.info(f"[google] Drive folder created: {name}")
    return folder["id"]


def _upload_file(service, local_path: Path, folder_id: str) -> str:
    from googleapiclient.http import MediaFileUpload
    mime_map = {
        ".mp3": "audio/mpeg", ".mp4": "video/mp4", ".wav": "audio/wav",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
    }
    mime = mime_map.get(local_path.suffix.lower(), "application/octet-stream")
    meta = {"name": local_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
    f = service.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    service.permissions().create(fileId=f["id"], body={"type": "anyone", "role": "reader"}).execute()
    logger.info(f"[google] Uploaded: {local_path.name}")
    return f.get("webViewLink", "")


def upload_assets_to_drive(workflow_id: int, title: str, stage_outputs: dict) -> dict:
    """Upload all workflow media files to a per-project Drive folder."""
    if not is_configured():
        return {}
    try:
        service = _drive_service()
        root_id = _get_or_create_folder(service, "Dubai Prod — Content Studio")
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = re.sub(r'[^\w\s-]', '', title)[:55].strip()
        project_folder_id = _get_or_create_folder(service, f"{date_str} — {safe_title}", root_id)

        links = {"drive_folder": f"https://drive.google.com/drive/folders/{project_folder_id}"}

        # Voiceover
        vo_web = stage_outputs.get("voiceover", "")
        if vo_web and vo_web.startswith("/uploads/"):
            p = UPLOADS_DIR / vo_web.replace("/uploads/", "")
            if p.exists():
                links["voiceover"] = _upload_file(service, p, project_folder_id)

        # Mixed audio
        mix_web = stage_outputs.get("audio_mix", "")
        if mix_web and mix_web.startswith("/uploads/"):
            p = UPLOADS_DIR / mix_web.replace("/uploads/", "")
            if p.exists():
                links["final_audio"] = _upload_file(service, p, project_folder_id)

        # Images from creative stage
        creative_out = stage_outputs.get("creative", "") or ""
        image_links = []
        for m in re.finditer(r'/uploads/[\w\-_.]+\.(?:png|jpg|jpeg)', creative_out):
            p = UPLOADS_DIR / m.group(0).replace("/uploads/", "")
            if p.exists():
                lnk = _upload_file(service, p, project_folder_id)
                image_links.append(lnk)
        if image_links:
            links["cover_image"] = image_links[0]          # first image = cover
            links["all_images"] = "\n".join(image_links)

        # Video
        for stage in ("video_render", "creative"):
            out = stage_outputs.get(stage, "") or ""
            for m in re.finditer(r'/uploads/[\w\-_.]+\.mp4', out):
                p = UPLOADS_DIR / m.group(0).replace("/uploads/", "")
                if p.exists():
                    links["video"] = _upload_file(service, p, project_folder_id)
                    break

        logger.info(f"[google] Drive upload done for workflow {workflow_id}")
        return links

    except Exception as e:
        logger.error(f"[google] Drive upload error: {e}")
        return {}


# ============================================================
# GOOGLE SHEETS
# ============================================================

def _sheets_service():
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=_get_credentials())


def _get_sheet_id() -> str:
    return os.getenv("GOOGLE_SHEET_ID", "").strip()


def _next_row_number(service, spreadsheet_id: str) -> int:
    """Return the next available row number (for the # column)."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{CONTENT_LIBRARY_TAB}!A:A"
        ).execute()
        values = result.get("values", [])
        return max(len(values), 1)  # Row 1 = header, so first data row = 1
    except Exception:
        return 1


def _extract_from_publishing(publishing_out: str) -> dict:
    """Pull caption, hashtags, platform from the publishing stage output."""
    out = publishing_out or ""
    data = {"caption": "", "hashtags": "", "platform": "Instagram"}

    # Caption
    cap = re.search(r'(?:Caption|caption)[:\s]+(.+?)(?=\n##|\n\*\*Hashtag|\n#|\Z)', out, re.DOTALL)
    if cap:
        data["caption"] = cap.group(1).strip()[:500]

    # Hashtags
    tag = re.search(r'(?:Hashtag|hashtag)[s]?[:\s]+(.+?)(?=\n##|\n\*\*|\Z)', out, re.DOTALL)
    if tag:
        data["hashtags"] = tag.group(1).strip()[:300]
    else:
        # Grab lines starting with #
        tags = re.findall(r'#\w+', out)
        if tags:
            data["hashtags"] = " ".join(tags[:25])

    # Platform
    low = out.lower()
    if "tiktok" in low:
        data["platform"] = "TikTok"
    elif "youtube" in low:
        data["platform"] = "YouTube"
    elif "linkedin" in low:
        data["platform"] = "LinkedIn"
    elif "facebook" in low:
        data["platform"] = "Facebook"

    return data


def _extract_script(copywriting_out: str) -> str:
    """Extract the voiceover script from the copywriting stage."""
    out = copywriting_out or ""
    vo = re.findall(r'(?:Voiceover|voiceover|Voice.?over|Script)[:\s]+(.+?)(?:\n\n|\n##|\n\*\*|$)',
                    out, re.DOTALL)
    if vo:
        return " | ".join(p.strip() for p in vo)[:600]
    return out[:400]


def append_to_content_library(workflow_id: int, title: str, task_type: str,
                               stage_outputs: dict, drive_links: dict,
                               client_name: str = "Dubai Prod") -> str | None:
    """Append a fully-formatted row to the 📋 Content Library tab."""
    sheet_id = _get_sheet_id()
    if not sheet_id:
        logger.warning("[google] GOOGLE_SHEET_ID not set — run scripts/setup_google.py first")
        return None

    if not is_configured():
        return None

    try:
        service = _sheets_service()

        publishing_out   = stage_outputs.get("publishing", "") or ""
        copywriting_out  = stage_outputs.get("copywriting", "") or ""
        research_out     = stage_outputs.get("research", "") or ""

        parsed    = _extract_from_publishing(publishing_out)
        script    = _extract_script(copywriting_out)
        row_num   = _next_row_number(service, sheet_id)

        type_labels = {
            "reels": "Reel", "carousel": "Carousel", "static_post": "Static Post",
            "story": "Story", "campaign": "Campaign", "content_plan": "Content Plan",
            "captions": "Captions", "hashtag_research": "Hashtag Research",
            "account_audit": "Account Audit",
        }

        # Source links from research
        sources = ""
        urls = re.findall(r'https?://[^\s\)\"\']+', research_out)
        if urls:
            sources = "\n".join(urls[:5])

        row = [
            str(row_num),                                          # #
            client_name,                                           # Client
            title,                                                 # Title / Idea
            sources,                                               # Sources
            parsed["platform"],                                    # Platform
            type_labels.get(task_type, task_type.title()),         # Type
            script,                                                # Script
            parsed["caption"],                                     # Caption
            parsed["hashtags"],                                    # Hashtags
            datetime.now().strftime("%Y-%m-%d"),                   # Date Created
            "",                                                    # Publish Date (user fills)
            "Approved ✅",                                         # Status
            drive_links.get("cover_image", ""),                    # Cover Image
            drive_links.get("video", ""),                          # Video
            drive_links.get("voiceover", ""),                      # Voiceover
            drive_links.get("final_audio", ""),                    # Final Audio
            drive_links.get("drive_folder", ""),                   # Drive Folder
            "",                                                    # Notes
        ]

        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{CONTENT_LIBRARY_TAB}!A:R",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()

        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        logger.info(f"[google] Row {row_num} added to Content Library: {title}")
        return sheet_url

    except Exception as e:
        logger.error(f"[google] Sheets append error: {e}")
        return None


# ============================================================
# CLIENT SYNC
# ============================================================

def sync_clients_to_sheet():
    """Re-sync the 👥 Clients tab and Dashboard client cards from the SQLite DB."""
    import asyncio, subprocess, sys
    from pathlib import Path
    try:
        script = Path(__file__).resolve().parent.parent / "scripts" / "setup_clients_sheet.py"
        subprocess.Popen([sys.executable, str(script)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("[google] Client sync triggered in background")
    except Exception as e:
        logger.warning(f"[google] Client sync error: {e}")


# ============================================================
# MAIN ENTRY POINT (called by workflow.py on completion)
# ============================================================

async def sync_completed_workflow(workflow_id: int):
    """Called automatically when a workflow completes."""
    if not is_configured():
        logger.info("[google] Not configured — skipping sync")
        return

    try:
        import asyncio
        from app.database import get_db

        db = await get_db()
        wf_rows = await db.execute_fetchall("SELECT * FROM workflows WHERE id=?", (workflow_id,))
        stage_rows = await db.execute_fetchall(
            "SELECT stage_name, output_data FROM workflow_stages WHERE workflow_id=? AND status='completed'",
            (workflow_id,)
        )
        await db.close()

        if not wf_rows:
            return

        wf = dict(wf_rows[0])
        stage_outputs = {dict(s)["stage_name"]: dict(s)["output_data"] or "" for s in stage_rows}

        title     = wf["title"]
        task_type = wf.get("task_type", "static_post")

        logger.info(f"[google] Syncing workflow {workflow_id}: {title}")

        # Upload assets to Drive
        drive_links = await asyncio.to_thread(
            upload_assets_to_drive, workflow_id, title, stage_outputs
        )

        # Append to Content Library sheet
        sheet_url = await asyncio.to_thread(
            append_to_content_library,
            workflow_id, title, task_type, stage_outputs, drive_links
        )

        # Save drive links back to the workflow record
        if drive_links:
            db = await get_db()
            await db.execute(
                "UPDATE workflows SET delivery=? WHERE id=?",
                (json.dumps(drive_links), workflow_id)
            )
            await db.commit()
            await db.close()

        if sheet_url:
            logger.info(f"[google] Sync complete — {sheet_url}")

    except Exception as e:
        logger.error(f"[google] sync_completed_workflow error: {e}")
