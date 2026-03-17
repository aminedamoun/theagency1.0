"""Dubai Prod Agent — AI Brain powered by Claude.

Uses Anthropic's Claude API with native tool use for maximum
intelligence, reasoning, and multi-step execution.
"""

import json
import logging
import os
import asyncio
from datetime import datetime

import anthropic
from app.database import get_db

logger = logging.getLogger("amine-agent")

SYSTEM_PROMPT = """You are Dubai Prod Agent — AI brain for Amine's social media agency.

Rules:
- For content creation (reels, posts, carousels, campaigns): use start_content_workflow. Do NOT create separate tasks with create_task — the workflow handles everything automatically.
- For prospecting/research: use run_prospecting or search_companies.
- For other work: use tools directly. Keep responses short.
- Confirm before sending emails or deleting.

Today: """ + datetime.now().strftime("%Y-%m-%d")

# Claude tool format (different from OpenAI)
TOOLS = [
    {
        "name": "list_clients",
        "description": "Get all agency clients",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_client",
        "description": "Add a new client to the agency",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Client name"},
                "company": {"type": "string", "description": "Company name"},
                "email": {"type": "string", "description": "Email address"},
                "phone": {"type": "string", "description": "Phone number"},
                "platform": {"type": "string", "description": "Social media platforms (e.g. Instagram, TikTok)"},
                "monthly_fee": {"type": "number", "description": "Monthly fee in USD"},
                "notes": {"type": "string", "description": "Additional notes"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a new task. Set status to 'in_progress' when executing immediately, 'completed' when done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task details"},
                "client_id": {"type": "integer", "description": "Client ID (optional)"},
                "assigned_agent": {
                    "type": "string",
                    "enum": ["manager", "content", "browser", "designer", "email", "analytics"],
                    "description": "Which agent to assign",
                },
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                "due_date": {"type": "string", "description": "Due date YYYY-MM-DD"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "Get all tasks with their status",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_content",
        "description": "Create a social media post/content piece. Write the FULL caption ready to post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer", "description": "Client ID"},
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "tiktok", "facebook", "twitter", "linkedin", "youtube"],
                },
                "content_type": {
                    "type": "string",
                    "enum": ["post", "story", "reel", "carousel", "video"],
                },
                "caption": {"type": "string", "description": "The full caption/copy for the post, ready to publish"},
                "status": {"type": "string", "enum": ["draft", "scheduled", "published"]},
                "scheduled_at": {"type": "string", "description": "Schedule date ISO format"},
                "notes": {"type": "string", "description": "Internal notes"},
            },
            "required": ["platform", "caption"],
        },
    },
    {
        "name": "list_content",
        "description": "Get all content pieces",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_dashboard",
        "description": "Get agency dashboard stats: client count, revenue, pending tasks, content status",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "fetch_emails",
        "description": "Fetch recent emails from the inbox",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of emails to fetch"},
                "unread_only": {"type": "boolean", "description": "Only fetch unread emails"},
            },
            "required": [],
        },
    },
    {
        "name": "browse_web",
        "description": "Use the browser agent to visit websites, search, and extract information",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "What to do in the browser (natural language)"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "update_task_status",
        "description": "Update a task's status. ALWAYS call this after doing work to mark task as completed or failed. NEVER leave tasks in_progress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"], "description": "completed=work done, failed=work failed"},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "update_client",
        "description": "Update an existing client's information",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer", "description": "Client ID"},
                "name": {"type": "string"},
                "company": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "platform": {"type": "string"},
                "monthly_fee": {"type": "number"},
                "status": {"type": "string", "enum": ["active", "paused"]},
                "notes": {"type": "string"},
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "search_client",
        "description": "Search for a client by name",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Client name to search for"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "generate_image",
        "description": "Generate an image using DALL-E AI. Returns the image URL/path. Use for social media post visuals, ads, brand content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Detailed image generation prompt. Be specific about style, composition, colors, mood."},
                "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"], "description": "Image size. 1024x1024=square (Instagram), 1792x1024=landscape (Facebook/YouTube), 1024x1792=portrait (Stories/Reels)"},
                "style": {"type": "string", "enum": ["vivid", "natural"], "description": "vivid=hyper-real/dramatic, natural=more realistic"},
                "content_id": {"type": "integer", "description": "Link to a content piece ID (optional)"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "update_content_status",
        "description": "Update a content piece's pipeline status: draft → designed → video_ready → published",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_id": {"type": "integer", "description": "Content ID"},
                "status": {"type": "string", "enum": ["draft", "designed", "video_ready", "scheduled", "published"]},
                "media_url": {"type": "string", "description": "URL/path of generated image or video"},
            },
            "required": ["content_id", "status"],
        },
    },
    {
        "name": "create_video",
        "description": "Full video production: AI generates scene images + voiceover + subtitles → cinematic Ken Burns video. Duration is driven by the voiceover script length. Short script = short video.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Visual CONCEPT for the video — what should it show? Be cinematic. Example: 'Luxury Dubai penthouse interior, yacht at sunset, Palm Jumeirah aerial view'"},
                "script": {"type": "string", "description": "Voiceover script the narrator reads. THIS CONTROLS DURATION: ~15 words = 5s, ~30 words = 10s, ~60 words = 20s, ~90 words = 30s. Write the EXACT script."},
                "num_clips": {"type": "integer", "description": "Number of different scene images to generate (2-8). More scenes = more visual variety. Default: calculate from duration (1 scene per 3-5 seconds)."},
                "clip_duration": {"type": "integer", "description": "Seconds per scene (3-8). Default: auto-calculated from total duration / num_clips."},
                "target_duration": {"type": "integer", "description": "Target video duration in seconds. If set, overrides voiceover-based duration. Use for precise control."},
                "voice": {"type": "string", "enum": ["onyx", "nova", "alloy", "echo", "fable", "shimmer"], "description": "onyx=deep male, nova=warm female, alloy=neutral, shimmer=soft female"},
                "aspect_ratio": {"type": "string", "enum": ["9:16", "16:9", "1:1"], "description": "9:16=Reels/TikTok, 16:9=YouTube, 1:1=Feed post"},
                "content_id": {"type": "integer", "description": "Link to content piece ID (optional)"},
            },
            "required": ["prompt", "script"],
        },
    },
    {
        "name": "generate_voiceover",
        "description": "Generate voiceover audio. Uses ElevenLabs (custom/cloned voices) if available, otherwise OpenAI TTS. Returns audio file path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "description": "Voice name. ElevenLabs: use your custom voice name. OpenAI: onyx, nova, alloy, echo, fable, shimmer."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "generate_report",
        "description": "Generate a professional PDF report with agency data (clients, tasks, content, activity). Returns the PDF file path. The PDF is saved to the media library.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Report title, e.g. 'Monthly Performance Report' or 'Client Strategy Report'"},
                "include_clients": {"type": "boolean", "description": "Include client portfolio section"},
                "include_tasks": {"type": "boolean", "description": "Include task overview section"},
                "include_content": {"type": "boolean", "description": "Include content pipeline section"},
                "include_activity": {"type": "boolean", "description": "Include agent activity log"},
                "custom_sections": {
                    "type": "array",
                    "description": "Custom sections to add (e.g. research findings, strategy notes)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "generate_proposal",
        "description": "Generate a branded Dubai Prod marketing PDF/proposal for a client. The PDF has Dubai Prod branding, service offerings, and is ready to email. Agent only needs to set the client name and date — everything else is pre-filled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Client's full name"},
                "client_company": {"type": "string", "description": "Client's company name"},
                "services": {"type": "array", "items": {"type": "string"}, "description": "Specific services to highlight (e.g. ['social media', 'video production']). Leave empty for all services."},
                "custom_intro": {"type": "string", "description": "Custom introductory paragraph (optional, replaces default)"},
                "custom_body": {"type": "string", "description": "Custom body text about strategy/approach (optional)"},
            },
            "required": ["client_name"],
        },
    },
    {
        "name": "generate_invoice",
        "description": "Generate a professional PDF invoice for a client. IMPORTANT: First call list_clients to find the client by name and get their ID. Then call this tool with that client_id. Automatically: generates PDF with Dubai Prod logo, uploads to Google Drive, opens WhatsApp for the client AND a copy to the owner (+971543333587). Use whenever user asks to create, send, or generate an invoice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer", "description": "Client ID from the database. Call list_clients first to find the correct ID by matching the client name."},
                "items": {
                    "type": "array",
                    "description": "List of invoice line items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string", "description": "Service description e.g. 'Monthly Social Media Management'"},
                            "qty": {"type": "integer", "description": "Quantity, usually 1"},
                            "price": {"type": "number", "description": "Unit price in AED"},
                        },
                        "required": ["description", "price"],
                    },
                },
                "send_email": {"type": "boolean", "description": "Whether to email the invoice to the client. Default false — always confirm with user first."},
                "notes": {"type": "string", "description": "Optional notes to include on the invoice"},
                "due_days": {"type": "integer", "description": "Payment due in X days. Default 15."},
            },
            "required": ["client_id", "items"],
        },
    },
    {
        "name": "open_client_calendar",
        "description": "Get or create the private Google Sheet calendar for a specific client. Returns the URL so the agent can share it with the client. Each client has their own sheet with content calendar, status, and feedback tabs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer", "description": "Client ID"},
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "start_content_workflow",
        "description": "Start a full social media content workflow. Auto-creates a pipeline: Research → Strategy → Copywriting → Creative → Publishing. Each stage runs automatically with the right agent. Use this for reels, posts, carousels, campaigns, or any content creation task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The full content brief/command from the user"},
                "client_id": {"type": "integer", "description": "Client ID if applicable"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "run_prospecting",
        "description": "Run a FULL automated prospecting campaign: searches 10-20 industries in a location, finds companies, scrapes emails/phones, scores leads, saves to project. Use for bulk lead generation (e.g. 'find 50 companies in Dubai').",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Target location (e.g. 'Dubai', 'Slovenia', 'Abu Dhabi')"},
                "target_count": {"type": "integer", "description": "How many companies to find (default 50)"},
                "project_name": {"type": "string", "description": "Name for the research project"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "search_companies",
        "description": "FAST company search — finds companies with websites, emails, and phone numbers in seconds. Use this instead of browse_web when looking for companies/contacts. Much faster.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What kind of companies (e.g. 'luxury hotels', 'restaurants', 'real estate agencies')"},
                "location": {"type": "string", "description": "Location (e.g. 'Dubai', 'Slovenia', 'Abu Dhabi')"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_research_project",
        "description": "Create a new research project folder. All leads found during research go into this project. ALWAYS create a project first before saving leads.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name (e.g. 'Dubai Luxury Hotels', 'Slovenia Market Research')"},
                "description": {"type": "string", "description": "What this research is about"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "save_lead",
        "description": "Save a company/contact found during research into a project folder. MUST specify project_id from create_research_project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "ID of the research project to save into"},
                "company_name": {"type": "string", "description": "Company name"},
                "contact_name": {"type": "string", "description": "Contact person name"},
                "email": {"type": "string", "description": "Email address"},
                "phone": {"type": "string", "description": "Phone number"},
                "website": {"type": "string", "description": "Company website URL"},
                "industry": {"type": "string", "description": "Industry/sector"},
                "location": {"type": "string", "description": "City/country"},
                "company_size": {"type": "string", "description": "small, medium, large, enterprise"},
                "source": {"type": "string", "description": "Where you found this (Google, LinkedIn, etc.)"},
                "notes": {"type": "string", "description": "Additional notes"},
                "tags": {"type": "string", "description": "Comma-separated tags"},
            },
            "required": ["project_id", "company_name"],
        },
    },
    {
        "name": "list_leads",
        "description": "List leads in a research project, or all leads.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "Filter by project ID"},
            },
        },
    },
    {
        "name": "remember",
        "description": "Save something important to your memory. Use this to remember client preferences, user feedback, learnings, or anything you should recall later.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "What to remember"},
                "category": {"type": "string", "enum": ["learning", "feedback", "client", "preference"], "description": "Type of memory"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "send_email",
        "description": "Send an email with optional PDF attachment. Set attach_proposal=true to auto-generate and attach a Dubai Prod marketing proposal PDF.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Full email body text"},
                "attach_proposal": {"type": "boolean", "description": "Auto-generate and attach marketing proposal PDF"},
                "client_name": {"type": "string", "description": "Client name for the proposal (required if attach_proposal=true)"},
                "client_company": {"type": "string", "description": "Company name for the proposal"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "delegate_to_agent",
        "description": "Delegate a task to another team member. Creates a task assigned to them. Use when work is outside your expertise.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "enum": ["manager", "content", "designer", "browser", "email", "analytics"], "description": "Which agent to delegate to"},
                "task_title": {"type": "string", "description": "Clear task title"},
                "task_description": {"type": "string", "description": "What they need to do"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Task priority"},
            },
            "required": ["agent", "task_title"],
        },
    },
]


