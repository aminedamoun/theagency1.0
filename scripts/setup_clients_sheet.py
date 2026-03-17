"""Add 👥 Clients tab + update Dashboard with clickable client cards."""

import sys, os, asyncio
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOKEN_FILE = Path(__file__).resolve().parent.parent / "config" / "google_token.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]


def rgb(r, g, b):
    return {"red": r/255, "green": g/255, "blue": b/255}

WHITE      = rgb(255, 255, 255)
BLACK      = rgb(15,  15,  15)
GOLD       = rgb(212, 175, 55)
LIGHT_BG   = rgb(248, 248, 248)
DARK_TEXT  = rgb(20,  20,  20)
GREY_TEXT  = rgb(110, 110, 110)
LIGHT_GREY = rgb(235, 235, 235)
GREEN      = rgb(52,  168, 83)
GREEN_LIGHT = rgb(220, 245, 228)
BLUE_LIGHT  = rgb(220, 235, 255)
GOLD_LIGHT  = rgb(255, 248, 210)

STATUS_COLORS = {
    "active":   rgb(100, 220, 140),
    "inactive": rgb(200, 200, 200),
    "paused":   rgb(255, 210, 100),
}


def fmt(sid, r0, r1, c0, c1, f, fields):
    return {"repeatCell": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "cell": {"userEnteredFormat": f}, "fields": fields,
    }}

def row_h(sid, r0, r1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}

def col_w(sid, ci, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": ci, "endIndex": ci+1},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}

def freeze(sid, rows=1, cols=0):
    return {"updateSheetProperties": {
        "properties": {"sheetId": sid, "gridProperties": {
            "frozenRowCount": rows, "frozenColumnCount": cols}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
    }}

def merge(sid, r0, r1, c0, c1):
    return {"mergeCells": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "mergeType": "MERGE_ALL",
    }}

def border(sid, r0, r1, c0, c1, style="SOLID", color=None):
    b = {"style": style, "color": color or LIGHT_GREY}
    return {"updateBorders": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "top": b, "bottom": b, "left": b, "right": b,
        "innerHorizontal": b, "innerVertical": b,
    }}

def dropdown(sid, r0, r1, col, values):
    return {"setDataValidation": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": col, "endColumnIndex": col+1},
        "rule": {
            "condition": {"type": "ONE_OF_LIST",
                          "values": [{"userEnteredValue": v} for v in values]},
            "showCustomUi": True, "strict": False,
        }
    }}


