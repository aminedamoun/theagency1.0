"""One-time Google OAuth setup + Professional Content Calendar creation.

Run this script ONCE to connect your Google account:
    python scripts/setup_google.py

Before running:
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable Google Drive API + Google Sheets API
  3. Create OAuth 2.0 credentials (Desktop app)
  4. Download JSON → save as config/google_credentials.json
"""

import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "config" / "google_credentials.json"
TOKEN_FILE       = Path(__file__).resolve().parent.parent / "config" / "google_token.json"
ENV_FILE         = Path(__file__).resolve().parent.parent / ".env"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# ─── Color palette ──────────────────────────────────────────────────────────

def rgb(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}

BLACK      = rgb(15,  15,  15)
WHITE      = rgb(255, 255, 255)
GOLD       = rgb(212, 175,  55)
DARK_GREY  = rgb(30,  30,  30)
MID_GREY   = rgb(50,  50,  50)
LIGHT_GREY = rgb(245, 245, 245)
ALT_ROW    = rgb(250, 250, 250)

# Status badge colors
STATUS_COLORS = {
    "Draft ✏️":        rgb(255, 244, 204),  # yellow-ish
    "In Production 🎬": rgb(230, 216, 255),  # purple
    "In Review 👀":     rgb(255, 229, 204),  # orange
    "Approved ✅":      rgb(204, 255, 229),  # green
    "Scheduled 📅":     rgb(204, 229, 255),  # blue
    "Published 🚀":     rgb(188, 240, 204),  # bright green
    "Rejected ❌":      rgb(255, 204, 204),  # red
}

# Platform colors
PLATFORM_COLORS = {
    "Instagram":  rgb(253, 204, 224),
    "TikTok":     rgb(204, 248, 252),
    "YouTube":    rgb(255, 210, 210),
    "LinkedIn":   rgb(204, 225, 255),
    "Facebook":   rgb(210, 228, 255),
}


def save_sheet_id(sheet_id: str):
    content = ENV_FILE.read_text() if ENV_FILE.exists() else ""
    if "GOOGLE_SHEET_ID=" in content:
        content = re.sub(r'GOOGLE_SHEET_ID=.*', f'GOOGLE_SHEET_ID={sheet_id}', content)
    else:
        content = content.rstrip("\n") + f"\nGOOGLE_SHEET_ID={sheet_id}\n"
    ENV_FILE.write_text(content)


def build_format_request(sheet_id, start_row, end_row, start_col, end_col, fmt, fields):
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row, "endRowIndex": end_row,
                "startColumnIndex": start_col, "endColumnIndex": end_col,
            },
            "cell": {"userEnteredFormat": fmt},
            "fields": fields,
        }
    }


def col_width_request(sheet_id, col_index, pixel_width):
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": col_index,
                "endIndex": col_index + 1,
            },
            "properties": {"pixelSize": pixel_width},
            "fields": "pixelSize",
        }
    }


def row_height_request(sheet_id, start_row, end_row, pixel_height):
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": start_row,
                "endIndex": end_row,
            },
            "properties": {"pixelSize": pixel_height},
            "fields": "pixelSize",
        }
    }


def freeze_request(sheet_id, rows=1, cols=0):
    return {
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": rows,
                    "frozenColumnCount": cols,
                }
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    }


def dropdown_validation(sheet_id, start_row, end_row, col, values):
    return {
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row, "endRowIndex": end_row,
                "startColumnIndex": col, "endColumnIndex": col + 1,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in values],
                },
                "showCustomUi": True,
                "strict": False,
            }
        }
    }


def conditional_color(sheet_id, col, text, bg_color):
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                }],
                "booleanRule": {
                    "condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": text}]},
                    "format": {"backgroundColor": bg_color},
                }
            },
            "index": 0,
        }
    }


def banding_request(sheet_id, header_color, first_color, second_color):
    return {
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": sheet_id,
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "startColumnIndex": 0,
                },
                "rowProperties": {
                    "headerColor": header_color,
                    "firstBandColor": first_color,
                    "secondBandColor": second_color,
                }
            }
        }
    }