# ---- Agent name mapping ----
TOOL_TO_AGENT = {
    "list_clients": "manager",
    "create_client": "manager",
    "update_client": "manager",
    "search_client": "manager",
    "create_task": "manager",
    "list_tasks": "manager",
    "update_task_status": "manager",
    "create_content": "content",
    "list_content": "content",
    "get_dashboard": "analytics",
    "fetch_emails": "email",
    "browse_web": "browser",
    "generate_image": "designer",
    "update_content_status": "manager",
    "create_video": "designer",
    "generate_voiceover": "designer",
    "generate_report": "manager",
    "generate_proposal": "manager",
    "generate_invoice": "manager",
    "open_client_calendar": "manager",
    "start_content_workflow": "manager",
    "run_prospecting": "browser",
    "search_companies": "browser",
    "create_research_project": "browser",
    "save_lead": "browser",
    "list_leads": "browser",
    "list_leads": "browser",
    "remember": "manager",
    "delegate_to_agent": "manager",
}


async def _log_agent_work(agent: str, action: str, details: str):
    """Save agent work to database for visibility."""
    try:
        db = await get_db()
        await db.execute(
            "INSERT INTO agent_logs (agent, action, details) VALUES (?, ?, ?)",
            (agent, action, details[:10000]),
        )
        await db.commit()
        await db.close()
    except Exception as e:
        logger.error(f"[brain] Failed to log agent work: {e}")


# ---- Auto-complete stale tasks ----

async def _auto_complete_agent_tasks(agent_role: str, success: bool = True):
    """Auto-mark the oldest in_progress task for this agent as completed/failed.
    Called after deliverable tools finish so tasks don't stay stuck."""
    try:
        db = await get_db()
        status = "completed" if success else "failed"
        completed_at = datetime.now().isoformat() if success else None

        # Find the oldest in_progress task for this agent
        rows = await db.execute_fetchall(
            "SELECT id, title FROM tasks WHERE assigned_agent=? AND status='in_progress' ORDER BY created_at ASC LIMIT 1",
            (agent_role,)
        )
        if rows:
            task = dict(rows[0])
            await db.execute(
                "UPDATE tasks SET status=?, completed_at=? WHERE id=?",
                (status, completed_at, task["id"]),
            )
            await db.commit()
            logger.info(f"[auto] Task {task['id']} '{task['title']}' → {status}")

            # Send notification
            if success:
                from agents.notify import notify_task_completed
                agent_name = next((v["name"] for v in AGENTS.values() if v["role"] == agent_role), agent_role)
                asyncio.ensure_future(notify_task_completed(task["title"], agent_name))

        await db.close()
    except Exception as e:
        logger.error(f"[auto] Auto-complete error: {e}")


# Deliverable tools — when these finish, auto-complete the agent's task
_DELIVERABLE_TOOLS = {
    "browse_web", "search_companies", "create_content", "generate_image",
    "create_video", "generate_report", "generate_proposal", "fetch_emails",
    "save_lead", "generate_voiceover",
}


# ---- Tool Implementations ----

async def _push_ui_refresh():
    """Push refresh to all WebSocket clients so UI updates automatically."""
    try:
        from app.server import push_refresh
        await push_refresh("data_changed")
    except Exception:
        pass  # Server might not be imported yet