def setup_clients_tab(service, spreadsheet_id, sheet_id, clients):
    """Build the 👥 Clients tab."""

    headers = [
        "#", "Client Name", "Company", "Platform", "Monthly Fee (AED)",
        "Status", "Email", "Phone", "Content Pieces", "Drive Folder", "Notes"
    ]
    col_widths = [40, 180, 180, 120, 150, 110, 220, 140, 130, 160, 220]

    # Header row
    rows = [headers]
    for i, c in enumerate(clients, 1):
        rows.append([
            str(i),
            c.get("name", ""),
            c.get("company", ""),
            c.get("platform", "Instagram"),
            str(c.get("monthly_fee", 0)) if c.get("monthly_fee") else "0",
            c.get("status", "active").capitalize(),
            c.get("email", ""),
            c.get("phone", ""),
            "0",          # content pieces — to be updated
            "",           # drive folder
            "",           # notes
        ])

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="👥 Clients!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    reqs = []

    # Full sheet white bg
    reqs.append(fmt(sheet_id, 0, 200, 0, 12,
        {"backgroundColor": WHITE, "textFormat": {"fontSize": 10, "foregroundColor": DARK_TEXT}},
        "userEnteredFormat(backgroundColor,textFormat)"))

    # Header row — black + gold
    reqs.append(fmt(sheet_id, 0, 1, 0, len(headers),
        {"backgroundColor": BLACK,
         "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": GOLD},
         "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"},
        "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"))
    reqs.append(row_h(sheet_id, 0, 1, 46))

    # Data rows alternating
    for i in range(len(clients)):
        bg = WHITE if i % 2 == 0 else LIGHT_BG
        reqs.append(fmt(sheet_id, i+1, i+2, 0, len(headers),
            {"backgroundColor": bg, "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(backgroundColor,verticalAlignment)"))
        reqs.append(row_h(sheet_id, i+1, i+2, 40))

    # Client Name column — bold
    reqs.append(fmt(sheet_id, 1, 200, 1, 2,
        {"textFormat": {"bold": True, "fontSize": 11}},
        "userEnteredFormat.textFormat"))

    # Monthly fee — center
    reqs.append(fmt(sheet_id, 1, 200, 4, 5,
        {"horizontalAlignment": "CENTER"},
        "userEnteredFormat.horizontalAlignment"))

    # Status column — center + color per status
    reqs.append(fmt(sheet_id, 1, 200, 5, 6,
        {"horizontalAlignment": "CENTER", "textFormat": {"bold": True}},
        "userEnteredFormat(horizontalAlignment,textFormat)"))

    # Status conditional formatting
    for status, bg in STATUS_COLORS.items():
        reqs.append({"addConditionalFormatRule": {"rule": {
            "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}],
            "booleanRule": {
                "condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": status.capitalize()}]},
                "format": {"backgroundColor": bg},
            }
        }, "index": 0}})

    # Status dropdown
    reqs.append(dropdown(sheet_id, 1, 200, 5, ["Active", "Inactive", "Paused"]))

    # Platform dropdown
    reqs.append(dropdown(sheet_id, 1, 200, 3,
        ["Instagram", "TikTok", "YouTube", "LinkedIn", "Facebook", "Multi-Platform"]))

    # Gold bottom border on header
    reqs.append({"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                  "startColumnIndex": 0, "endColumnIndex": len(headers)},
        "bottom": {"style": "SOLID_MEDIUM", "color": GOLD},
    }})

    # Column widths
    for i, w in enumerate(col_widths):
        reqs.append(col_w(sheet_id, i, w))

    # Freeze header
    reqs.append(freeze(sheet_id, rows=1, cols=2))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": reqs}
    ).execute()


