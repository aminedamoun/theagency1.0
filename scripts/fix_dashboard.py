"""Fix Dashboard tab — white background, dark readable text."""

import sys, os, re
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOKEN_FILE       = Path(__file__).resolve().parent.parent / "config" / "google_token.json"
CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "config" / "google_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]

def rgb(r, g, b):
    return {"red": r/255, "green": g/255, "blue": b/255}

WHITE      = rgb(255, 255, 255)
BLACK      = rgb(15,  15,  15)
GOLD       = rgb(212, 175, 55)
LIGHT_BG   = rgb(248, 248, 248)
DARK_TEXT  = rgb(20,  20,  20)
GREY_TEXT  = rgb(100, 100, 100)
LIGHT_GREY = rgb(235, 235, 235)

def fmt_req(sheet_id, r0, r1, c0, c1, fmt, fields):
    return {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "cell": {"userEnteredFormat": fmt},
        "fields": fields,
    }}

def row_h(sheet_id, r0, r1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}

def col_w(sheet_id, ci, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": ci, "endIndex": ci+1},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}

def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID not in .env"); sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("sheets", "v4", credentials=creds)

    # Get tab IDs
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    dash_id = tabs.get("🏠 Dashboard")
    if dash_id is None:
        print("❌ Dashboard tab not found"); sys.exit(1)

    print("Clearing and rewriting Dashboard...")

    # Clear old content
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range="🏠 Dashboard!A1:Z50"
    ).execute()

    # Write content
    values = [
        [""],                                                                    # row 1 spacer
        ["", "Dubai Prod  —  Content Studio"],                                  # row 2 title
        ["", "Dubai Prod Agency", "", "", "Updated: March 2026"],               # row 3 subtitle
        [""],                                                                    # row 4 spacer
        ["", "📋 Content Library", "", "📅 Calendar", "", "💡 Ideas Bank"],     # row 5 nav
        ["", "All content pieces, scripts,", "", "Monthly posting", "", "Save ideas &"],
        ["", "captions & assets in one place.", "", "schedule & planner.", "", "inspiration sources."],
        [""],                                                                    # spacer
        ["", "STATUS GUIDE"],                                                   # row 9
        ["", "Draft ✏️",           "", "Content is being written"],
        ["", "In Production 🎬",   "", "Video/audio being created"],
        ["", "In Review 👀",       "", "Waiting for approval"],
        ["", "Approved ✅",        "", "Ready to schedule"],
        ["", "Scheduled 📅",       "", "Posting date confirmed"],
        ["", "Published 🚀",       "", "Live on platform"],
        ["", "Rejected ❌",        "", "Needs rework"],
    ]

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="🏠 Dashboard!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    reqs = []

    # ── Entire sheet: white background, dark text ──────────────────────────
    reqs.append(fmt_req(dash_id, 0, 50, 0, 20,
        {"backgroundColor": WHITE, "textFormat": {"fontSize": 10, "foregroundColor": DARK_TEXT}},
        "userEnteredFormat(backgroundColor,textFormat)"))

    # ── Title row (row 2 = index 1): black bg, gold text ──────────────────
    reqs.append(fmt_req(dash_id, 1, 2, 1, 6,
        {"backgroundColor": BLACK,
         "textFormat": {"bold": True, "fontSize": 24, "foregroundColor": GOLD},
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "LEFT"},
        "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,horizontalAlignment)"))
    reqs.append(row_h(dash_id, 1, 2, 75))

    # ── Subtitle row (row 3 = index 2) ────────────────────────────────────
    reqs.append(fmt_req(dash_id, 2, 3, 1, 6,
        {"backgroundColor": LIGHT_GREY,
         "textFormat": {"fontSize": 10, "italic": True, "foregroundColor": GREY_TEXT},
         "verticalAlignment": "MIDDLE"},
        "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"))
    reqs.append(row_h(dash_id, 2, 3, 34))

    # ── Nav section headers (row 5 = index 4) ─────────────────────────────
    reqs.append(fmt_req(dash_id, 4, 5, 1, 6,
        {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": BLACK}},
        "userEnteredFormat.textFormat"))
    reqs.append(row_h(dash_id, 4, 5, 38))

    # ── Nav descriptions (rows 6-7 = index 5-6) ───────────────────────────
    reqs.append(fmt_req(dash_id, 5, 7, 1, 6,
        {"textFormat": {"fontSize": 10, "foregroundColor": GREY_TEXT}},
        "userEnteredFormat.textFormat"))

    # ── STATUS GUIDE header (row 9 = index 8) ─────────────────────────────
    reqs.append(fmt_req(dash_id, 8, 9, 1, 2,
        {"textFormat": {"bold": True, "fontSize": 13, "foregroundColor": BLACK}},
        "userEnteredFormat.textFormat"))
    reqs.append(row_h(dash_id, 8, 9, 38))

    # ── Status badge rows (rows 10-16 = index 9-15) ───────────────────────
    badge_colors = [
        rgb(255, 244, 150),   # Draft - yellow
        rgb(210, 180, 255),   # In Production - purple
        rgb(255, 210, 150),   # In Review - orange
        rgb(150, 255, 190),   # Approved - green
        rgb(150, 210, 255),   # Scheduled - blue
        rgb(100, 230, 140),   # Published - bright green
        rgb(255, 160, 160),   # Rejected - red
    ]
    for i, bg in enumerate(badge_colors):
        row_idx = 9 + i
        reqs.append(fmt_req(dash_id, row_idx, row_idx+1, 1, 2,
            {"backgroundColor": bg,
             "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": DARK_TEXT},
             "horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"))
        reqs.append(fmt_req(dash_id, row_idx, row_idx+1, 3, 5,
            {"textFormat": {"fontSize": 10, "foregroundColor": GREY_TEXT}, "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(textFormat,verticalAlignment)"))
        reqs.append(row_h(dash_id, row_idx, row_idx+1, 34))

    # ── Column widths ──────────────────────────────────────────────────────
    reqs += [
        col_w(dash_id, 0, 40),
        col_w(dash_id, 1, 210),
        col_w(dash_id, 2, 40),
        col_w(dash_id, 3, 300),
        col_w(dash_id, 4, 40),
        col_w(dash_id, 5, 220),
    ]

    # ── Gold separator line under title ───────────────────────────────────
    reqs.append({"updateBorders": {
        "range": {"sheetId": dash_id, "startRowIndex": 1, "endRowIndex": 2,
                  "startColumnIndex": 1, "endColumnIndex": 6},
        "bottom": {"style": "SOLID_MEDIUM", "color": GOLD},
    }})

    # ── Merge title cell ──────────────────────────────────────────────────
    reqs.append({"mergeCells": {
        "range": {"sheetId": dash_id, "startRowIndex": 1, "endRowIndex": 2,
                  "startColumnIndex": 1, "endColumnIndex": 6},
        "mergeType": "MERGE_ALL",
    }})

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": reqs}
    ).execute()

    print(f"✅ Dashboard fixed!")
    print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}")

if __name__ == "__main__":
    main()