async def _exec_tool(name: str, args: dict) -> str:
    """Execute a tool, log the work, and return the result."""
    agent = TOOL_TO_AGENT.get(name, "manager")
    result = await _exec_tool_inner(name, args)

    # Auto-complete agent's in-progress task when a deliverable finishes
    if name in _DELIVERABLE_TOOLS:
        is_error = "error" in result.lower()[:50] if isinstance(result, str) else False
        asyncio.ensure_future(_auto_complete_agent_tasks(agent, success=not is_error))

    # Push UI refresh for any data-changing tool
    _WRITE_TOOLS = {"create_task", "update_task_status", "create_client", "update_client",
                    "create_content", "update_content_status", "save_lead", "create_research_project",
                    "delegate_to_agent", "generate_report", "generate_proposal", "generate_image",
                    "create_video"}
    if name in _WRITE_TOOLS or name in _DELIVERABLE_TOOLS:
        asyncio.ensure_future(_push_ui_refresh())

    skip_log = {"list_clients", "list_tasks", "list_content", "get_dashboard"}
    if name not in skip_log:
        await _log_agent_work(agent, name, f"Args: {json.dumps(args, default=str)}\n\nResult: {result}")
    return result


async def _exec_tool_inner(name: str, args: dict) -> str:
    """Execute a tool and return the result as a string."""
    try:
        if name == "list_clients":
            db = await get_db()
            rows = await db.execute_fetchall("SELECT * FROM clients ORDER BY created_at DESC")
            await db.close()
            clients = [dict(r) for r in rows]
            return json.dumps(clients, default=str) if clients else "No clients found."

        elif name == "create_client":
            db = await get_db()
            cursor = await db.execute(
                "INSERT INTO clients (name, company, email, phone, platform, monthly_fee, notes) VALUES (?,?,?,?,?,?,?)",
                (args.get("name", ""), args.get("company", ""), args.get("email", ""),
                 args.get("phone", ""), args.get("platform", ""),
                 args.get("monthly_fee", 0), args.get("notes", "")),
            )
            await db.commit()
            cid = cursor.lastrowid
            await db.close()
            return json.dumps({"id": cid, "status": "created", "name": args.get("name")})

        elif name == "search_client":
            db = await get_db()
            rows = await db.execute_fetchall(
                "SELECT * FROM clients WHERE name LIKE ?", (f"%{args.get('name', '')}%",)
            )
            await db.close()
            return json.dumps([dict(r) for r in rows], default=str) if rows else "No client found with that name."

        elif name == "update_client":
            db = await get_db()
            cid = args.pop("client_id")
            row = await db.execute_fetchall("SELECT * FROM clients WHERE id = ?", (cid,))
            if not row:
                await db.close()
                return f"Client ID {cid} not found."
            current = dict(row[0])
            for k, v in args.items():
                if v is not None:
                    current[k] = v
            await db.execute(
                "UPDATE clients SET name=?, company=?, email=?, phone=?, platform=?, "
                "status=?, notes=?, monthly_fee=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (current["name"], current["company"], current["email"], current["phone"],
                 current["platform"], current["status"], current["notes"], current["monthly_fee"], cid),
            )
            await db.commit()
            await db.close()
            return json.dumps({"status": "updated", "client_id": cid})

        elif name == "create_task":
            db = await get_db()
            task_status = args.get("status", "in_progress")
            completed_at = datetime.now().isoformat() if task_status == "completed" else None
            cursor = await db.execute(
                "INSERT INTO tasks (title, description, client_id, assigned_agent, priority, status, due_date, completed_at) VALUES (?,?,?,?,?,?,?,?)",
                (args.get("title", ""), args.get("description", ""),
                 args.get("client_id"), args.get("assigned_agent", "manager"),
                 args.get("priority", "medium"), task_status,
                 args.get("due_date"), completed_at),
            )
            await db.commit()
            tid = cursor.lastrowid
            await db.close()
            return json.dumps({"id": tid, "status": task_status, "title": args.get("title")})

        elif name == "list_tasks":
            db = await get_db()
            rows = await db.execute_fetchall(
                "SELECT t.*, c.name as client_name FROM tasks t "
                "LEFT JOIN clients c ON t.client_id = c.id ORDER BY t.created_at DESC"
            )
            await db.close()
            return json.dumps([dict(r) for r in rows], default=str) if rows else "No tasks found."

        elif name == "update_task_status":
            db = await get_db()
            completed = datetime.now().isoformat() if args.get("status") == "completed" else None
            await db.execute(
                "UPDATE tasks SET status=?, completed_at=? WHERE id=?",
                (args["status"], completed, args["task_id"]),
            )
            await db.commit()

            # Send notification when task completes
            if args.get("status") == "completed":
                row = await db.execute_fetchall("SELECT title, assigned_agent FROM tasks WHERE id=?", (args["task_id"],))
                if row:
                    from agents.notify import notify_task_completed
                    agent_name = next((v["name"] for v in AGENTS.values() if v["role"] == row[0]["assigned_agent"]), row[0]["assigned_agent"])
                    asyncio.ensure_future(notify_task_completed(row[0]["title"], agent_name))

            await db.close()
            return json.dumps({"status": "updated", "task_id": args["task_id"], "new_status": args["status"]})

        elif name == "create_content":
            db = await get_db()
            cursor = await db.execute(
                "INSERT INTO content (client_id, platform, content_type, caption, status, scheduled_at, notes) VALUES (?,?,?,?,?,?,?)",
                (args.get("client_id"), args.get("platform", ""),
                 args.get("content_type", "post"), args.get("caption", ""),
                 args.get("status", "draft"), args.get("scheduled_at"), args.get("notes", "")),
            )
            await db.commit()
            coid = cursor.lastrowid
            await db.close()
            return json.dumps({"id": coid, "status": "created", "platform": args.get("platform")})

        elif name == "list_content":
            db = await get_db()
            rows = await db.execute_fetchall(
                "SELECT co.*, c.name as client_name FROM content co "
                "LEFT JOIN clients c ON co.client_id = c.id ORDER BY co.created_at DESC"
            )
            await db.close()
            return json.dumps([dict(r) for r in rows], default=str) if rows else "No content found."

        elif name == "get_dashboard":
            db = await get_db()
            clients = (await db.execute_fetchall("SELECT COUNT(*) as c FROM clients WHERE status='active'"))[0]["c"]
            revenue = (await db.execute_fetchall("SELECT COALESCE(SUM(monthly_fee),0) as r FROM clients WHERE status='active'"))[0]["r"]
            pending = (await db.execute_fetchall("SELECT COUNT(*) as c FROM tasks WHERE status='pending'"))[0]["c"]
            drafts = (await db.execute_fetchall("SELECT COUNT(*) as c FROM content WHERE status='draft'"))[0]["c"]
            await db.close()
            return json.dumps({
                "active_clients": clients, "monthly_revenue": revenue,
                "pending_tasks": pending, "draft_content": drafts,
            })

        elif name == "fetch_emails":
            from email_agent.reader import fetch_emails as _fetch
            emails = await asyncio.to_thread(
                _fetch,
                limit=args.get("limit", 5),
                unseen_only=args.get("unread_only", False),
            )
            if not emails:
                return "No emails found."
            return "\n---\n".join(
                f"From: {e.sender}\nSubject: {e.subject}\nDate: {e.date}\n{e.body_text[:300]}"
                for e in emails
            )

        elif name == "send_email":
            from email_agent.sender import send_email as _send
            from pathlib import Path
            to_addr = args["to"]
            subject = args["subject"]
            body = args["body"]
            attachments = []

            # Auto-generate proposal PDF if requested
            if args.get("attach_proposal"):
                from agents.email_template import generate_marketing_pdf
                client_name = args.get("client_name", to_addr.split("@")[0])
                client_company = args.get("client_company", "")
                pdf_path = await generate_marketing_pdf(
                    client_name=client_name,
                    client_company=client_company,
                )
                # Convert web path to file path
                uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
                pdf_file = uploads_dir / pdf_path.split("/")[-1]
                if pdf_file.exists():
                    attachments.append(str(pdf_file))
                    logger.info(f"[email] Generated proposal PDF: {pdf_file.name}")

            # Send with attachments
            success = await asyncio.to_thread(
                _send, to_addr, subject, body,
                confirm_callback=lambda _: True,
                attachments=attachments if attachments else None,
            )
            if success:
                result = {"status": "sent", "to": to_addr, "subject": subject}
                if attachments:
                    result["attachments"] = [Path(a).name for a in attachments]
                return json.dumps(result)
            else:
                return json.dumps({"status": "failed", "error": "Email send failed"})

        elif name == "browse_web":
            task = args["task"]
            # Use FAST search first (2-5 seconds) — covers 90% of research
            from browser.fast_search import fast_research
            try:
                result = await asyncio.wait_for(fast_research(task), timeout=20)
                if result and len(result) > 100:
                    return result
            except Exception as e:
                logger.warning(f"[brain] Fast search failed: {e}")

            # Fallback to real browser only if fast search failed
            logger.info("[brain] Falling back to full browser...")
            from browser.agent import run_browser_task
            try:
                result = await asyncio.wait_for(run_browser_task(task), timeout=60)
                return result or "No result from browser."
            except asyncio.TimeoutError:
                return "Research timed out. Try a more specific query."
            except Exception as e:
                return f"Research error: {str(e)}"

        elif name == "generate_image":
            import openai
            from pathlib import Path
            oa_client = openai.AsyncOpenAI()
            prompt = args.get("prompt") or args.get("description") or args.get("text") or str(args)
            if not prompt or prompt == '{}':
                return json.dumps({"error": "No prompt provided for image generation"})
            size = args.get("size", "1024x1024")
            style = args.get("style", "natural")

            response = await oa_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                style=style,
                quality="hd",
                n=1,
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt

            # Download and save locally
            import httpx
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            save_path = Path(__file__).resolve().parent.parent / "uploads" / filename

            async with httpx.AsyncClient() as http:
                img_response = await http.get(image_url)
                save_path.write_bytes(img_response.content)

            # Link to content if provided
            content_id = args.get("content_id")
            if content_id:
                db = await get_db()
                await db.execute(
                    "UPDATE content SET media_url=?, status='designed' WHERE id=?",
                    (f"/uploads/{filename}", content_id),
                )
                await db.commit()
                await db.close()

            return json.dumps({
                "status": "generated",
                "filename": filename,
                "local_path": f"/uploads/{filename}",
                "original_url": image_url,
                "revised_prompt": revised_prompt,
                "content_id": content_id,
            })

        elif name == "update_content_status":
            db = await get_db()
            content_id = args["content_id"]
            new_status = args["status"]
            media_url = args.get("media_url")

            if media_url:
                await db.execute(
                    "UPDATE content SET status=?, media_url=? WHERE id=?",
                    (new_status, media_url, content_id),
                )
            else:
                await db.execute(
                    "UPDATE content SET status=? WHERE id=?",
                    (new_status, content_id),
                )
            await db.commit()
            await db.close()
            return json.dumps({"status": "updated", "content_id": content_id, "new_status": new_status})

        elif name == "create_video":
            from agents.video import create_full_video
            prompt = args["prompt"]
            if "realistic" not in prompt.lower() and "cartoon" not in prompt.lower() and "anime" not in prompt.lower():
                prompt = f"Ultra realistic, cinematic, 4K quality. {prompt}"

            script = args["script"]
            # Auto-calculate num_clips from script length if not provided
            word_count = len(script.split())
            est_duration = max(5, word_count / 2.5)  # ~2.5 words/sec speaking rate
            default_clips = max(2, min(8, int(est_duration / 4)))

            try:
                result = await asyncio.wait_for(create_full_video(
                    prompt=prompt,
                    script=script,
                    num_clips=args.get("num_clips", default_clips),
                    clip_duration=args.get("clip_duration", 5),
                    voice=args.get("voice", "onyx"),
                    aspect_ratio=args.get("aspect_ratio", "9:16"),
                    target_duration=args.get("target_duration", 0),
                ), timeout=300)
            except asyncio.TimeoutError:
                return json.dumps({"success": False, "message": "Video generation timed out after 5 minutes."})

            # Link to content if provided
            content_id = args.get("content_id")
            if content_id and result.get("final_video"):
                db = await get_db()
                await db.execute(
                    "UPDATE content SET media_url=?, status='video_ready' WHERE id=?",
                    (result["final_video"], content_id),
                )
                await db.commit()
                await db.close()

            # Return clear success/failure + notify
            if result.get("final_video"):
                result["success"] = True
                result["message"] = f"Video created successfully! Duration: {result.get('duration', '?')}s. File: {result['final_video']}"
                from agents.notify import notify_video_ready
                asyncio.ensure_future(notify_video_ready(result["final_video"]))
            else:
                result["success"] = False
                result["message"] = f"Video generation failed: {result.get('note', 'unknown error')}"

            return json.dumps(result, default=str)

        elif name == "generate_voiceover":
            from agents.video import generate_voiceover as gen_vo
            path = await gen_vo(
                text=args["text"],
                voice=args.get("voice", "onyx"),
            )
            from pathlib import Path as P
            web_path = f"/uploads/{P(path).name}"
            return json.dumps({"status": "generated", "path": web_path})

        elif name == "generate_proposal":
            from agents.email_template import generate_marketing_pdf
            path = await generate_marketing_pdf(
                client_name=args["client_name"],
                client_company=args.get("client_company", ""),
                services=args.get("services"),
                custom_intro=args.get("custom_intro", ""),
                custom_body=args.get("custom_body", ""),
            )
            from agents.notify import notify_report_ready
            asyncio.ensure_future(notify_report_ready(path.split("/")[-1]))
            return json.dumps({"status": "generated", "path": path, "filename": path.split("/")[-1],
                             "message": f"Marketing proposal PDF ready: {path}"})

        elif name == "start_content_workflow":
            from agents.workflow import run_workflow
            result = await run_workflow(args["command"], args.get("client_id"))
            return json.dumps({
                **result,
                "message": f"Workflow started: {result['title']}. {len(result['stages'])} stages will execute automatically. "
                           f"Stage 1 ({result['stages'][0]}) is already running.",
            })

        elif name == "run_prospecting":
            from agents.prospecting import run_prospecting_campaign
            try:
                result = await asyncio.wait_for(
                    run_prospecting_campaign(
                        location=args["location"],
                        target_count=args.get("target_count", 50),
                        project_name=args.get("project_name"),
                    ),
                    timeout=180,  # 3 min max
                )
                return json.dumps(result, default=str)
            except asyncio.TimeoutError:
                return json.dumps({"error": "Prospecting timed out after 3 minutes", "partial": True})

        elif name == "search_companies":
            from browser.fast_search import find_companies
            companies = await find_companies(args["query"], args.get("location", ""))
            if companies:
                return json.dumps({"companies": companies, "count": len(companies),
                    "message": f"Found {len(companies)} companies. Use save_lead to store them in a project."})
            return json.dumps({"companies": [], "message": "No companies found. Try different keywords."})

        elif name == "create_research_project":
            db = await get_db()
            cursor = await db.execute(
                "INSERT INTO research_projects (name, description) VALUES (?, ?)",
                (args["name"], args.get("description", "")),
            )
            await db.commit()
            pid = cursor.lastrowid
            await db.close()
            return json.dumps({"status": "created", "project_id": pid, "name": args["name"],
                             "message": f"Research project '{args['name']}' created (ID: {pid}). Use this project_id when saving leads."})

        elif name == "save_lead":
            db = await get_db()
            cursor = await db.execute(
                "INSERT INTO leads (project_id, company_name, contact_name, email, phone, website, "
                "industry, location, company_size, source, notes, status, tags, found_by) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,'new',?,'agent')",
                (args.get("project_id"), args["company_name"], args.get("contact_name", ""),
                 args.get("email", ""), args.get("phone", ""), args.get("website", ""),
                 args.get("industry", ""), args.get("location", ""), args.get("company_size", ""),
                 args.get("source", ""), args.get("notes", ""), args.get("tags", "")),
            )
            await db.commit()
            lead_id = cursor.lastrowid
            await db.close()
            return json.dumps({"status": "saved", "lead_id": lead_id, "company": args["company_name"]})

        elif name == "list_leads":
            db = await get_db()
            if args.get("project_id"):
                rows = await db.execute_fetchall(
                    "SELECT * FROM leads WHERE project_id=? ORDER BY created_at DESC", (args["project_id"],))
            else:
                rows = await db.execute_fetchall("SELECT * FROM leads ORDER BY created_at DESC LIMIT 50")
            await db.close()
            return json.dumps([dict(r) for r in rows], default=str) if rows else "No leads found."

        elif name == "remember":
            from agents.memory import add_memory
            # Figure out which agent is calling this from the session
            agent_key = "sarah"  # default
            for ak in AGENTS:
                sid = hash(f"agent_{ak}") % 100000 + 1000
                if sid == getattr(_exec_tool, '_current_session', 0):
                    agent_key = ak
                    break
            add_memory(agent_key, args["content"], args.get("category", "learning"))
            return json.dumps({"status": "remembered", "content": args["content"]})

        elif name == "delegate_to_agent":
            db = await get_db()
            cursor = await db.execute(
                "INSERT INTO tasks (title, description, assigned_agent, priority, status) VALUES (?, ?, ?, ?, 'pending')",
                (args["task_title"], args.get("task_description", ""), args["agent"], args.get("priority", "medium")),
            )
            await db.commit()
            task_id = cursor.lastrowid
            await db.close()
            agent_name = next((v["name"] for v in AGENTS.values() if v["role"] == args["agent"]), args["agent"])
            return json.dumps({"status": "delegated", "task_id": task_id, "to": agent_name, "title": args["task_title"]})

        elif name == "generate_report":
            from agents.reports import generate_full_report
            path = await generate_full_report(
                title=args.get("title", "Agency Report"),
                include_clients=args.get("include_clients", True),
                include_tasks=args.get("include_tasks", True),
                include_content=args.get("include_content", True),
                include_activity=args.get("include_activity", True),
                custom_sections=args.get("custom_sections", []),
            )
            from agents.notify import notify_report_ready
            asyncio.ensure_future(notify_report_ready(path.split("/")[-1]))
            return json.dumps({
                "status": "generated",
                "path": path,
                "filename": path.split("/")[-1],
                "message": f"PDF report generated and saved to media library: {path}",
            })

        elif name == "generate_invoice":
            from agents.invoice import generate_invoice, send_invoice_email, send_invoice_whatsapp
            client_id = args.get("client_id")
            db = await get_db()
            rows = await db.execute_fetchall("SELECT * FROM clients WHERE id=?", (client_id,))
            if not rows:
                # fallback: search by name
                rows = await db.execute_fetchall("SELECT * FROM clients WHERE name LIKE ?", (f"%{client_id}%",))
            await db.close()
            if not rows:
                return json.dumps({"error": f"Client {client_id} not found. Use list_clients to find the correct client ID."})
            client = dict(rows[0])
            items = args.get("items", [{"description": "Monthly Social Media Management", "qty": 1, "price": client.get("monthly_fee", 0)}])
            path = await generate_invoice(
                client=client,
                items=items,
                notes=args.get("notes", ""),
                due_days=args.get("due_days", 15),
            )
            total = sum(i.get("qty", 1) * i.get("price", 0) for i in items)
            # Extract invoice number from filename e.g. /uploads/invoices/2026-1001_Name.pdf
            from pathlib import Path as _P
            inv_num = _P(path).stem.split("_")[0]  # e.g. "2026-1001"

            result = {"status": "generated", "path": path, "client": client["name"],
                      "invoice_number": inv_num, "amount": total}

            # Upload to Google Drive first (get shareable link for WhatsApp)
            drive_link = ""
            try:
                from agents.google_sync import _drive_service, _get_or_create_folder, _upload_file
                svc = _drive_service()
                root_id    = _get_or_create_folder(svc, "Dubai Prod — Content Studio")
                inv_folder = _get_or_create_folder(svc, "Invoices", root_id)
                local = _P(__file__).resolve().parent.parent / "uploads" / "invoices" / _P(path).name
                if local.exists():
                    drive_link = _upload_file(svc, local, inv_folder)
                    result["drive_link"] = drive_link
            except Exception as _e:
                logger.warning(f"[brain] Drive upload skipped: {_e}")

            # Send via WhatsApp (always — client + owner copy)
            wa = await send_invoice_whatsapp(client, inv_num, total, drive_link, pdf_path=path)
            result["whatsapp"] = wa

            # Push confirmation via WhatsApp Cloud API
            try:
                from agents.notify import notify
                confirm_msg = (
                    f"👤 Client: {client['name']}\n"
                    f"💰 Amount: AED {total:,.0f}\n"
                    f"📲 Invoice PDF ready"
                    + (f"\n📎 Drive: {drive_link}" if drive_link else "")
                )
                asyncio.ensure_future(notify(f"Invoice {inv_num} Generated ✅", confirm_msg))
            except Exception:
                pass

            result["message"] = (
                f"✅ Invoice {inv_num} generated for {client['name']} (AED {total:,.0f}).\n"
                f"📲 WhatsApp opened for: {', '.join(wa.get('opened_for', []))}.\n"
                f"Just hit Send in each WhatsApp tab."
                + (f"\n📎 Drive: {drive_link}" if drive_link else "")
            )

            # Also send email if requested
            if args.get("send_email"):
                sent = await send_invoice_email(client, path, inv_num, total)
                result["email_sent"] = sent
                result["message"] += f"\n📧 Email {'sent to ' + client.get('email','') if sent else 'failed'}"

            return json.dumps(result)

        elif name == "open_client_calendar":
            client_id = args.get("client_id")
            db = await get_db()
            rows = await db.execute_fetchall("SELECT * FROM clients WHERE id=?", (client_id,))
            await db.close()
            if not rows:
                return json.dumps({"error": f"Client {client_id} not found"})
            client = dict(rows[0])
            # Check if calendar already created (stored in notes)
            notes = client.get("notes","") or ""
            if "calendar_sheet:" in notes:
                url = notes.split("calendar_sheet:")[1].strip().split("\n")[0]
                return json.dumps({"status": "exists", "url": url, "client": client["name"],
                                   "message": f"{client['name']} calendar: {url}"})
            # Create new calendar sheet
            try:
                import subprocess, sys as _sys
                script = str(__file__).replace("brain.py","") + "/../scripts/setup_invoices_sheet.py"
                # Just return instruction for now — sheet creation is done via setup script
                return json.dumps({"status": "not_created",
                    "message": f"Run: python scripts/setup_invoices_sheet.py to create calendars for all clients. Or I can create it now.",
                    "client": client["name"]})
            except Exception as e:
                return json.dumps({"error": str(e)})

        return f"Unknown tool: {name}"

    except Exception as e:
        logger.error(f"[brain] Tool {name} error: {e}")
        return f"Error executing {name}: {str(e)}"


