"""Social Media Workflow Engine.

Auto-classifies tasks → creates stage pipeline → executes each stage
with the right agent → auto-handoff between stages → delivers final package.

Workflow: Command → Classify → Research → Strategy → Copywriting → Creative → Publishing
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("amine-agent")

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


# ============================================================
# TASK TYPE DEFINITIONS
# ============================================================

TASK_TYPES = {
    "reels": {
        "label": "Instagram Reels",
        "stages": ["research", "strategy", "copywriting", "voiceover", "music", "audio_mix", "publishing"],
    },
    "carousel": {
        "label": "Carousel Post",
        "stages": ["research", "strategy", "copywriting", "publishing"],
    },
    "static_post": {
        "label": "Static Post",
        "stages": ["strategy", "copywriting", "publishing"],
    },
    "story": {
        "label": "Story Sequence",
        "stages": ["strategy", "copywriting", "voiceover", "music", "video_render", "publishing"],
    },
    "campaign": {
        "label": "Campaign Concept",
        "stages": ["research", "strategy", "copywriting", "voiceover", "music", "audio_mix", "publishing"],
    },
    "content_plan": {
        "label": "Monthly Content Plan",
        "stages": ["research", "strategy", "copywriting"],
    },
    "captions": {
        "label": "Caption Writing",
        "stages": ["strategy", "copywriting"],
    },
    "hashtag_research": {
        "label": "Hashtag Research",
        "stages": ["research"],
    },
    "account_audit": {
        "label": "Account Audit",
        "stages": ["research", "strategy"],
    },
}

# ============================================================
# STAGE DEFINITIONS
# ============================================================

STAGE_DEFS = {
    "research": {
        "name": "Research",
        "agent": "browser",      # Kai
        "icon": "🔍",
        "goal": "Research the topic thoroughly",
        "deliverables": "research_summary, talking_points, angle",
        "prompt_template": """WORK ORDER — DO THIS NOW, DO NOT DELEGATE:

Research this topic: {command}

Use browse_web to find real data. Deliver:

## Research Summary
Key findings (facts, data, stats).

## Key Talking Points
5+ bullet points we can use in content.

## Do/Don't List
DO: safe angles to take. DON'T: things to avoid.

## Recommended Angle
Best positioning for this content.

IMPORTANT: Do the research yourself. Write the findings. Do not delegate.""",
    },

    "strategy": {
        "name": "Content Strategy",
        "agent": "manager",      # Sarah
        "icon": "🧠",
        "goal": "Create content concepts",
        "deliverables": "content_ideas, hooks, audience, cta",
        "prompt_template": """WORK ORDER — DO THIS NOW, DO NOT DELEGATE:

Create {count} content concepts for: {command}

Based on this research: {prev_output}

Deliver:

## Content Ideas
{count} concepts with title, angle, and why it works.

## Hooks
One scroll-stopping first line per concept.

## Target Audience
Who sees this and why they care.

## CTA Direction
What viewers should do after.

IMPORTANT: Write the strategy yourself. Do not create tasks or delegate.""",
    },

    "copywriting": {
        "name": "Copywriting",
        "agent": "content",      # Marcus
        "icon": "✍️",
        "goal": "Write scripts, captions, hashtags",
        "deliverables": "scripts, captions, hashtags",
        "prompt_template": """WORK ORDER — WRITE THIS NOW, DO NOT DELEGATE:

Write the actual content for: {command}

Based on this strategy: {prev_output}

For EACH piece, deliver:

## Piece [1], [2], [3]...
**On-Screen Text:** Short punchy text for the screen.
**Voiceover:** What the narrator says (~2.5 words/sec).
**Caption:** Full posting caption with emojis, line breaks, ready to paste.
**Hashtags:** 20 relevant hashtags.