def setup_content_library(service, spreadsheet_id: str, sheet_id: int):
    """Configure the Content Library tab with professional formatting."""

    # ── Column definitions ──────────────────────────────────────────────────
    # (header, width_px, wrap)
    columns = [
        ("#",              45,   False),
        ("Client",        130,   False),
        ("Title / Idea",  260,   True),
        ("Sources",       180,   True),
        ("Platform",      110,   False),
        ("Type",          120,   False),
        ("Script",        320,   True),
        ("Caption",       320,   True),
        ("Hashtags",      200,   True),
        ("Date Created",  130,   False),
        ("Publish Date",  130,   False),
        ("Status",        140,   False),
        ("Cover Image",   140,   False),
        ("Video",         140,   False),
        ("Voiceover",     140,   False),
        ("Final Audio",   140,   False),
        ("Drive Folder",  140,   False),
        ("Notes",         220,   True),
    ]
    headers = [c[0] for c in columns]

    # Write header row
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="📋 Content Library!A1",
        valueInputOption="RAW",
        body={"values": [headers]},
    ).execute()

    requests = []

    # Header row — black bg, gold text, bold, center, size 11
    requests.append(build_format_request(
        sheet_id, 0, 1, 0, len(columns),
        {
            "backgroundColor": BLACK,
            "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": GOLD},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
        },
        "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
    ))

    # Header row height
    requests.append(row_height_request(sheet_id, 0, 1, 48))

    # Data rows — light text, size 10, middle-align
    requests.append(build_format_request(
        sheet_id, 1, 1000, 0, len(columns),
        {
            "textFormat": {"fontSize": 10},
            "verticalAlignment": "MIDDLE",
        },
        "userEnteredFormat(textFormat,verticalAlignment)"
    ))

    # Wrap cells that need it
    for i, (_, _, wrap) in enumerate(columns):
        if wrap:
            requests.append(build_format_request(
                sheet_id, 1, 1000, i, i + 1,
                {"wrapStrategy": "WRAP"},
                "userEnteredFormat.wrapStrategy"
            ))

    # Column widths
    for i, (_, width, _) in enumerate(columns):
        requests.append(col_width_request(sheet_id, i, width))

    # Freeze header + first 2 cols
    requests.append(freeze_request(sheet_id, rows=1, cols=2))

    # Status dropdown (col 11)
    requests.append(dropdown_validation(sheet_id, 1, 1000, 11, list(STATUS_COLORS.keys())))

    # Platform dropdown (col 4)
    requests.append(dropdown_validation(sheet_id, 1, 1000, 4, list(PLATFORM_COLORS.keys())))

    # Conditional formatting — Status column (col 11)
    for status_text, bg in STATUS_COLORS.items():
        requests.append(conditional_color(sheet_id, 11, status_text.split()[0], bg))

    # Conditional formatting — Platform column (col 4)
    for platform, bg in PLATFORM_COLORS.items():
        requests.append(conditional_color(sheet_id, 4, platform, bg))

    # Alternating row banding (light grey / white)
    requests.append(banding_request(sheet_id, BLACK, WHITE, LIGHT_GREY))

    # Border on header
    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0, "endRowIndex": 1,
                "startColumnIndex": 0, "endColumnIndex": len(columns),
            },
            "bottom": {"style": "SOLID_MEDIUM", "color": GOLD},
        }
    })

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()


def setup_calendar_tab(service, spreadsheet_id: str, sheet_id: int):
    """Configure the 📅 Calendar tab — a monthly calendar view."""

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    days   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Week header
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="📅 Calendar!A1",
        valueInputOption="RAW",
        body={"values": [days]},
    ).execute()

    requests = [
        build_format_request(
            sheet_id, 0, 1, 0, 7,
            {
                "backgroundColor": BLACK,
                "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": GOLD},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
            },
            "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        ),
        row_height_request(sheet_id, 0, 1, 44),
        freeze_request(sheet_id, rows=1),
    ]
    # Column widths — 7 equal columns
    for i in range(7):
        requests.append(col_width_request(sheet_id, i, 160))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()


