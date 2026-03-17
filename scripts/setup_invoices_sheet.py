"""Add 🧾 Invoices tab + invoice columns to Clients tab + update Dashboard."""

import sys, os, asyncio
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOKEN_FILE = Path(__file__).resolve().parent.parent / "config" / "google_token.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]


def rgb(r, g, b):
    return {"red": r/255, "green": g/255, "blue": b/255}

WHITE       = rgb(255,255,255)
BLACK       = rgb(15, 15, 15)
GOLD        = rgb(212,175,55)
LIGHT_BG    = rgb(248,248,248)
DARK_TEXT   = rgb(20, 20, 20)
GREY_TEXT   = rgb(110,110,110)
LIGHT_GREY  = rgb(235,235,235)
GREEN       = rgb(52, 168, 83)
GREEN_LIGHT = rgb(210,245,220)
RED_LIGHT   = rgb(255,210,210)
ORANGE_LIGHT= rgb(255,235,180)
BLUE_LIGHT  = rgb(210,230,255)
GREY_LIGHT  = rgb(240,240,240)
GOLD_LIGHT  = rgb(255,248,210)

INVOICE_STATUS_COLORS = {
    "Pending ⏳":  ORANGE_LIGHT,
    "Sent 📤":     BLUE_LIGHT,
    "Paid ✅":     GREEN_LIGHT,
    "Overdue 🔴":  RED_LIGHT,
    "Cancelled ❌": GREY_LIGHT,
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

def cond_color(sid, col, text, bg):
    return {"addConditionalFormatRule": {"rule": {
        "ranges": [{"sheetId": sid, "startRowIndex": 1,
                    "startColumnIndex": col, "endColumnIndex": col+1}],
        "booleanRule": {
            "condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": text}]},
            "format": {"backgroundColor": bg},
        }
    }, "index": 0}}


def setup_invoices_tab(service, spreadsheet_id, sheet_id, clients):
    """Build the 🧾 Invoices tab."""

    headers = [
        "Invoice #", "Client", "Date Issued", "Due Date",
        "Amount (AED)", "Status", "Sent Date", "Paid Date",
        "Invoice PDF", "Notes"
    ]
    col_widths = [110, 170, 130, 130, 140, 140, 130, 130, 160, 220]

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="🧾 Invoices!A1",
        valueInputOption="RAW",
        body={"values": [headers]},
    ).execute()

    # Pre-fill one pending invoice per client
    rows = []
    today = datetime.now()
    for i, c in enumerate(clients, 1):
        due = today + timedelta(days=15)
        inv_num = f"INV-{today.strftime('%Y%m')}-{i:03d}"
        fee = c.get("monthly_fee") or 0
        rows.append([
            inv_num,
            c.get("name",""),
            today.strftime("%Y-%m-%d"),
            due.strftime("%Y-%m-%d"),
            str(fee) if fee else "",
            "Pending ⏳",
            "",  # sent date
            "",  # paid date
            "",  # PDF link
            "",  # notes
        ])

    if rows:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="🧾 Invoices!A2",
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()

    reqs = []

    # Full white bg
    reqs.append(fmt(sheet_id, 0, 500, 0, 11,
        {"backgroundColor": WHITE, "textFormat": {"fontSize": 10, "foregroundColor": DARK_TEXT}},
        "userEnteredFormat(backgroundColor,textFormat)"))

    # Header — black + gold
    reqs.append(fmt(sheet_id, 0, 1, 0, len(headers),
        {"backgroundColor": BLACK,
         "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": GOLD},
         "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"},
        "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"))
    reqs.append(row_h(sheet_id, 0, 1, 46))
    reqs.append({"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                  "startColumnIndex": 0, "endColumnIndex": len(headers)},
        "bottom": {"style": "SOLID_MEDIUM", "color": GOLD},
    }})

    # Alternating rows
    for i in range(200):
        bg = WHITE if i % 2 == 0 else LIGHT_BG
        reqs.append(fmt(sheet_id, i+1, i+2, 0, len(headers),
            {"backgroundColor": bg, "verticalAlignment": "MIDDLE"},
            "userEnteredFormat(backgroundColor,verticalAlignment)"))
        reqs.append(row_h(sheet_id, i+1, i+2, 38))

    # Invoice # — bold
    reqs.append(fmt(sheet_id, 1, 500, 0, 1,
        {"textFormat": {"bold": True, "fontSize": 10, "foregroundColor": BLACK}},
        "userEnteredFormat.textFormat"))

    # Amount — bold center
    reqs.append(fmt(sheet_id, 1, 500, 4, 5,
        {"textFormat": {"bold": True, "fontSize": 11},
         "horizontalAlignment": "CENTER"},
        "userEnteredFormat(textFormat,horizontalAlignment)"))

    # Status — center
    reqs.append(fmt(sheet_id, 1, 500, 5, 6,
        {"horizontalAlignment": "CENTER", "textFormat": {"bold": True, "fontSize": 10}},
        "userEnteredFormat(horizontalAlignment,textFormat)"))

    # Status conditional colors
    for status_text, bg in INVOICE_STATUS_COLORS.items():
        reqs.append(cond_color(sheet_id, 5, status_text.split()[0], bg))

    # Status dropdown
    reqs.append(dropdown(sheet_id, 1, 500, 5, list(INVOICE_STATUS_COLORS.keys())))

    # Client dropdown
    client_names = [c.get("name","") for c in clients]
    if client_names:
        reqs.append(dropdown(sheet_id, 1, 500, 1, client_names))

    # Column widths
    for i, w in enumerate(col_widths):
        reqs.append(col_w(sheet_id, i, w))

    reqs.append(freeze(sheet_id, rows=1, cols=1))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": reqs}
    ).execute()
    print("  ✅ Invoices tab formatted")