def update_dashboard_clients(service, spreadsheet_id, dash_id, clients_sheet_id, clients):
    """Add a CLIENTS section to the Dashboard with hyperlinks to the Clients tab."""

    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id, range="🏠 Dashboard!A1:Z60"
    ).execute()

    # Build values — clients section starts at row 20
    values = [
        [""],
        ["", "Dubai Prod  —  Content Studio"],
        ["", "Dubai Prod Agency", "", "", "Updated: March 2026"],
        [""],
        ["", "📋 Content Library", "", "📅 Calendar", "", "💡 Ideas Bank"],
        ["", "All content pieces, scripts,", "", "Monthly posting", "", "Save ideas &"],
        ["", "captions & assets in one place.", "", "schedule & planner.", "", "inspiration sources."],
        [""],
        ["", "STATUS GUIDE"],
        ["", "Draft ✏️",           "", "Content is being written"],
        ["", "In Production 🎬",   "", "Video/audio being created"],
        ["", "In Review 👀",       "", "Waiting for approval"],
        ["", "Approved ✅",        "", "Ready to schedule"],
        ["", "Scheduled 📅",       "", "Posting date confirmed"],
        ["", "Published 🚀",       "", "Live on platform"],
        ["", "Rejected ❌",        "", "Needs rework"],
        [""],
        [""],
        ["", "👥 CLIENTS"],
    ]

    # Client cards row: Name | Platform | Status | Email
    client_row_start = 19  # 0-indexed = row 20 in sheet
    for c in clients:
        values.append([
            "",
            c.get("name", ""),
            c.get("company", "") or "—",
            c.get("platform", "Instagram") or "Instagram",
            c.get("status", "active").capitalize(),
            c.get("email", "") or "—",
            c.get("monthly_fee", 0) and f"AED {c['monthly_fee']:,.0f}" or "—",
        ])

    # Add client button
    values.append(["", "+ Add New Client  →  Go to 👥 Clients tab"])

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="🏠 Dashboard!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    reqs = []

    # ── Full sheet white ───────────────────────────────────────────────────
    reqs.append(fmt(dash_id, 0, 60, 0, 20,
        {"backgroundColor": WHITE, "textFormat": {"fontSize": 10, "foregroundColor": DARK_TEXT}},
        "userEnteredFormat(backgroundColor,textFormat)"))

    # ── Title row (index 1) ────────────────────────────────────────────────
    reqs.append(merge(dash_id, 1, 2, 1, 6))
    reqs.append(fmt(dash_id, 1, 2, 1, 6,
        {"backgroundColor": BLACK,
         "textFormat": {"bold": True, "fontSize": 24, "foregroundColor": GOLD},
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "LEFT"},
        "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,horizontalAlignment)"))
    reqs.append(row_h(dash_id, 1, 2, 75))
    reqs.append({"updateBorders": {
        "range": {"sheetId": dash_id, "startRowIndex": 1, "endRowIndex": 2,
                  "startColumnIndex": 1, "endColumnIndex": 6},
        "bottom": {"style": "SOLID_MEDIUM", "color": GOLD},
    }})

    # ── Subtitle (index 2) ─────────────────────────────────────────────────
    reqs.append(fmt(dash_id, 2, 3, 1, 6,
        {"backgroundColor": LIGHT_GREY,
         "textFormat": {"fontSize": 10, "italic": True, "foregroundColor": GREY_TEXT},
         "verticalAlignment": "MIDDLE"},
        "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"))
    reqs.append(row_h(dash_id, 2, 3, 34))

    # ── Nav headers (index 4) ──────────────────────────────────────────────
    reqs.append(fmt(dash_id, 4, 5, 1, 6,
        {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": BLACK}},
        "userEnteredFormat.textFormat"))
    reqs.append(row_h(dash_id, 4, 5, 38))

    # ── Nav descriptions (5-6) ────────────────────────────────────────────
    reqs.append(fmt(dash_id, 5, 7, 1, 6,
        {"textFormat": {"fontSize": 10, "foregroundColor": GREY_TEXT}},
        "userEnteredFormat.textFormat"))

    # ── STATUS GUIDE header (index 8) ────────────────────────────────────
    reqs.append(fmt(dash_id, 8, 9, 1, 2,
        {"textFormat": {"bold": True, "fontSize": 13, "foregroundColor": BLACK}},
        "userEnteredFormat.textFormat"))
    reqs.append(row_h(dash_id, 8, 9, 38))

    badge_colors = [
        rgb(255,244,150), rgb(210,180,255), rgb(255,210,150),
        rgb(150,255,190), rgb(150,210,255), rgb(100,230,140), rgb(255,160,160),
    ]
    for i, bg in enumerate(badge_colors):
        ri = 9 + i
        reqs.append(fmt(dash_id, ri, ri+1, 1, 2,
            {"backgroundColor": bg,
             "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": DARK_TEXT},
             "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"))
        reqs.append(fmt(dash_id, ri, ri+1, 3, 5,
            {"textFormat": {"fontSize": 10, "foregroundColor": GREY_TEXT}, "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(textFormat,verticalAlignment)"))
        reqs.append(row_h(dash_id, ri, ri+1, 34))

    # ── CLIENTS section header (index 18) ────────────────────────────────
    reqs.append(fmt(dash_id, 18, 19, 1, 7,
        {"backgroundColor": BLACK,
         "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": GOLD},
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "LEFT"},
        "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,horizontalAlignment)"))
    reqs.append(row_h(dash_id, 18, 19, 44))
    reqs.append({"updateBorders": {
        "range": {"sheetId": dash_id, "startRowIndex": 18, "endRowIndex": 19,
                  "startColumnIndex": 1, "endColumnIndex": 7},
        "bottom": {"style": "SOLID_MEDIUM", "color": GOLD},
    }})

    # ── Client column sub-headers ─────────────────────────────────────────
    sub_headers = ["", "NAME", "COMPANY", "PLATFORM", "STATUS", "EMAIL", "FEE"]
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"🏠 Dashboard!A{19+1}",
        valueInputOption="RAW",
        body={"values": [sub_headers]},
    ).execute()
    reqs.append(fmt(dash_id, 19, 20, 0, 7,
        {"backgroundColor": LIGHT_GREY,
         "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": GREY_TEXT},
         "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"},
        "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"))
    reqs.append(row_h(dash_id, 19, 20, 28))

    # ── Client rows ────────────────────────────────────────────────────────
    for i, c in enumerate(clients):
        ri = 20 + i   # data starts at sheet row 21 = index 20
        # Alternating card background
        bg = WHITE if i % 2 == 0 else LIGHT_BG
        reqs.append(fmt(dash_id, ri, ri+1, 0, 7,
            {"backgroundColor": bg, "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(backgroundColor,verticalAlignment)"))
        reqs.append(row_h(dash_id, ri, ri+1, 40))

        # Client name — bold, dark, clickable look
        reqs.append(fmt(dash_id, ri, ri+1, 1, 2,
            {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": BLACK,
                            "underline": True},
             "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(textFormat,verticalAlignment)"))

        # Status badge color
        s = c.get("status", "active").lower()
        sbg = STATUS_COLORS.get(s, rgb(200,200,200))
        reqs.append(fmt(dash_id, ri, ri+1, 4, 5,
            {"backgroundColor": sbg,
             "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": DARK_TEXT},
             "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"))

        # Left border accent — gold for active clients
        accent = GOLD if s == "active" else rgb(200,200,200)
        reqs.append({"updateBorders": {
            "range": {"sheetId": dash_id, "startRowIndex": ri, "endRowIndex": ri+1,
                      "startColumnIndex": 1, "endColumnIndex": 2},
            "left": {"style": "SOLID_MEDIUM", "color": accent},
        }})

        # Bottom border separator
        reqs.append({"updateBorders": {
            "range": {"sheetId": dash_id, "startRowIndex": ri, "endRowIndex": ri+1,
                      "startColumnIndex": 1, "endColumnIndex": 7},
            "bottom": {"style": "SOLID", "color": LIGHT_GREY},
        }})

    # ── "+ Add New Client" row ─────────────────────────────────────────────
    add_row = 20 + len(clients)
    reqs.append(fmt(dash_id, add_row, add_row+1, 1, 4,
        {"textFormat": {"bold": True, "fontSize": 10,
                        "foregroundColor": GOLD},
         "verticalAlignment": "MIDDLE"},
        "userEnteredFormat(textFormat,verticalAlignment)"))
    reqs.append(row_h(dash_id, add_row, add_row+1, 36))

    # ── Column widths ──────────────────────────────────────────────────────
    for ci, w in enumerate([30, 180, 170, 130, 110, 220, 140]):
        reqs.append(col_w(dash_id, ci, w))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": reqs}
    ).execute()

    # ── Now add HYPERLINKS on client names → Clients tab ──────────────────
    # Format: =HYPERLINK("#gid=SHEET_ID", "Name")
    for i, c in enumerate(clients):
        sheet_row = 21 + i   # 1-indexed sheet row
        formula = f'=HYPERLINK("#gid={clients_sheet_id}","  {c.get("name","")}")'
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"🏠 Dashboard!B{sheet_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[formula]]},
        ).execute()