def setup_ideas_bank(service, spreadsheet_id: str, sheet_id: int):
    """Configure the 💡 Ideas Bank tab."""
    headers = ["Date", "Source / Inspiration", "Idea / Concept", "Platform", "Priority", "Assigned To", "Status", "Notes"]
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="💡 Ideas Bank!A1",
        valueInputOption="RAW",
        body={"values": [headers]},
    ).execute()

    col_widths = [130, 220, 320, 110, 100, 130, 130, 220]
    requests = [
        build_format_request(
            sheet_id, 0, 1, 0, len(headers),
            {
                "backgroundColor": BLACK,
                "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": GOLD},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
            },
            "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        ),
        row_height_request(sheet_id, 0, 1, 44),
        freeze_request(sheet_id, rows=1),
        dropdown_validation(sheet_id, 1, 1000, 4, ["🔥 High", "⚡ Medium", "💤 Low"]),
        dropdown_validation(sheet_id, 1, 1000, 6, ["💡 Idea", "✏️ In Progress", "✅ Done", "❌ Dropped"]),
    ]
    for i, w in enumerate(col_widths):
        requests.append(col_width_request(sheet_id, i, w))
    requests.append(banding_request(sheet_id, BLACK, WHITE, LIGHT_GREY))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()


def setup_dashboard(service, spreadsheet_id: str, sheet_id: int, client_name: str = "Dubai Prod"):
    """Configure the 🏠 Dashboard tab."""

    now = datetime.now().strftime("%B %Y")
    values = [
        [""],
        ["", f"  {client_name}  —  Content Studio", "", "", ""],
        ["", f"  Dubai Prod Agency                                     Updated: {now}"],
        [""],
        ["", "📋 Content Library", "", "📅 Calendar", "", "💡 Ideas Bank"],
        ["", "All content pieces, scripts,", "", "Monthly posting", "", "Save ideas and"],
        ["", "captions & assets in one place.", "", "schedule & planner.", "", "inspiration sources."],
        [""],
        ["", "STATUS GUIDE"],
        ["", "Draft ✏️",        "", "Content is being written"],
        ["", "In Production 🎬","", "Video/audio being created"],
        ["", "In Review 👀",    "", "Waiting for approval"],
        ["", "Approved ✅",     "", "Ready to schedule"],
        ["", "Scheduled 📅",   "", "Posting date confirmed"],
        ["", "Published 🚀",   "", "Live on platform"],
        ["", "Rejected ❌",    "", "Needs rework"],
    ]
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="🏠 Dashboard!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    requests = [
        # Entire sheet background — dark
        build_format_request(
            sheet_id, 0, 100, 0, 20,
            {"backgroundColor": DARK_GREY},
            "userEnteredFormat.backgroundColor"
        ),
        # Title row
        build_format_request(
            sheet_id, 1, 2, 1, 6,
            {
                "backgroundColor": BLACK,
                "textFormat": {"bold": True, "fontSize": 22, "foregroundColor": GOLD},
                "verticalAlignment": "MIDDLE",
            },
            "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"
        ),
        row_height_request(sheet_id, 1, 2, 70),
        # Subtitle
        build_format_request(
            sheet_id, 2, 3, 1, 6,
            {
                "backgroundColor": MID_GREY,
                "textFormat": {"fontSize": 10, "italic": True, "foregroundColor": rgb(180,180,180)},
                "verticalAlignment": "MIDDLE",
            },
            "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"
        ),
        row_height_request(sheet_id, 2, 3, 36),
        # Section headers row (tabs guide)
        build_format_request(
            sheet_id, 4, 5, 1, 6,
            {"textFormat": {"bold": True, "fontSize": 13, "foregroundColor": GOLD}},
            "userEnteredFormat.textFormat"
        ),
        row_height_request(sheet_id, 4, 5, 36),
        # Status guide header
        build_format_request(
            sheet_id, 8, 9, 1, 4,
            {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": GOLD}},
            "userEnteredFormat.textFormat"
        ),
        col_width_request(sheet_id, 0, 40),
        col_width_request(sheet_id, 1, 200),
        col_width_request(sheet_id, 2, 40),
        col_width_request(sheet_id, 3, 280),
        freeze_request(sheet_id, rows=0, cols=0),
    ]
    # Status badge colors in dashboard
    status_list = [
        ("Draft ✏️",        rgb(255,244,204)),
        ("In Production 🎬", rgb(230,216,255)),
        ("In Review 👀",    rgb(255,229,204)),
        ("Approved ✅",     rgb(204,255,229)),
        ("Scheduled 📅",   rgb(204,229,255)),
        ("Published 🚀",   rgb(188,240,204)),
        ("Rejected ❌",    rgb(255,204,204)),
    ]
    for i, (label, color) in enumerate(status_list):
        row = 9 + i
        requests.append(build_format_request(
            sheet_id, row, row + 1, 1, 2,
            {"backgroundColor": color, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": BLACK}},
            "userEnteredFormat(backgroundColor,textFormat)"
        ))
        requests.append(row_height_request(sheet_id, row, row + 1, 32))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()


def main():
    print("\n🔗 Dubai Prod — Google Sheets Professional Setup\n")

    if not CREDENTIALS_FILE.exists():
        print("❌ config/google_credentials.json not found!")
        print("Download it from Google Cloud Console (OAuth 2.0 Desktop credentials)")
        sys.exit(1)

    print(f"✅ Credentials found")
    print("🌐 Opening browser for Google sign-in...\n")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        # Auth
        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
            TOKEN_FILE.parent.mkdir(exist_ok=True)
            TOKEN_FILE.write_text(creds.to_json())

        drive_svc  = build("drive",  "v3", credentials=creds)
        sheets_svc = build("sheets", "v4", credentials=creds)

        about = drive_svc.about().get(fields="user").execute()
        print(f"✅ Signed in as: {about['user']['emailAddress']}\n")

        print("📊 Creating professional Content Calendar spreadsheet...")

        # Create spreadsheet with 4 tabs
        spreadsheet = sheets_svc.spreadsheets().create(body={
            "properties": {"title": "Dubai Prod — Content Studio"},
            "sheets": [
                {"properties": {"title": "🏠 Dashboard",       "index": 0, "tabColor": BLACK}},
                {"properties": {"title": "📋 Content Library", "index": 1, "tabColor": GOLD}},
                {"properties": {"title": "📅 Calendar",        "index": 2, "tabColor": rgb(66,133,244)}},
                {"properties": {"title": "💡 Ideas Bank",      "index": 3, "tabColor": rgb(52,168,83)}},
            ],
        }).execute()

        spreadsheet_id = spreadsheet["spreadsheetId"]
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

        # Get tab IDs
        tab_ids = {s["properties"]["title"]: s["properties"]["sheetId"]
                   for s in spreadsheet["sheets"]}

        print("  🎨 Formatting Dashboard...")
        setup_dashboard(sheets_svc, spreadsheet_id, tab_ids["🏠 Dashboard"])

        print("  📋 Formatting Content Library...")
        setup_content_library(sheets_svc, spreadsheet_id, tab_ids["📋 Content Library"])

        print("  📅 Formatting Calendar...")
        setup_calendar_tab(sheets_svc, spreadsheet_id, tab_ids["📅 Calendar"])

        print("  💡 Formatting Ideas Bank...")
        setup_ideas_bank(sheets_svc, spreadsheet_id, tab_ids["💡 Ideas Bank"])

        # Make sheet shareable (view) by default — optional
        drive_svc.permissions().create(
            fileId=spreadsheet_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        # Save sheet ID to .env
        save_sheet_id(spreadsheet_id)

        print(f"\n✅ Spreadsheet created and saved to .env\n")
        print(f"📊 Open your Content Studio:\n   {sheet_url}\n")
        print("From now on, every completed workflow will:")
        print("  • Upload all assets to Google Drive")
        print("  • Automatically add a row to 📋 Content Library")
        print("  • Status, captions, scripts, links — all filled in\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