async def create_client_calendar_sheet(drive_svc, sheets_svc, client):
    """Create a private Google Sheet for one client with their content calendar."""

    def rgb2(r,g,b): return {"red":r/255,"green":g/255,"blue":b/255}

    name    = client.get("name", "Client")
    email   = client.get("email","")
    cid     = client.get("id")

    spreadsheet = sheets_svc.spreadsheets().create(body={
        "properties": {"title": f"{name} — Content Calendar | Dubai Prod"},
        "sheets": [
            {"properties": {"title": "📅 My Content Calendar", "index": 0}},
            {"properties": {"title": "📋 Content Status",      "index": 1}},
            {"properties": {"title": "💬 Feedback",            "index": 2}},
        ],
    }).execute()

    sid = spreadsheet["spreadsheetId"]
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sid}"

    # Get tab IDs
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"]
            for s in spreadsheet["sheets"]}
    cal_id    = tabs["📅 My Content Calendar"]
    status_id = tabs["📋 Content Status"]
    fb_id     = tabs["💬 Feedback"]

    # ── Calendar tab headers ──────────────────────────────────────────────
    cal_headers = [
        "Week", "Publish Date", "Platform", "Content Type",
        "Title / Idea", "Caption", "Hashtags", "Status", "Link / Asset", "Notes"
    ]
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sid, range="📅 My Content Calendar!A1",
        valueInputOption="RAW", body={"values": [cal_headers]},
    ).execute()

    # ── Status tab headers ────────────────────────────────────────────────
    status_headers = [
        "#", "Content Title", "Platform", "Type", "Status",
        "Publish Date", "Caption Preview", "Video", "Asset Link", "Feedback"
    ]
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sid, range="📋 Content Status!A1",
        valueInputOption="RAW", body={"values": [status_headers]},
    ).execute()

    # ── Feedback tab ──────────────────────────────────────────────────────
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sid, range="💬 Feedback!A1",
        valueInputOption="RAW",
        body={"values": [
            ["", f"  💬 Feedback & Revision Requests — {name}"],
            [""],
            ["Date", "Content Title", "Your Feedback / Change Request", "Status", "Resolved Date"],
        ]},
    ).execute()

    # ── Formatting ────────────────────────────────────────────────────────
    BLACK2 = rgb2(15,15,15); GOLD2 = rgb2(212,175,55)
    WHITE2 = rgb2(255,255,255); LG = rgb2(248,248,248)

    def hdr(tab_id, n_cols):
        return [
            {"repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1,
                          "startColumnIndex": 0, "endColumnIndex": n_cols},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": BLACK2,
                    "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": GOLD2},
                    "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)",
            }},
            {"updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 44}, "fields": "pixelSize",
            }},
            {"updateBorders": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1,
                          "startColumnIndex": 0, "endColumnIndex": n_cols},
                "bottom": {"style": "SOLID_MEDIUM", "color": GOLD2},
            }},
            {"updateSheetProperties": {
                "properties": {"sheetId": tab_id,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }},
        ]

    reqs = hdr(cal_id, len(cal_headers)) + hdr(status_id, len(status_headers))

    # Intro banner on calendar tab
    reqs.append({"repeatCell": {
        "range": {"sheetId": cal_id, "startRowIndex": 0, "endRowIndex": 1,
                  "startColumnIndex": 0, "endColumnIndex": len(cal_headers)},
        "cell": {"userEnteredFormat": {
            "backgroundColor": BLACK2,
            "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": GOLD2},
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat)",
    }})

    # Feedback title row
    reqs.append({"repeatCell": {
        "range": {"sheetId": fb_id, "startRowIndex": 1, "endRowIndex": 2,
                  "startColumnIndex": 0, "endColumnIndex": 5},
        "cell": {"userEnteredFormat": {
            "backgroundColor": BLACK2,
            "textFormat": {"bold": True, "fontSize": 16, "foregroundColor": GOLD2},
            "verticalAlignment": "MIDDLE",
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)",
    }})
    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": fb_id, "dimension": "ROWS", "startIndex": 1, "endIndex": 2},
        "properties": {"pixelSize": 60}, "fields": "pixelSize",
    }})
    reqs += hdr(fb_id, 5)

    # Status dropdown on calendar (col 7)
    status_vals = ["Draft ✏️", "In Production 🎬", "In Review 👀",
                   "Approved ✅", "Scheduled 📅", "Published 🚀"]
    reqs.append({"setDataValidation": {
        "range": {"sheetId": cal_id, "startRowIndex": 1, "endRowIndex": 500,
                  "startColumnIndex": 7, "endColumnIndex": 8},
        "rule": {
            "condition": {"type": "ONE_OF_LIST",
                          "values": [{"userEnteredValue": v} for v in status_vals]},
            "showCustomUi": True, "strict": False,
        }
    }})

    # Cal col widths
    for i, w in enumerate([60,130,120,130,240,280,200,130,160,180]):
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": cal_id, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i+1},
            "properties": {"pixelSize": w}, "fields": "pixelSize",
        }})

    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=sid, body={"requests": reqs}
    ).execute()

    # ── Share with client email ───────────────────────────────────────────
    if email:
        try:
            drive_svc.permissions().create(
                fileId=sid,
                body={"type": "user", "role": "writer", "emailAddress": email},
                sendNotificationEmail=True,
                emailMessage=f"Hi {name},\n\nYour Dubai Prod Content Calendar is ready! You can view your content schedule, check status updates, and leave feedback directly in this sheet.\n\nBest,\nDubai Prod Team",
            ).execute()
            print(f"  📧 Shared with {email}")
        except Exception as e:
            print(f"  ⚠️  Could not share with {email}: {e}")

    return sid, sheet_url