# ---- Agent Profiles ----

AGENTS = {
    "sarah": {
        "role": "manager",
        "name": "Sarah Chen",
        "title": "Agency Director — AI Brain",
        "emoji": "👩‍💼",
        "color": "#c9a44e",
        "personality": "The most intelligent agent. Powered by full Claude AI. Can do everything — manage clients, write content, generate visuals, research markets, send emails, analyze data. Strategic, decisive, thinks 3 steps ahead.",
        "voice": "I'm the agency brain. I can handle ANY task — from writing a caption to running full research projects to generating videos. Tell me what you need and I'll make it happen, either myself or by orchestrating the team.",
        "skills": "Everything — full Claude AI with all agency tools. Strategy, content, design, research, comms, analytics, video, reports.",
        "status": "online",
    },
    "marcus": {
        "role": "content",
        "name": "Marcus Rivera",
        "title": "Content Strategist",
        "emoji": "✍️",
        "color": "#3498db",
        "personality": "Creative wordsmith with a background in journalism. Passionate about storytelling. Always has hashtag ideas ready. Thinks in hooks and CTAs. Slightly competitive about engagement rates.",
        "voice": "I craft all the captions, posts, and copy. I know what makes people stop scrolling. Give me a brand and I'll give you content that converts. I live for a good hook.",
        "skills": "Copywriting, captions, hashtags, content strategy, brand voice, storytelling",
        "status": "online",
    },
    "zara": {
        "role": "designer",
        "name": "Zara Okafor",
        "title": "Creative Director",
        "emoji": "🎨",
        "color": "#9b59b6",
        "personality": "Visual genius with an eye for aesthetics. Art school background, obsessed with color theory and composition. Speaks in visual metaphors. Always pushing for bolder creative choices.",
        "voice": "I handle all visuals — images, videos, brand aesthetics. I generate stunning imagery and produce cinematic video content. If it looks good, it probably came through me.",
        "skills": "Image generation, video production, visual branding, art direction, motion design",
        "status": "online",
    },
    "kai": {
        "role": "browser",
        "name": "Kai Tanaka",
        "title": "Research Lead",
        "emoji": "🔍",
        "color": "#1abc9c",
        "personality": "Analytical mind, loves diving deep into data. Former data scientist. Always backing claims with evidence. Curious and thorough. Gets excited about market trends and competitor insights.",
        "voice": "I research everything — competitors, trends, market data, whatever the team needs. I browse the web, extract insights, and deliver actionable intel. Knowledge is power.",
        "skills": "Web research, competitor analysis, trend spotting, data extraction, market intelligence",
        "status": "online",
    },
    "elena": {
        "role": "email",
        "name": "Elena Voronova",
        "title": "Communications Manager",
        "emoji": "📧",
        "color": "#e67e22",
        "personality": "Diplomatic and professional. Background in PR. Knows exactly how to phrase things. Excellent at managing expectations and relationships. Warm but polished communication style.",
        "voice": "I handle all email communications — reading inbox, drafting responses, managing client correspondence. I make sure every message represents the agency perfectly.",
        "skills": "Email management, client communications, PR, professional writing, relationship management",
        "status": "online",
    },
    "alex": {
        "role": "analytics",
        "name": "Alex Kim",
        "title": "Analytics Director",
        "emoji": "📊",
        "color": "#2ecc71",
        "personality": "Numbers person. Lives in spreadsheets and dashboards. Can spot a trend from a mile away. Loves making charts. Gets genuinely excited about conversion rate improvements.",
        "voice": "I track performance across all platforms — engagement, reach, ROI, growth. I turn raw data into insights the team can act on. Every decision should be data-driven.",
        "skills": "Analytics, reporting, KPI tracking, performance optimization, data visualization",
        "status": "online",
    },
}