async def get_clients_from_db():
    from app.database import get_db
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, name, company, email, phone, platform, status, monthly_fee FROM clients ORDER BY id"
    )
    await db.close()
    return [dict(r) for r in rows]


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

    # Fetch clients from SQLite
    clients = asyncio.run(get_clients_from_db())
    print(f"✅ Found {len(clients)} client(s) in database")

    # Get existing tabs
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    # Create 👥 Clients tab if it doesn't exist
    if "👥 Clients" not in tabs:
        res = service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
            "addSheet": {"properties": {
                "title": "👥 Clients",
                "index": 1,
                "tabColor": rgb(212, 175, 55),
            }}
        }]}).execute()
        clients_sheet_id = res["replies"][0]["addSheet"]["properties"]["sheetId"]
        tabs["👥 Clients"] = clients_sheet_id
        print("✅ Created 👥 Clients tab")
    else:
        clients_sheet_id = tabs["👥 Clients"]
        print("✅ Using existing 👥 Clients tab")

    print("📋 Setting up Clients tab...")
    setup_clients_tab(service, sheet_id, clients_sheet_id, clients)

    print("🏠 Updating Dashboard with client cards...")
    update_dashboard_clients(service, sheet_id, tabs["🏠 Dashboard"], clients_sheet_id, clients)

    print(f"\n✅ Done!")
    print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}")


if __name__ == "__main__":
    main()