IMPORTANT: Write ALL the copy yourself right now. Do not delegate or create tasks. Just write the content.""",
    },

    "audio_mix": {
        "name": "Audio Mix",
        "agent": "designer",
        "icon": "🎧",
        "goal": "Mix voiceover + background music into final audio",
        "deliverables": "mixed_audio",
        "prompt_template": "",  # Auto-handled
    },

    "music": {
        "name": "Background Music",
        "agent": "designer",
        "icon": "🎵",
        "goal": "Auto-select background music",
        "deliverables": "music_track",
        "prompt_template": "",  # Not used — auto-handled
    },

    "voiceover": {
        "name": "Voiceover",
        "agent": "designer",     # Zara handles audio
        "icon": "🎙️",
        "goal": "Generate voiceover from the scripts using the best voice for the content",
        "deliverables": "voiceover_audio",
        "prompt_template": """WORK ORDER — GENERATE VOICEOVER NOW:

Task: {command}

Scripts to voice: {prev_output}

Choose the best voice for this content:
- Luxury/serious content → use "Adam" or "onyx"
- Warm/friendly content → use "Jessica" or "nova"
- Professional/corporate → use "Eric" or "Daniel"
- Energetic/social → use "Liam" or "Charlie"

Extract the voiceover/script text from the previous stage and call generate_voiceover with the right voice.
Generate the actual audio file. Do not just describe — USE THE TOOL.""",
    },

    "creative": {
        "name": "Creative & Production",
        "agent": "designer",     # Zara
        "icon": "🎨",
        "goal": "Generate all visual assets — images, thumbnails, visual direction",
        "deliverables": "images, thumbnails, visual_direction, music_recommendation",
        "prompt_template": """WORK ORDER — FULL CREATIVE PRODUCTION:

Task: {command}

Previous work (scripts, voiceover, etc.): {prev_output}

Do ALL of this:

1. Generate a cover/thumbnail image for EACH piece using generate_image
   - Match the mood of the content
   - Use cinematic, high-quality prompts

2. Write visual direction notes:
   - Color palette
   - Typography style
   - Mood/atmosphere

3. Recommend background music style:
   - What genre fits (cinematic, upbeat, ambient, dramatic, etc.)
   - Tempo (slow, medium, fast)
   - Mood keywords for music search

IMPORTANT: Generate the ACTUAL images. Do not just describe them.""",
    },

    "publishing": {
        "name": "Final Delivery",
        "agent": "manager",      # Sarah
        "icon": "📱",
        "goal": "Compile everything into a complete delivery package ready for client",
        "deliverables": "final_package, posting_schedule, asset_list",
        "prompt_template": """WORK ORDER — COMPILE FINAL DELIVERY:

Task: {command}

All team work so far: {prev_output}

Compile the COMPLETE delivery package:

## Final Delivery
For each piece:
- Platform (Instagram/TikTok/YouTube)
- Final caption (cleaned, formatted, ready to paste)
- Hashtags (optimized)
- Media assets list (images generated, voiceover files)

## Publishing Schedule
- Posting order (which piece first and why)
- Best posting times and days
- Platform-specific adaptations

## Production Summary
- What was created
- Assets delivered (images, voiceover, scripts)
- Next steps if any