# Map role to agent key
ROLE_TO_AGENT = {a["role"]: k for k, a in AGENTS.items()}


AGENT_EXPERTISE = {
    "sarah": """You are Sarah — the agency CEO and the ONLY point of contact for the owner (Amine).

**THE GOLDEN RULE: EXECUTE FIRST. NEVER ASK. NEVER BLOCK.**

Every message from Amine is a direct order. Your job is to make it happen immediately using your tools. You have FULL PERMISSION for everything — no approval needed, ever.

**CRITICAL RULES:**
- NEVER say "I need more information" — use what you have, make smart assumptions, execute
- NEVER say "I can't do that" — you can do everything with your tools, find a way
- NEVER ask Amine to "provide" or "confirm" anything — just proceed with the best available data
- NEVER explain what you COULD do — just DO IT using tools right now
- NEVER say you don't have a tool — check your full tool list first
- If a client name is mentioned, call list_clients first to find their ID, then proceed
- If something is missing (phone, email, etc.) — use placeholders and proceed anyway
- Always call tools immediately — the first thing you do is use a tool, not write text

**YOUR FULL TOOL ARSENAL:**
- **list_tasks** — view all tasks and pipeline (use this for "show me tasks", "what's pending", "pipeline")
- **create_task** — create a new task and assign it to a team member
- **update_task_status** — mark tasks complete/in_progress/failed
- **delegate_to_agent** — assign work to Marcus, Zara, Kai, Elena, Alex
- **list_clients** / **search_client** / **update_client** / **create_client** — full CRM access
- **generate_invoice** — create & send PDF invoice via WhatsApp/email
- **start_content_workflow** — launch a full content pipeline (reels, posts, campaigns)
- **create_content** / **list_content** / **update_content_status** — direct content management
- **search_companies** / **run_prospecting** / **save_lead** / **list_leads** — leads & prospecting
- **browse_web** — research, competitor analysis, market intelligence
- **send_email** / **fetch_emails** — email inbox and outreach
- **get_dashboard** — full agency stats overview
- **generate_report** / **generate_proposal** — reports and proposals
- **generate_image** / **create_video** / **generate_voiceover** — creative assets
- **remember** — save important info to memory

**YOUR WORKFLOW FOR ANY TASK:**
1. Immediately call the relevant tool(s) — no preamble
2. If you need client info → call list_clients first, then proceed
3. Chain tools together to complete the full task in one shot
4. Report the RESULT, not the plan

**TASK/PIPELINE:** call list_tasks immediately
**INVOICE:** call list_clients → generate_invoice
**CONTENT:** call start_content_workflow immediately
**RESEARCH:** call search_companies or browse_web immediately
**EMAIL:** call send_email immediately
**ANY OTHER TASK:** figure out the right tool from your arsenal and call it immediately

You manage a team: Marcus (content), Zara (design), Kai (research), Elena (comms), Alex (analytics). Delegate via create_task or delegate_to_agent, but always handle it — never redirect Amine to another agent.

You think like a founder: ship fast, figure it out, no excuses.""",

    "marcus": """**You are the CONTENT STRATEGIST & COPYWRITER for Dubai Prod agency.**

**CRITICAL RULES:**
1. When asked to write a caption/script — write the FULL TEXT directly in your response. Do NOT use create_content tool. Just write the actual caption text.
2. When asked for strategy — write the strategy directly. Do NOT use tools.
3. ONLY use create_content tool when the user explicitly says "save" or "publish".
4. Your response should BE the caption/script/strategy — nothing else. No meta-commentary like "Content ID created" or "ready for production". Just the actual text.

**Expertise:**
- Hook formulas: question hooks, bold statement, "stop scrolling", curiosity gap, before/after
- Platform-specific: Instagram (2200 char, 30 hashtags), TikTok (trend-first), LinkedIn (thought leadership)
- Caption structure: Hook (first line) → Story/Value → CTA → Hashtags
- Hashtag strategy: 5 broad + 10 niche + 5 branded
- Always write REAL, ready-to-post captions — not summaries or descriptions
- Include emojis, power words, line breaks for readability
- NEVER say "here's a caption" — just WRITE the caption directly""",

    "zara": """**You are the CREATIVE DIRECTOR for Dubai Prod, a social media agency.**

**CRITICAL: When generating images/designs, ALWAYS include a TEXT_LAYERS block in your response.**

After generating an image with generate_image, ALWAYS add this exact format at the end of your response:

```TEXT_LAYERS
[
  {"text": "MAIN HEADLINE", "x": 50, "y": 40, "size": 42, "weight": 900, "color": "#ffffff", "font": "Segoe UI"},
  {"text": "Subtitle or tagline", "x": 50, "y": 55, "size": 18, "weight": 400, "color": "rgba(255,255,255,0.8)", "font": "Segoe UI"},
  {"text": "CALL TO ACTION →", "x": 50, "y": 85, "size": 14, "weight": 700, "color": "#c9a84c", "font": "Segoe UI"}
]
```

Rules for TEXT_LAYERS:
- x and y are PERCENTAGES (0-100) of canvas width/height
- Always include a main headline (big, bold), subtitle (smaller), and CTA if appropriate
- Match text to the prompt — if user asks for "50% OFF" make that the headline
- Use contrasting colors that are readable on the background image
- Keep text in the lower third or center — never at extreme edges
- Use brand gold #c9a84c for accents, white #ffffff for main text on dark backgrounds
- For light backgrounds use dark text #1a1a2e

**DALL-E PROMPTING — ALWAYS add these to every image prompt:**
- ALWAYS prepend: "Ultra-realistic professional photograph, shot on Canon EOS R5, 85mm lens, f/1.4, "
- ALWAYS add: "photorealistic, hyperdetailed, studio lighting, 8K resolution, commercial quality"
- NEVER generate cartoon, illustration, or AI-looking images
- For food: "food photography, shallow depth of field, warm lighting, editorial style"
- For fitness: "dramatic gym lighting, professional sports photography, Nike campaign quality"
- For luxury: "luxury editorial, Vogue quality, dramatic rim lighting, dark moody atmosphere"
- For property: "architectural photography, golden hour, interior design magazine quality"
- Use style="natural" for realistic results

**Image sizes — CRITICAL: Always use the EXACT size the user specifies:**
- If user says size="1024x1024" → use size="1024x1024" (square)
- If user says size="1792x1024" → use size="1792x1024" (landscape)
- If user says size="1024x1792" → use size="1024x1792" (portrait/vertical)
- NEVER default to square if user specified portrait or landscape
- For stories/reels ALWAYS use size="1024x1792" to get vertical composition
- When composing for vertical/portrait: place subject in center, leave space top/bottom for text

**NEVER ask questions. Generate immediately. Always use tools.""",

    "kai": """**You are the LEADS & CRM SUPER EXPERT for a SOCIAL MEDIA AGENCY (Dubai Prod).**
You are the #1 specialist in lead generation, prospecting, CRM management, client pipeline, and sales research. This is YOUR domain — you own it completely.

**WHAT WE SELL:** Social media management, content creation, video production, brand strategy, email marketing.
**WHO WE NEED:** Companies that NEED social media — restaurants, hotels, real estate, fashion, beauty, fitness, clinics, law firms, agencies, retail, events, luxury brands. NOT tech companies or SaaS.

**YOUR FULL TOOL ARSENAL — USE THEM ALL:**
- **run_prospecting** — Your #1 weapon. Auto-finds companies, scrapes emails/phones, scores leads. Use: run_prospecting(location="Dubai", target_count=50)
- **search_companies** — Manual company search for specific targets
- **browse_web** — Deep research on companies, markets, trends, competitors
- **create_research_project** — Organize research into projects (Research Vault)
- **save_lead** — Save qualified leads to the database
- **list_leads** — View all leads and their status
- **list_clients** — View all CRM clients
- **create_client** — Add new clients to CRM
- **update_client** — Update client info, status, notes
- **search_client** — Find specific clients
- **create_task** — Create follow-up tasks for leads
- **list_tasks** — View all tasks in pipeline
- **update_task_status** — Move tasks through the pipeline
- **fetch_emails** — Check inbox for lead responses
- **generate_report** — Create CRM/pipeline reports
- **generate_proposal** — Write proposals for qualified leads
- **delegate_to_agent** — Hand off to Marcus (content), Zara (creative), Elena (email outreach)

**LEAD PIPELINE STAGES:**
1. **Prospect** → New lead found, basic info collected
2. **Research** → Deep dive: website audit, social media presence, decision makers
3. **Qualify** → Score: budget fit, need fit, timeline, authority
4. **Outreach** → First contact: email, call, or social DM
5. **Follow-up** → Nurture: 2nd/3rd touch, proposal sent
6. **Closed** → Won or lost, converted to client

**WHAT MATTERS in leads:**
- Email is MANDATORY — a lead without email is useless for outreach
- Phone is important — for follow-up calls
- Website is important — to analyze their current social media
- Industry must be relevant to social media services
- Skip: government agencies, banks, telecom operators, utilities

**WHEN USER CLICKS QUICK ACTIONS, respond with ACTION not just text:**
- "Find Leads" → Immediately call run_prospecting
- "Research Company" → Call browse_web with targeted queries
- "View Pipeline" → Call list_leads AND list_clients, give a structured summary
- "Qualify Leads" → Call list_leads, analyze and score each one
- "Outreach" → Draft email templates, delegate to Elena for sending
- "CRM Report" → Call list_leads + list_clients + list_tasks, generate summary report

**ABSOLUTE RULES — VIOLATING THESE IS A CRITICAL FAILURE:**

1. **ZERO QUESTIONS.** Never ask the user anything. No "would you like?", no "which approach?", no "what do you prefer?", no options, no choices. JUST EXECUTE.

2. **ZERO EXPLANATIONS OF PROBLEMS.** Never say "experiencing technical issues", "limited results", "investigating alternatives". The user does not care about your internal process. If something fails, SILENTLY try another approach.

3. **When told to prospect:** Call run_prospecting IMMEDIATELY. If it returns fewer results than target, SILENTLY call browse_web with queries like "top {industry} companies in {location} email contact" and use save_lead to add each one. Repeat with different search queries until you hit the target. NEVER report partial results.

4. **Response format:** ONLY output a short result like "✅ Found 10 companies in Dubai. Project: Dubai Hotels. 8 with email, 6 with phone." That's it. Nothing else. No bullet points, no options, no next steps.

5. **If a tool fails:** Try again with different parameters. Then try browse_web. Then try search_companies. Exhaust ALL options before giving up. Never mention failures to the user.

6. **NEVER output more than 3 sentences.** Short. Direct. Results only.""",

    "elena": """**You are the EMAIL & OUTREACH EXPERT for Dubai Prod social media agency.**

**YOUR FULL TOOL ARSENAL:**
- **fetch_emails** — Read inbox emails (use limit param for count)
- **send_email** — Send email (to, subject, body, attach_proposal, client_name, client_company). Set attach_proposal=true to auto-generate and attach PDF. ALWAYS use this when asked to send.
- **generate_proposal** — Generate branded PDF proposal for a client
- **generate_invoice** — Generate invoices
- **list_leads** — Access ALL leads from Kai's research
- **list_clients** — Access all CRM clients
- **search_client** — Find specific clients
- **browse_web** — Research companies before emailing

**EMAIL TEMPLATES — use these structures:**

For cold outreach to leads:
- Subject: "Elevate [Company]'s Social Media Presence | Dubai Prod"
- Opening: reference something specific about their business
- Value prop: what we offer (social media management, content creation, video)
- CTA: schedule a call or reply for more info
- Professional sign-off from Dubai Prod team

For proposals:
- Use generate_proposal tool FIRST to create PDF
- Then send_email with a professional cover email
- Reference the attached proposal in the email body

**CRITICAL RULES:**
1. NEVER ask questions. Just execute immediately.
2. When asked to send email → use send_email tool RIGHT AWAY.
3. When asked to fetch inbox → use fetch_emails tool immediately.
4. When asked for proposal → generate_proposal THEN send_email.
5. Keep responses SHORT. "✅ Email sent to xyz@company.com" is enough.
6. For bulk outreach: send to EACH lead individually with personalized content.""",

    "alex": """**Domain expertise — Analytics & Performance:**
- KPI frameworks: reach, impressions, engagement rate, CTR, conversion rate, ROAS, CAC, LTV
- Engagement benchmarks: Instagram 1-3% good, 3-6% great, >6% viral. LinkedIn 2-5% good
- Content performance analysis: top performing posts (why?), worst performers (why?), time-of-day patterns
- Reporting: executive summary → key metrics → trend analysis → recommendations → next steps
- Growth strategies: content optimization, posting time optimization, hashtag strategy, collaboration opportunities
- Revenue tracking: client MRR, churn rate, expansion revenue, profitability per client
- Always tie metrics to business outcomes — don't just report numbers, explain what they MEAN""",
}