async def get_clients_from_db():
    from app.database import get_db
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, name, company, email, phone, platform, status, monthly_fee FROM clients ORDER BY id"
    )
    await db.close()
    return [dict(r) for r in rows]


async def save_client_sheet_url(client_id, sheet_id_val, sheet_url):
    """Save the client's personal sheet URL back to the DB."""
    from app.database import get_db
    db = await get_db()
    # Check if notes column exists and store the sheet URL there
    try:
        await db.execute(
            "UPDATE clients SET notes=? WHERE id=?",
            (f"calendar_sheet:{sheet_url}", client_id)
        )
        await db.commit()
    except Exception:
        pass
    await db.close()


async def main_async():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID not in .env"); sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    drive_svc  = build("drive",  "v3", credentials=creds)
    sheets_svc = build("sheets", "v4", credentials=creds)

    clients = await get_clients_from_db()
    print(f"✅ {len(clients)} client(s) found")

    # Get existing tabs
    meta = service = sheets_svc
    meta_resp = sheets_svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"]
            for s in meta_resp["sheets"]}

    # ── Create 🧾 Invoices tab ─────────────────────────────────────────────
    if "🧾 Invoices" not in tabs:
        res = sheets_svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
            "addSheet": {"properties": {
                "title": "🧾 Invoices",
                "index": 2,
                "tabColor": rgb(255,175,55),
            }}
        }]}).execute()
        inv_sheet_id = res["replies"][0]["addSheet"]["properties"]["sheetId"]
        print("✅ Created 🧾 Invoices tab")
    else:
        inv_sheet_id = tabs["🧾 Invoices"]
        print("✅ Using existing 🧾 Invoices tab")

    print("🧾 Setting up Invoices tab...")
    setup_invoices_tab(sheets_svc, sheet_id, inv_sheet_id, clients)

    # ── Create per-client calendar sheets ─────────────────────────────────
    print("\n📅 Creating per-client calendar sheets...")
    client_sheet_urls = {}
    for c in clients:
        name = c.get("name","Client")
        print(f"  Creating sheet for {name}...")
        cal_sid, cal_url = await create_client_calendar_sheet(drive_svc, sheets_svc, c)
        client_sheet_urls[c["id"]] = cal_url
        await save_client_sheet_url(c["id"], cal_sid, cal_url)
        print(f"  ✅ {name}: {cal_url}")

    # ── Add client sheet links to 👥 Clients tab ─────────────────────────
    if "👥 Clients" in tabs:
        print("\n🔗 Adding calendar links to Clients tab...")
        # Read existing client names to find rows
        result = sheets_svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range="👥 Clients!A:B"
        ).execute()
        existing = result.get("values", [])
        for ri, row_vals in enumerate(existing[1:], 2):  # skip header
            if len(row_vals) >= 2:
                client_name = row_vals[1]
                matched = next((c for c in clients if c.get("name","").lower() == client_name.lower()), None)
                if matched and matched["id"] in client_sheet_urls:
                    url = client_sheet_urls[matched["id"]]
                    formula = f'=HYPERLINK("{url}","📅 Open Calendar")'
                    sheets_svc.spreadsheets().values().update(
                        spreadsheetId=sheet_id,
                        range=f"👥 Clients!J{ri}",
                        valueInputOption="USER_ENTERED",
                        body={"values": [[formula]]},
                    ).execute()

        # Format the calendar link column (J = col 9)
        clients_tab_id = tabs["👥 Clients"]
        sheets_svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [
            {"repeatCell": {
                "range": {"sheetId": clients_tab_id, "startRowIndex": 1, "endRowIndex": 200,
                          "startColumnIndex": 9, "endColumnIndex": 10},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": rgb(26,115,232)},
                    "horizontalAlignment": "CENTER",
                }},
                "fields": "userEnteredFormat(textFormat,horizontalAlignment)",
            }}
        ]}).execute()
        print("  ✅ Calendar links added to Clients tab")

    print(f"\n✅ All done!")
    print(f"   Agency sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")
    for cid, url in client_sheet_urls.items():
        c = next((x for x in clients if x["id"] == cid), {})
        print(f"   {c.get('name','')}: {url}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