This is the FINAL delivery to the client. Make it complete and professional.""",
    },
}


# ============================================================
# CLASSIFIER
# ============================================================

def classify_task(command: str) -> tuple[str, int]:
    """Classify a command into a task type and content count.
    Returns (task_type, count).
    """
    cmd = command.lower()

    # Detect count
    count = 1
    for word in cmd.split():
        if word.isdigit():
            count = int(word)
            break

    # Detect type
    if any(w in cmd for w in ["reel", "reels", "short", "shorts"]):
        return "reels", count
    elif any(w in cmd for w in ["carousel", "slide"]):
        return "carousel", count
    elif any(w in cmd for w in ["story", "stories"]):
        return "story", count
    elif any(w in cmd for w in ["campaign", "launch"]):
        return "campaign", count
    elif any(w in cmd for w in ["content plan", "monthly plan", "calendar"]):
        return "content_plan", count
    elif any(w in cmd for w in ["caption", "copy", "write"]):
        return "captions", count
    elif any(w in cmd for w in ["hashtag"]):
        return "hashtag_research", count
    elif any(w in cmd for w in ["audit", "review", "analyze"]):
        return "account_audit", count
    else:
        return "static_post", count


# ============================================================
# WORKFLOW CREATION
# ============================================================

async def create_workflow(command: str, client_id: int = None) -> dict:
    """Create a new workflow from a command.

    1. Classifies the task
    2. Creates workflow record
    3. Creates stage records with dependencies
    4. Returns workflow info
    """
    from app.database import get_db

    task_type, count = classify_task(command)
    type_info = TASK_TYPES.get(task_type, TASK_TYPES["static_post"])
    stages = type_info["stages"]

    title = f"{type_info['label']}: {command[:80]}"

    db = await get_db()

    # Create workflow
    cursor = await db.execute(
        "INSERT INTO workflows (title, task_type, status, client_id, original_command) VALUES (?,?,?,?,?)",
        (title, task_type, "in_research" if "research" in stages else "in_strategy", client_id, command),
    )
    wf_id = cursor.lastrowid

    # Create stages with dependencies
    prev_stage_id = None
    for i, stage_key in enumerate(stages):
        sdef = STAGE_DEFS[stage_key]
        status = "in_progress" if i == 0 else "waiting"
        cursor = await db.execute(
            "INSERT INTO workflow_stages (workflow_id, stage_number, stage_name, agent_role, status, depends_on) "
            "VALUES (?,?,?,?,?,?)",
            (wf_id, i + 1, stage_key, sdef["agent"], status, prev_stage_id),
        )
        prev_stage_id = cursor.lastrowid

    await db.commit()
    await db.close()

    logger.info(f"[workflow] Created workflow {wf_id}: {title} ({len(stages)} stages)")

    return {
        "workflow_id": wf_id,
        "title": title,
        "task_type": task_type,
        "count": count,
        "stages": stages,
    }


# ============================================================
# STAGE EXECUTOR
# ============================================================

async def execute_stage(workflow_id: int, stage_id: int) -> str:
    """Execute a single workflow stage using the assigned agent.

    1. Builds prompt from template + previous stage output
    2. Calls the agent
    3. Saves deliverables
    4. Marks stage complete
    5. Auto-starts next stage
    """
    from app.database import get_db
    from agents.brain import chat_agent

    db = await get_db()

    # Get stage info
    stage_rows = await db.execute_fetchall(
        "SELECT * FROM workflow_stages WHERE id=?", (stage_id,)
    )
    if not stage_rows:
        await db.close()
        return "Stage not found"
    stage = dict(stage_rows[0])

    # Get workflow info
    wf_rows = await db.execute_fetchall(
        "SELECT * FROM workflows WHERE id=?", (workflow_id,)
    )
    wf = dict(wf_rows[0])

    # Get previous stage output (if dependency exists)
    prev_output = ""
    if stage["depends_on"]:
        prev_rows = await db.execute_fetchall(
            "SELECT output_data FROM workflow_stages WHERE id=?", (stage["depends_on"],)
        )
        if prev_rows:
            prev_output = prev_rows[0]["output_data"] or ""

    # Mark stage as in_progress
    await db.execute(
        "UPDATE workflow_stages SET status='in_progress', started_at=CURRENT_TIMESTAMP WHERE id=?",
        (stage_id,)
    )

    # Update workflow status
    status_map = {
        "research": "in_research", "strategy": "in_strategy",
        "copywriting": "in_copywriting", "creative": "in_creative",
        "publishing": "in_publishing",
    }
    await db.execute(
        "UPDATE workflows SET status=? WHERE id=?",
        (status_map.get(stage["stage_name"], "in_progress"), workflow_id),
    )
    await db.commit()
    await db.close()

    # Build prompt
    sdef = STAGE_DEFS.get(stage["stage_name"])
    if not sdef:
        return "Unknown stage type"

    # Count from task type classification
    _, count = classify_task(wf["original_command"])

    prompt = sdef["prompt_template"].format(
        command=wf["original_command"],
        task_type=wf["task_type"],
        prev_output=prev_output[:3000] if prev_output else "No previous output.",
        count=count,
    )

    # Map agent role to agent key
    role_to_key = {
        "browser": "kai", "manager": "sarah", "content": "marcus",
        "designer": "zara", "email": "elena", "analytics": "alex",
    }
    agent_key = role_to_key.get(stage["agent_role"], "sarah")

    logger.info(f"[workflow] Stage {stage['stage_number']} ({stage['stage_name']}) → {agent_key}")

    # Audio mix stage: combine voiceover + background music with FFmpeg
    if stage["stage_name"] == "audio_mix":
        try:
            import subprocess

            # Get voiceover and music paths from previous stages
            db = await get_db()
            all_stages = await db.execute_fetchall(
                "SELECT stage_name, output_data FROM workflow_stages WHERE workflow_id=? AND status='completed'",
                (workflow_id,))
            await db.close()

            outputs = {dict(s)["stage_name"]: dict(s)["output_data"] or "" for s in all_stages}
            vo_web = outputs.get("voiceover", "")
            music_web = outputs.get("music", "")

            # Convert web paths to filesystem paths
            vo_file = UPLOADS_DIR / vo_web.replace("/uploads/", "") if vo_web.startswith("/uploads/") else None
            music_file = UPLOADS_DIR / music_web.replace("/uploads/", "") if music_web.startswith("/uploads/") else None

            if vo_file and vo_file.exists() and music_file and music_file.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_name = f"mix_{ts}.mp3"
                out_path = UPLOADS_DIR / out_name

                # FFmpeg: mix voiceover (full volume) + music (low volume, trimmed to voiceover length)
                cmd = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(vo_file),           # Input 0: voiceover
                    "-i", str(music_file),         # Input 1: music
                    "-filter_complex",
                    "[1:a]volume=0.15[music];"     # Music at 15% volume
                    "[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
                    "-map", "[out]",
                    "-ac", "2", "-ar", "44100",
                    str(out_path),
                ]

                proc = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True, timeout=30
                )

                if proc.returncode == 0 and out_path.exists():
                    result = f"/uploads/{out_name}"
                    logger.info(f"[workflow] Audio mixed: {out_name}")
                else:
                    logger.warning(f"[workflow] FFmpeg mix error: {proc.stderr[:200]}")
                    result = vo_web  # Fallback: just use voiceover
            elif vo_file and vo_file.exists():
                result = vo_web  # No music, just use voiceover
            else:
                result = "No audio files to mix"

        except Exception as e:
            result = f"Audio mix error: {str(e)}"
            logger.error(f"[workflow] Audio mix error: {e}")

        # Save and advance
        db = await get_db()
        await db.execute(
            "UPDATE workflow_stages SET status='completed', output_data=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
            (result, stage_id))
        await db.commit()
        await db.close()

        try:
            from agents.brain import _push_ui_refresh
            await _push_ui_refresh()
        except Exception:
            pass

        await _advance_workflow(workflow_id)
        return result

    # Music stage: auto-pick instantly, no agent call
    if stage["stage_name"] == "music":
        cmd_lower = wf["original_command"].lower()
        if any(w in cmd_lower for w in ["luxury", "elegant", "premium", "exclusive"]):
            music_file = "luxury-elegant.mp3"
        elif any(w in cmd_lower for w in ["dramatic", "war", "conflict", "impact", "serious"]):
            music_file = "dramatic-cinematic.mp3"
        elif any(w in cmd_lower for w in ["fun", "party", "energetic", "dance"]):
            music_file = "energetic-fun.mp3"
        elif any(w in cmd_lower for w in ["inspiring", "motivat", "success", "growth"]):
            music_file = "inspiring-motivational.mp3"
        elif any(w in cmd_lower for w in ["happy", "lifestyle", "travel", "food"]):
            music_file = "happy-lifestyle.mp3"
        elif any(w in cmd_lower for w in ["dark", "mystery", "risk"]):
            music_file = "dark-serious.mp3"
        else:
            music_file = "upbeat-corporate.mp3"

        music_path = UPLOADS_DIR / "music" / music_file
        result = f"/uploads/music/{music_file}" if music_path.exists() else "No music available"
        logger.info(f"[workflow] Auto-selected music: {music_file}")

        # Save and advance immediately
        db = await get_db()
        await db.execute(
            "UPDATE workflow_stages SET status='completed', output_data=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
            (result, stage_id))
        await db.commit()
        await db.close()

        try:
            from agents.brain import _push_ui_refresh
            await _push_ui_refresh()
        except Exception:
            pass

        await _advance_workflow(workflow_id)
        return result

    # Voiceover stage: auto-generate audio directly (faster than asking agent)
    if stage["stage_name"] == "voiceover" and prev_output:
        try:
            import re
            # Extract voiceover/script text
            vo_parts = re.findall(r'(?:Voiceover|voiceover|Voice.?over|Script)[:\s]*(.+?)(?:\n\n|\n##|\n\*\*|$)', prev_output, re.DOTALL)
            vo_text = " ".join(p.strip() for p in vo_parts)[:800] if vo_parts else prev_output[:500]

            # Auto-pick voice based on content mood
            cmd_lower = wf["original_command"].lower()
            if any(w in cmd_lower for w in ["luxury", "elegant", "premium", "investor"]):
                voice = "Adam"
            elif any(w in cmd_lower for w in ["fun", "energetic", "social", "youth"]):
                voice = "Liam"
            elif any(w in cmd_lower for w in ["professional", "corporate", "business"]):
                voice = "Eric"
            elif any(w in cmd_lower for w in ["warm", "friendly", "lifestyle"]):
                voice = "Jessica"
            else:
                voice = "Adam"

            from agents.video import generate_voiceover
            path = await asyncio.wait_for(generate_voiceover(vo_text, voice=voice), timeout=60)
            from pathlib import Path as P
            web_path = f"/uploads/{P(path).name}"
            result = web_path
            logger.info(f"[workflow] Voiceover auto-generated: {web_path} (voice: {voice})")
        except Exception as e:
            result = f"Voiceover error: {str(e)}"
            logger.error(f"[workflow] Voiceover error: {e}")
    else:
        # Normal stage: run agent
        timeout = 180 if stage["stage_name"] == "creative" else 120

        try:
            result = await asyncio.wait_for(
                chat_agent(prompt, agent_key, use_tools=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            result = f"Stage timed out after {timeout}s. The work may be partially done."
            logger.warning(f"[workflow] Stage {stage['stage_number']} timed out")
        except Exception as e:
            result = f"Stage error: {str(e)}"
            logger.error(f"[workflow] Stage {stage['stage_number']} error: {e}")

    # Save output and mark complete
    db = await get_db()
    await db.execute(
        "UPDATE workflow_stages SET status='completed', output_data=?, deliverables=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (result, sdef["deliverables"], stage_id),
    )
    await db.commit()
    await db.close()

    logger.info(f"[workflow] Stage {stage['stage_number']} completed ({len(result)} chars)")

    # Push UI refresh so user sees the update live
    try:
        from agents.brain import _push_ui_refresh
        await _push_ui_refresh()
    except Exception:
        pass

    # Auto-start next stage
    await _advance_workflow(workflow_id)

    return result


async def _advance_workflow(workflow_id: int):
    """Check if next stage can start and auto-start it."""
    from app.database import get_db

    db = await get_db()
    stages = await db.execute_fetchall(
        "SELECT * FROM workflow_stages WHERE workflow_id=? ORDER BY stage_number",
        (workflow_id,)
    )
    stages = [dict(s) for s in stages]
    await db.close()

    all_done = True
    for stage in stages:
        if stage["status"] == "waiting":
            all_done = False
            # Check if dependency is met
            if stage["depends_on"]:
                dep = next((s for s in stages if s["id"] == stage["depends_on"]), None)
                if dep and dep["status"] == "completed":
                    # Dependency met — auto-start this stage!
                    logger.info(f"[workflow] Auto-starting stage {stage['stage_number']} ({stage['stage_name']})")
                    asyncio.create_task(execute_stage(workflow_id, stage["id"]))
                    return
            else:
                # No dependency — start immediately
                asyncio.create_task(execute_stage(workflow_id, stage["id"]))
                return
        elif stage["status"] == "in_progress":
            all_done = False

    if all_done:
        # All stages done — workflow complete!
        db = await get_db()
        await db.execute(
            "UPDATE workflows SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?",
            (workflow_id,)
        )
        await db.commit()
        await db.close()

        logger.info(f"[workflow] Workflow {workflow_id} COMPLETE ✅")

        # Get workflow title for notification
        db2 = await get_db()
        wf_rows = await db2.execute_fetchall("SELECT title FROM workflows WHERE id=?", (workflow_id,))
        await db2.close()
        title = dict(wf_rows[0])["title"] if wf_rows else "Workflow"

        # Sync to Google Drive + Sheets
        try:
            from agents.google_sync import sync_completed_workflow
            asyncio.create_task(sync_completed_workflow(workflow_id))
            logger.info(f"[workflow] Google sync triggered for workflow {workflow_id}")
        except Exception as e:
            logger.warning(f"[workflow] Google sync error: {e}")

        # Send notification
        from agents.notify import notify
        await notify(
            "Content Delivered ✅",
            f"{title}\nAll stages completed. Assets uploading to Google Drive.",
            "high", "white_check_mark"
        )

        # Push UI refresh
        try:
            from agents.brain import _push_ui_refresh
            await _push_ui_refresh()
        except Exception:
            pass


# ============================================================
# RUN WORKFLOW (main entry point)
# ============================================================

async def run_workflow(command: str, client_id: int = None) -> dict:
    """Create and immediately start executing a workflow.

    This is the main entry point. Call this with the user's command.
    """
    # Create workflow and stages
    wf_info = await create_workflow(command, client_id)

    # Get the first stage and start it
    from app.database import get_db
    db = await get_db()
    first_stage = await db.execute_fetchall(
        "SELECT id FROM workflow_stages WHERE workflow_id=? AND stage_number=1",
        (wf_info["workflow_id"],)
    )
    await db.close()

    if first_stage:
        # Start first stage in background — don't wait for it
        asyncio.create_task(execute_stage(wf_info["workflow_id"], first_stage[0]["id"]))

    return wf_info


async def _auto_add_music(workflow_id: int, command: str):
    """Auto-pick and add background music based on content mood."""
    try:
        cmd_lower = command.lower()
        if any(w in cmd_lower for w in ["luxury", "elegant", "premium", "exclusive"]):
            music_file = "luxury-elegant.mp3"
        elif any(w in cmd_lower for w in ["dramatic", "war", "conflict", "impact", "serious"]):
            music_file = "dramatic-cinematic.mp3"
        elif any(w in cmd_lower for w in ["fun", "party", "energetic", "dance"]):
            music_file = "energetic-fun.mp3"
        elif any(w in cmd_lower for w in ["inspiring", "motivat", "success", "growth"]):
            music_file = "inspiring-motivational.mp3"
        elif any(w in cmd_lower for w in ["happy", "lifestyle", "travel", "food"]):
            music_file = "happy-lifestyle.mp3"
        elif any(w in cmd_lower for w in ["dark", "mystery", "risk"]):
            music_file = "dark-serious.mp3"
        else:
            music_file = "upbeat-corporate.mp3"

        music_path = UPLOADS_DIR / "music" / music_file
        if not music_path.exists():
            logger.warning(f"[workflow] Music file not found: {music_file}")
            return

        from app.database import get_db
        db = await get_db()
        existing = await db.execute_fetchall(
            "SELECT id FROM workflow_stages WHERE workflow_id=? AND stage_name='music'", (workflow_id,))
        if not existing:
            max_row = await db.execute_fetchall(
                "SELECT MAX(stage_number) as mx FROM workflow_stages WHERE workflow_id=?", (workflow_id,))
            max_num = max_row[0]["mx"] or 0
            await db.execute(
                "INSERT INTO workflow_stages (workflow_id, stage_number, stage_name, agent_role, "
                "status, output_data, completed_at) VALUES (?,?,?,?,'completed',?,CURRENT_TIMESTAMP)",
                (workflow_id, max_num + 1, "music", "designer", f"/uploads/music/{music_file}"),
            )
            await db.commit()
            logger.info(f"[workflow] Auto-added music: {music_file}")
        await db.close()
    except Exception as e:
        logger.warning(f"[workflow] Auto-music error: {e}")


# ============================================================
# REVISIONS
# ============================================================

async def revise_stage(workflow_id: int, stage_id: int, feedback: str) -> str:
    """Re-run a stage with revision feedback. Previous output is kept as context."""
    from app.database import get_db
    from agents.brain import chat_agent

    db = await get_db()
    stage_rows = await db.execute_fetchall("SELECT * FROM workflow_stages WHERE id=?", (stage_id,))
    wf_rows = await db.execute_fetchall("SELECT * FROM workflows WHERE id=?", (workflow_id,))

    if not stage_rows or not wf_rows:
        await db.close()
        return "Not found"

    stage = dict(stage_rows[0])
    wf = dict(wf_rows[0])
    prev_output = stage.get("output_data", "")

    # Mark as in_progress
    await db.execute("UPDATE workflow_stages SET status='in_progress', started_at=CURRENT_TIMESTAMP WHERE id=?", (stage_id,))
    await db.execute("UPDATE workflows SET status=? WHERE id=?", (f"revising_{stage['stage_name']}", workflow_id))
    await db.commit()
    await db.close()

    # Push UI refresh
    try:
        from agents.brain import _push_ui_refresh
        await _push_ui_refresh()
    except Exception:
        pass

    sdef = STAGE_DEFS.get(stage["stage_name"])
    role_to_key = {"browser": "kai", "manager": "sarah", "content": "marcus", "designer": "zara", "email": "elena", "analytics": "alex"}
    agent_key = role_to_key.get(stage["agent_role"], "sarah")

    prompt = f"""REVISION REQUEST — REDO THIS WORK:

Original task: {wf['original_command']}

Your previous output:
{prev_output[:2000]}

CLIENT FEEDBACK — CHANGES REQUESTED:
{feedback}

Rewrite your deliverable incorporating this feedback. Keep what was good, fix what was asked. Deliver the FULL revised version."""

    logger.info(f"[workflow] Revising stage {stage['stage_number']} ({stage['stage_name']}) with feedback")

    try:
        result = await asyncio.wait_for(chat_agent(prompt, agent_key, use_tools=True), timeout=120)
    except Exception as e:
        result = f"Revision error: {str(e)}"

    db = await get_db()
    await db.execute(
        "UPDATE workflow_stages SET status='completed', output_data=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (result, stage_id)
    )
    await db.execute("UPDATE workflows SET status='completed' WHERE id=?", (workflow_id,))
    await db.commit()
    await db.close()

    logger.info(f"[workflow] Stage {stage['stage_number']} revised ({len(result)} chars)")

    try:
        from agents.brain import _push_ui_refresh
        await _push_ui_refresh()
    except Exception:
        pass

    from agents.notify import notify
    await notify("Revision Done ✏️", f"Stage {stage['stage_number']} ({stage['stage_name']}) has been revised.", "default", "pencil2")

    return result


# ============================================================
# QUERY FUNCTIONS
# ============================================================

async def get_workflow(workflow_id: int) -> dict:
    """Get workflow with all stages and deliverables."""
    from app.database import get_db
    db = await get_db()

    wf_rows = await db.execute_fetchall("SELECT * FROM workflows WHERE id=?", (workflow_id,))
    if not wf_rows:
        await db.close()
        return {}
    wf = dict(wf_rows[0])

    stage_rows = await db.execute_fetchall(
        "SELECT * FROM workflow_stages WHERE workflow_id=? ORDER BY stage_number",
        (workflow_id,)
    )
    wf["stages"] = [dict(s) for s in stage_rows]

    await db.close()
    return wf


async def list_workflows(status: str = None, limit: int = 20) -> list:
    """List all workflows."""
    from app.database import get_db
    db = await get_db()

    if status:
        rows = await db.execute_fetchall(
            "SELECT w.*, COUNT(ws.id) as stage_count, "
            "SUM(CASE WHEN ws.status='completed' THEN 1 ELSE 0 END) as stages_done "
            "FROM workflows w LEFT JOIN workflow_stages ws ON ws.workflow_id=w.id "
            "WHERE w.status=? GROUP BY w.id ORDER BY w.created_at DESC LIMIT ?",
            (status, limit)
        )
    else:
        rows = await db.execute_fetchall(
            "SELECT w.*, COUNT(ws.id) as stage_count, "
            "SUM(CASE WHEN ws.status='completed' THEN 1 ELSE 0 END) as stages_done "
            "FROM workflows w LEFT JOIN workflow_stages ws ON ws.workflow_id=w.id "
            "GROUP BY w.id ORDER BY w.created_at DESC LIMIT ?",
            (limit,)
        )

    await db.close()
    return [dict(r) for r in rows]