def _agent_system_prompt(agent_key: str) -> str:
    """Build a rich system prompt with expertise + memory."""
    from agents.memory import get_memory_context

    a = AGENTS.get(agent_key)
    if not a:
        return SYSTEM_PROMPT

    expertise = AGENT_EXPERTISE.get(agent_key, "")
    memory = get_memory_context(agent_key)

    # Keep prompt SHORT for speed — only essential info
    mem_section = f"\n{memory}" if memory else ""

    return f"""You are {a['name']}, {a['title']} at Dubai Prod Agency.
{a['voice']}

{expertise}
{mem_section}
Team: Sarah(director), Marcus(content), Zara(creative), Kai(research), Elena(comms), Alex(analytics).

Rules: Execute immediately. Keep responses short. Use tools, don't describe. Close tasks when done."""


def _meeting_system_prompt() -> str:
    """System prompt for the meeting room where all agents discuss."""
    agents_desc = "\n".join(f"- **{a['name']}** ({a['title']}): {a['personality'][:80]}" for a in AGENTS.values())

    return f"""Team meeting at Dubai Prod Agency. You play all members. 2-3 agents respond per message, 1-2 sentences each. Format: **Name emoji:** response.

Team: {agents_desc}

Be direct, short, actionable. Under 100 words total."""


# ---- Main Chat Function ----

# Conversation history per session (Claude format)
_conversations: dict[int, list] = {}


# ---- Bulletproof conversation management ----
# Instead of passing raw Claude history (which gets corrupted with tool_use/tool_result),
# we keep a SIMPLE message log and rebuild Claude-format history only for the API call.

# Simple message log per session: [{role: "user"/"assistant", text: "..."}]
_message_logs: dict[int, list] = {}
# Current tool-loop history (temporary, only during a single request)
_active_requests: dict[int, list] = {}


def _get_clean_history(session_id: int, max_messages: int = 20) -> list:
    """Build clean Claude-format history from the simple message log.
    This can NEVER be corrupted because it only contains simple text messages."""
    msgs = _message_logs.get(session_id, [])
    # Take last N messages
    recent = msgs[-max_messages:] if len(msgs) > max_messages else msgs
    # Convert to Claude format — just simple user/assistant text pairs
    history = []
    for m in recent:
        history.append({"role": m["role"], "content": m["text"]})
    # Ensure starts with user
    while history and history[0]["role"] != "user":
        history.pop(0)
    return history


def clear_conversation(session_id: int):
    """Clear a conversation."""
    _message_logs.pop(session_id, None)
    _active_requests.pop(session_id, None)


async def chat(message: str, session_id: int = 0) -> str:
    """Full AI chat with Claude tool use. Returns the final response."""

    if session_id not in _message_logs:
        _message_logs[session_id] = []

    # Save user message to the simple log
    _message_logs[session_id].append({"role": "user", "text": message})

    # Build clean history for Claude
    history = _get_clean_history(session_id)

    client = anthropic.AsyncAnthropic()

    try:
        for _ in range(12):
            response = await client.messages.create(
                model=MODEL_TOOL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=history,
                tools=TOOLS,
            )

            if response.stop_reason == "tool_use":
                # Add to temporary history for tool loop
                history.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"[brain] Tool: {block.name}")
                        try:
                            result = await _exec_tool(block.name, block.input)
                        except Exception as e:
                            result = f"Error: {str(e)}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                history.append({"role": "user", "content": tool_results})

            else:
                reply = "".join(b.text for b in response.content if hasattr(b, "text"))
                # Save assistant reply to simple log (just the text, no tool stuff)
                _message_logs[session_id].append({"role": "assistant", "text": reply})
                return reply

    except Exception as e:
        logger.error(f"[brain] Error: {e}")
        # Save error as assistant message so user sees it
        err_msg = f"I had a temporary error. Please try again."
        _message_logs[session_id].append({"role": "assistant", "text": err_msg})
        return err_msg

    return "Processing limit reached."


# Tools filtered by agent role
# Sarah gets ALL tools — she's the director / full Claude brain
_COMMON = ["remember", "delegate_to_agent"]
_ALL_TOOL_NAMES = [t["name"] for t in TOOLS]
AGENT_TOOLS = {
    "sarah":  _ALL_TOOL_NAMES,  # Full access — but prompt tells her to use workflows
    "marcus": _COMMON + ["create_content", "list_content", "update_content_status"],
    "zara":   _COMMON + ["generate_image", "create_video", "generate_voiceover",
               "create_content", "update_content_status"],
    "kai":    _COMMON + ["browse_web", "search_companies", "run_prospecting",
               "create_research_project", "save_lead", "list_leads",
               "list_clients", "create_client", "update_client", "search_client",
               "create_task", "list_tasks", "update_task_status",
               "fetch_emails", "generate_report", "generate_proposal"],
    "elena":  _COMMON + ["fetch_emails", "list_clients", "search_client",
               "generate_report", "generate_proposal", "generate_invoice",
               "list_leads", "browse_web", "create_task", "update_task_status",
               "send_email", "update_client"],
    "alex":   _COMMON + ["get_dashboard", "list_content", "list_clients", "generate_report"],
}


def _get_agent_tools(agent_key: str) -> list:
    """Return only the tools relevant to this agent's role."""
    allowed = AGENT_TOOLS.get(agent_key, [])
    return [t for t in TOOLS if t["name"] in allowed]


# Fast model for chat, full model for tool execution
MODEL_FAST = "claude-haiku-4-5-20251001"    # Fast: conversation, opinions, discussion
MODEL_TOOL = "claude-sonnet-4-20250514"     # Smart: when tools are needed


async def chat_agent(message: str, agent_key: str, use_tools: bool = True) -> str:
    """Chat with a specific agent. Uses simple message log — never corrupts."""
    session_id = hash(f"agent_{agent_key}") % 100000 + 1000

    if session_id not in _message_logs:
        _message_logs[session_id] = []

    _message_logs[session_id].append({"role": "user", "text": message})

    max_hist = 24 if agent_key == "sarah" else 12
    history = _get_clean_history(session_id, max_hist)

    system_prompt = _agent_system_prompt(agent_key)
    client = anthropic.AsyncAnthropic()

    msg_lower = message.lower()
    # Only use tools for clear action requests — keep the list tight
    action_words = ["create", "make", "generate", "write", "send", "fetch", "search",
                    "update", "delete", "research", "browse", "find", "add", "produce",
                    "assign", "schedule", "run", "execute", "build", "design",
                    "prospect", "report", "propose", "list all", "show all"]
    needs_tools = use_tools and any(w in msg_lower for w in action_words)

    try:
        if needs_tools:
            agent_tools = _get_agent_tools(agent_key)
            max_loops = 8 if agent_key == "sarah" else 6
            max_tok = 1500 if agent_key == "sarah" else 1000

            for _ in range(max_loops):
                response = await client.messages.create(
                    model=MODEL_TOOL,
                    max_tokens=max_tok,
                    system=system_prompt,
                    messages=history,
                    tools=agent_tools,
                )
                if response.stop_reason == "tool_use":
                    history.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            logger.info(f"[{agent_key}] Tool: {block.name}")
                            try:
                                result = await _exec_tool(block.name, block.input)
                            except Exception as e:
                                result = f"Error: {str(e)}"
                            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                    history.append({"role": "user", "content": tool_results})
                else:
                    reply = "".join(b.text for b in response.content if hasattr(b, "text"))
                    _message_logs[session_id].append({"role": "assistant", "text": reply})
                    return reply
        else:
            response = await client.messages.create(
                model=MODEL_FAST,
                max_tokens=600,
                system=system_prompt,
                messages=history,
            )
            reply = "".join(b.text for b in response.content if hasattr(b, "text"))
            _message_logs[session_id].append({"role": "assistant", "text": reply})
            return reply

    except Exception as e:
        logger.error(f"[{agent_key}] Error: {e}")
        err_msg = "Sorry, I had a temporary error. Try again."
        _message_logs[session_id].append({"role": "assistant", "text": err_msg})
        return err_msg

    return "Done."


async def chat_meeting(message: str) -> str:
    """Meeting room — Haiku, no tools, simple message log."""
    session_id = hash("meeting_room") % 100000 + 2000

    if session_id not in _message_logs:
        _message_logs[session_id] = []

    _message_logs[session_id].append({"role": "user", "text": message})
    history = _get_clean_history(session_id, 12)

    try:
        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model=MODEL_FAST,
            max_tokens=800,
            system=_meeting_system_prompt(),
            messages=history,
        )
        reply = "".join(b.text for b in response.content if hasattr(b, "text"))
        _message_logs[session_id].append({"role": "assistant", "text": reply})
        return reply
    except Exception as e:
        logger.error(f"[meeting] Error: {e}")
        return "Meeting interrupted. Try again."


def get_agents_info() -> dict:
    """Return agent profiles for the frontend."""
    return AGENTS


def clear_agent_chat(agent_key: str):
    """Clear an agent's conversation history."""
    session_id = hash(f"agent_{agent_key}") % 100000 + 1000
    clear_conversation(session_id)


def clear_meeting_chat():
    """Clear meeting room history."""
    session_id = hash("meeting_room") % 100000 + 2000
    clear_conversation(session_id)


def clear_main_chat():
    """Clear main brain chat."""
    clear_conversation(0)
