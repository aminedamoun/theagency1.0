"""REST API routes for the platform."""

import os
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
import shutil
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.database import get_db

router = APIRouter(prefix="/api")

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
TEMP_DIR = UPLOADS_DIR / "_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Video Editing API  (FFmpeg-based)
# ---------------------------------------------------------------------------

def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _find_file(filename: str) -> Path | None:
    """Find a file in uploads/ or uploads/_temp/."""
    p = UPLOADS_DIR / filename
    if p.exists():
        return p
    p = TEMP_DIR / filename
    if p.exists():
        return p
    return None


def _safe_fps(val):
    """Parse frame rate string like '30/1' or '29.97' without eval."""
    try:
        s = str(val)
        if "/" in s:
            num, den = s.split("/", 1)
            return round(float(num) / float(den), 2)
        return round(float(s), 2)
    except Exception:
        return 30


def _run_ffmpeg(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """Run ffmpeg with common flags.  Raises on failure."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _probe(filepath: str) -> dict:
    """Return ffprobe JSON for a media file."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", filepath,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout) if r.returncode == 0 else {}


class TrimReq(BaseModel):
    filename: str
    start: float       # seconds
    end: float         # seconds


class SplitReq(BaseModel):
    filename: str
    at: float          # split point in seconds


class ConcatReq(BaseModel):
    files: list[str]   # ordered list of filenames in /uploads/


class ProbeReq(BaseModel):
    filename: str


@router.post("/video/probe")
async def video_probe(req: ProbeReq):
    """Get duration / resolution / codec info for a media file."""
    fpath = _find_file(req.filename)
    if not fpath:
        return {"error": "File not found"}
    info = await asyncio.to_thread(_probe, str(fpath))
    duration = float(info.get("format", {}).get("duration", 0))
    streams = info.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_type") == "video"), None)
    astream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {
        "duration": duration,
        "width": int(vstream["width"]) if vstream else 0,
        "height": int(vstream["height"]) if vstream else 0,
        "has_audio": astream is not None,
        "codec": vstream.get("codec_name", "") if vstream else "",
        "fps": _safe_fps(vstream.get("r_frame_rate", "30")) if vstream else 30,
    }


@router.post("/video/trim")
async def video_trim(req: TrimReq):
    """Trim a video between start and end seconds.  Returns new temp filename."""
    src = _find_file(req.filename)
    if not src:
        return {"error": "Source not found"}
    safe = "".join(c if c.isalnum() or c in "_-." else "_" for c in req.filename)[:80]
    out_name = f"{_ts()}_trim_{safe}"
    out = TEMP_DIR / out_name
    args = ["-i", str(src), "-ss", str(req.start), "-to", str(req.end),
            "-c", "copy", "-avoid_negative_ts", "make_zero", str(out)]
    r = await asyncio.to_thread(_run_ffmpeg, args)
    if r.returncode != 0:
        args = ["-i", str(src), "-ss", str(req.start), "-to", str(req.end),
                "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", str(out)]
        r = await asyncio.to_thread(_run_ffmpeg, args)
    if r.returncode != 0:
        return {"error": r.stderr or "FFmpeg trim failed"}
    return {"filename": out_name, "path": f"/uploads/_temp/{out_name}"}


@router.post("/video/split")
async def video_split(req: SplitReq):
    """Split a video at the given second.  Returns two temp filenames."""
    src = _find_file(req.filename)
    if not src:
        return {"error": f"Source not found: {req.filename}"}
    info = await asyncio.to_thread(_probe, str(src))
    duration = float(info.get("format", {}).get("duration", 0))
    if duration == 0:
        return {"error": "Cannot determine video duration"}
    if req.at <= 0.05 or req.at >= duration - 0.05:
        return {"error": f"Split point {req.at:.2f}s out of range (duration {duration:.2f}s)"}

    ts = _ts()
    # Sanitize base name: remove spaces and special chars to avoid URL issues
    base = req.filename.rsplit(".", 1)[0]
    safe_base = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)[:60]
    name_a = f"{ts}_splitA_{safe_base}.mp4"
    name_b = f"{ts}_splitB_{safe_base}.mp4"
    path_a = str(TEMP_DIR / name_a)
    path_b = str(TEMP_DIR / name_b)

    # Try stream copy first (fast), fall back to re-encode
    for mode in ["copy", "reencode"]:
        if mode == "copy":
            args_a = ["-i", str(src), "-ss", "0", "-to", str(req.at),
                      "-c", "copy", "-avoid_negative_ts", "make_zero", path_a]
            args_b = ["-i", str(src), "-ss", str(req.at),
                      "-c", "copy", "-avoid_negative_ts", "make_zero", path_b]
        else:
            args_a = ["-i", str(src), "-ss", "0", "-to", str(req.at),
                      "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", path_a]
            args_b = ["-i", str(src), "-ss", str(req.at),
                      "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", path_b]

        r1 = await asyncio.to_thread(_run_ffmpeg, args_a)
        r2 = await asyncio.to_thread(_run_ffmpeg, args_b)

        # Check both files exist and are non-empty
        pa = Path(path_a)
        pb = Path(path_b)
        if r1.returncode == 0 and r2.returncode == 0 and pa.exists() and pb.exists() and pa.stat().st_size > 100 and pb.stat().st_size > 100:
            return {"parts": [
                {"filename": name_a, "path": f"/uploads/_temp/{name_a}"},
                {"filename": name_b, "path": f"/uploads/_temp/{name_b}"},
            ]}

        # Clean up failed attempts
        pa.unlink(missing_ok=True)
        pb.unlink(missing_ok=True)

    return {"error": f"Split failed (ffmpeg). Part A: {r1.stderr[:200] if r1 else 'n/a'}, Part B: {r2.stderr[:200] if r2 else 'n/a'}"}


@router.post("/video/concat")
async def video_concat(req: ConcatReq):
    """Concatenate multiple videos/images → single mp4 in uploads/ (final export)."""
    if len(req.files) < 2:
        return {"error": "Need at least 2 files"}

    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    all_images = all(Path(f).suffix.lower() in image_exts for f in req.files)

    out_name = f"{_ts()}_export.mp4"
    out = UPLOADS_DIR / out_name  # Final export goes to real uploads/

    if all_images:
        inputs = []
        filters = []
        for i, f in enumerate(req.files):
            fpath = _find_file(f)
            if not fpath:
                return {"error": f"File not found: {f}"}
            inputs += ["-loop", "1", "-t", "5", "-i", str(fpath)]
            filters.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")
        filter_concat = "".join(f"[v{i}]" for i in range(len(req.files))) + f"concat=n={len(req.files)}:v=1:a=0[out]"
        filter_str = ";".join(filters) + ";" + filter_concat
        args = inputs + ["-filter_complex", filter_str, "-map", "[out]",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", str(out)]
    else:
        list_file = TEMP_DIR / f"{_ts()}_concat.txt"
        lines = []
        for f in req.files:
            fpath = _find_file(f)
            if not fpath:
                return {"error": f"File not found: {f}"}
            lines.append(f"file '{fpath}'")
        list_file.write_text("\n".join(lines))
        args = ["-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c", "copy", str(out)]
        r = await asyncio.to_thread(_run_ffmpeg, args)
        if r.returncode != 0:
            args = ["-f", "concat", "-safe", "0", "-i", str(list_file),
                    "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", str(out)]
            r = await asyncio.to_thread(_run_ffmpeg, args)
        list_file.unlink(missing_ok=True)
        if r.returncode != 0:
            return {"error": r.stderr or "Concat failed"}
        return {"filename": out_name, "path": f"/uploads/{out_name}"}

    r = await asyncio.to_thread(_run_ffmpeg, args, 300)
    if r.returncode != 0:
        return {"error": r.stderr or "Concat failed"}
    return {"filename": out_name, "path": f"/uploads/{out_name}"}


class ResizeReq(BaseModel):
    filename: str
    width: int
    height: int


@router.post("/video/resize")
async def video_resize(req: ResizeReq):
    """Resize/reformat video to given dimensions (e.g. 1080x1920 for Reel)."""
    src = _find_file(req.filename)
    if not src:
        return {"error": "Source not found"}
    safe = "".join(c if c.isalnum() or c in "_-." else "_" for c in req.filename)[:80]
    out_name = f"{_ts()}_export_{safe}"
    out = UPLOADS_DIR / out_name  # Export goes to real uploads/
    args = [
        "-i", str(src),
        "-vf", f"scale={req.width}:{req.height}:force_original_aspect_ratio=decrease,"
               f"pad={req.width}:{req.height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", str(out),
    ]
    r = await asyncio.to_thread(_run_ffmpeg, args)
    if r.returncode != 0:
        return {"error": r.stderr or "Resize failed"}
    return {"filename": out_name, "path": f"/uploads/{out_name}"}


@router.post("/video/thumbnail")
async def video_thumbnail(req: ProbeReq):
    """Extract a thumbnail from a video at 1 second."""
    src = _find_file(req.filename)
    if not src:
        return {"error": "Source not found"}
    safe_base = "".join(c if c.isalnum() or c in "_-" else "_" for c in req.filename.rsplit('.', 1)[0])[:80]
    out_name = f"thumb_{safe_base}.jpg"
    out = TEMP_DIR / out_name
    if out.exists():
        return {"filename": out_name, "path": f"/uploads/_temp/{out_name}"}
    args = ["-i", str(src), "-ss", "1", "-vframes", "1", "-q:v", "5", str(out)]
    r = await asyncio.to_thread(_run_ffmpeg, args)
    if r.returncode != 0:
        args = ["-i", str(src), "-ss", "0", "-vframes", "1", "-q:v", "5", str(out)]
        await asyncio.to_thread(_run_ffmpeg, args)
    return {"filename": out_name, "path": f"/uploads/_temp/{out_name}"}


@router.delete("/video/temp")
async def clear_temp():
    """Delete all temporary editing files."""
    count = 0
    if TEMP_DIR.exists():
        for f in TEMP_DIR.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
    return {"deleted": count}


# --- Report Generation ---

class ReportReq(BaseModel):
    title: str = "Agency Report"
    include_clients: bool = True
    include_tasks: bool = True
    include_content: bool = True
    include_activity: bool = True
    custom_sections: list = []


@router.post("/report")
async def generate_report(req: ReportReq):
    """Generate a PDF report and return its path."""
    from agents.reports import generate_full_report
    path = await generate_full_report(
        title=req.title,
        include_clients=req.include_clients,
        include_tasks=req.include_tasks,
        include_content=req.include_content,
        include_activity=req.include_activity,
        custom_sections=req.custom_sections,
    )
    return {"path": path, "filename": path.split("/")[-1]}


# --- Text-to-Speech ---

class TTSReq(BaseModel):
    text: str
    voice: str = "nova"
    use_elevenlabs: bool = True


@router.post("/tts")
async def text_to_speech(req: TTSReq):
    """Generate speech audio. Uses ElevenLabs if available, OpenAI TTS fallback."""
    from fastapi.responses import Response
    from agents.video import generate_voiceover
    import os

    text = req.text[:500]
    if not text.strip():
        return {"error": "No text"}

    # If ElevenLabs key exists and requested, use it
    el_key = os.getenv("ELEVENLABS_API_KEY", "")
    if el_key and req.use_elevenlabs:
        try:
            from agents.video import _generate_elevenlabs
            audio = await _generate_elevenlabs(text, req.voice, el_key)
            return Response(content=audio, media_type="audio/mpeg")
        except Exception:
            pass

    # Fallback: OpenAI TTS
    import openai as oa
    openai_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
    voice = req.voice if req.voice in openai_voices else "nova"
    client = oa.AsyncOpenAI()
    response = await client.audio.speech.create(model="tts-1", voice=voice, input=text, speed=1.05)
    return Response(content=response.content, media_type="audio/mpeg")


@router.get("/voices")
async def list_voices():
    """List all available voices (ElevenLabs + OpenAI)."""
    from agents.video import list_elevenlabs_voices

    voices = {
        "openai": [
            {"id": "onyx", "name": "Onyx (Deep Male)"},
            {"id": "nova", "name": "Nova (Warm Female)"},
            {"id": "alloy", "name": "Alloy (Neutral)"},
            {"id": "echo", "name": "Echo (Male)"},
            {"id": "fable", "name": "Fable (British)"},
            {"id": "shimmer", "name": "Shimmer (Soft Female)"},
        ],
        "elevenlabs": await list_elevenlabs_voices(),
    }
    return voices


# --- Research Projects & Leads ---

class ProjectIn(BaseModel):
    name: str
    description: str = ""
    client_id: int | None = None


class LeadIn(BaseModel):
    project_id: int | None = None
    company_name: str
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    industry: str = ""
    location: str = ""
    company_size: str = ""
    source: str = ""
    notes: str = ""
    tags: str = ""


@router.get("/projects")
async def list_projects():
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT p.*, COUNT(l.id) as lead_count, "
        "SUM(CASE WHEN l.email != '' THEN 1 ELSE 0 END) as email_count "
        "FROM research_projects p LEFT JOIN leads l ON l.project_id = p.id "
        "GROUP BY p.id ORDER BY p.created_at DESC"
    )
    await db.close()
    return [dict(r) for r in rows]


@router.post("/projects")
async def create_project(proj: ProjectIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO research_projects (name, description, client_id) VALUES (?, ?, ?)",
        (proj.name, proj.description, proj.client_id),
    )
    await db.commit()
    pid = cursor.lastrowid
    await db.close()
    return {"id": pid, "status": "created"}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    db = await get_db()
    await db.execute("DELETE FROM leads WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM research_projects WHERE id = ?", (project_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


@router.get("/projects/{project_id}/leads")
async def get_project_leads(project_id: int):
    db = await get_db()
    proj_rows = await db.execute_fetchall("SELECT * FROM research_projects WHERE id=?", (project_id,))
    lead_rows = await db.execute_fetchall(
        "SELECT * FROM leads WHERE project_id=? ORDER BY created_at DESC", (project_id,)
    )
    await db.close()
    return {
        "project": dict(proj_rows[0]) if proj_rows else {},
        "leads": [dict(r) for r in lead_rows],
    }


@router.post("/leads")
async def create_lead(lead: LeadIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO leads (project_id, company_name, contact_name, email, phone, website, "
        "industry, location, company_size, source, notes, status, tags, found_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, 'agent')",
        (lead.project_id, lead.company_name, lead.contact_name, lead.email, lead.phone,
         lead.website, lead.industry, lead.location, lead.company_size, lead.source,
         lead.notes, lead.tags),
    )
    await db.commit()
    lead_id = cursor.lastrowid
    await db.close()
    return {"id": lead_id, "status": "created"}


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int):
    db = await get_db()
    await db.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


@router.get("/leads/export/csv")
async def export_leads_csv(project_id: int = None):
    from fastapi.responses import Response
    db = await get_db()
    if project_id:
        rows = await db.execute_fetchall("SELECT * FROM leads WHERE project_id=? ORDER BY created_at DESC", (project_id,))
    else:
        rows = await db.execute_fetchall("SELECT * FROM leads ORDER BY created_at DESC")
    await db.close()
    leads = [dict(r) for r in rows]
    if not leads:
        return Response(content="No leads", media_type="text/plain")
    headers = ["company_name", "contact_name", "email", "phone", "website", "industry", "location", "company_size", "source", "notes", "tags"]
    lines = [",".join(headers)]
    for l in leads:
        lines.append(",".join(f'"{l.get(h, "")}"' for h in headers))
    return Response(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


# --- Social Media Workflows ---

class WorkflowReq(BaseModel):
    command: str
    client_id: int | None = None


@router.post("/workflows")
async def create_workflow_endpoint(req: WorkflowReq):
    from agents.workflow import run_workflow
    result = await run_workflow(req.command, req.client_id)
    return result


@router.get("/workflows")
async def list_workflows_endpoint(status: str = None):
    from agents.workflow import list_workflows
    return await list_workflows(status)


@router.get("/workflows/{workflow_id}")
async def get_workflow_endpoint(workflow_id: int):
    from agents.workflow import get_workflow
    return await get_workflow(workflow_id)


@router.post("/workflows/{workflow_id}/approve")
async def approve_workflow(workflow_id: int):
    db = await get_db()
    await db.execute("UPDATE workflows SET status='ready_to_publish' WHERE id=?", (workflow_id,))
    await db.commit()
    await db.close()
    return {"status": "approved"}


@router.post("/workflows/{workflow_id}/stages/{stage_id}/run")
async def run_stage_manually(workflow_id: int, stage_id: int):
    """Manually trigger a workflow stage to run."""
    from agents.workflow import execute_stage
    import asyncio
    db = await get_db()
    stage = await db.execute_fetchall("SELECT status FROM workflow_stages WHERE id=? AND workflow_id=?", (stage_id, workflow_id))
    await db.close()
    if not stage:
        return {"error": "Stage not found"}
    asyncio.create_task(execute_stage(workflow_id, stage_id))
    return {"status": "started"}


class RevisionReq(BaseModel):
    feedback: str


@router.post("/workflows/{workflow_id}/stages/{stage_id}/revise")
async def revise_stage(workflow_id: int, stage_id: int, req: RevisionReq):
    """Re-run a stage with revision feedback. Keeps previous output as context."""
    from agents.workflow import revise_stage
    import asyncio
    asyncio.create_task(revise_stage(workflow_id, stage_id, req.feedback))
    return {"status": "revising"}


class VoiceoverReq(BaseModel):
    voice: str = "Adam"
    stage_id: int | None = None


@router.post("/workflows/{workflow_id}/voiceover")
async def generate_workflow_voiceover(workflow_id: int, req: VoiceoverReq):
    """Generate voiceover from the copywriting stage output."""
    from agents.video import generate_voiceover
    db = await get_db()
    # Find copywriting stage
    if req.stage_id:
        rows = await db.execute_fetchall("SELECT output_data FROM workflow_stages WHERE id=? AND workflow_id=?", (req.stage_id, workflow_id))
    else:
        rows = await db.execute_fetchall("SELECT output_data FROM workflow_stages WHERE workflow_id=? AND stage_name='copywriting'", (workflow_id,))
    await db.close()

    if not rows or not rows[0]["output_data"]:
        return {"error": "No copywriting output found"}

    script = rows[0]["output_data"]
    # Extract voiceover text — look for "Voiceover" sections
    import re
    vo_parts = re.findall(r'(?:Voiceover|voiceover|Voice.?over)[:\s]*(.+?)(?:\n\n|\n##|\n\*\*|$)', script, re.DOTALL)
    if vo_parts:
        vo_text = " ".join(p.strip() for p in vo_parts)
    else:
        # Fallback: use first 500 chars of the script
        vo_text = script[:500]

    vo_text = vo_text[:1000]  # Cap length

    path = await generate_voiceover(vo_text, voice=req.voice)
    from pathlib import Path
    web_path = f"/uploads/{Path(path).name}"
    return {"path": web_path, "voice": req.voice, "text_length": len(vo_text)}


@router.post("/workflows/{workflow_id}/add-voiceover")
async def add_voiceover_stage(workflow_id: int):
    """Add a voiceover stage to a workflow."""
    db = await get_db()
    # Get max stage number
    rows = await db.execute_fetchall("SELECT MAX(stage_number) as mx FROM workflow_stages WHERE workflow_id=?", (workflow_id,))
    max_num = rows[0]["mx"] or 0
    # Check if voiceover stage already exists
    existing = await db.execute_fetchall("SELECT id FROM workflow_stages WHERE workflow_id=? AND stage_name='voiceover'", (workflow_id,))
    if existing:
        await db.close()
        return {"status": "already_exists", "stage_id": existing[0]["id"]}
    cursor = await db.execute(
        "INSERT INTO workflow_stages (workflow_id, stage_number, stage_name, agent_role, status) VALUES (?,?,?,?,?)",
        (workflow_id, max_num + 1, "voiceover", "designer", "waiting"),
    )
    stage_id = cursor.lastrowid
    await db.commit()
    await db.close()
    return {"status": "added", "stage_id": stage_id}


class StageOutputReq(BaseModel):
    output: str


@router.post("/workflows/{workflow_id}/stages/{stage_id}/output")
async def save_stage_output(workflow_id: int, stage_id: int, req: StageOutputReq):
    """Save output to a stage and mark it complete."""
    db = await get_db()
    await db.execute(
        "UPDATE workflow_stages SET status='completed', output_data=?, completed_at=CURRENT_TIMESTAMP WHERE id=? AND workflow_id=?",
        (req.output, stage_id, workflow_id),
    )
    await db.commit()
    await db.close()
    return {"status": "saved"}


@router.post("/workflows/{workflow_id}/add-music")
async def add_music_stage(workflow_id: int):
    """Add a music stage to a workflow."""
    db = await get_db()
    rows = await db.execute_fetchall("SELECT MAX(stage_number) as mx FROM workflow_stages WHERE workflow_id=?", (workflow_id,))
    max_num = rows[0]["mx"] or 0
    existing = await db.execute_fetchall("SELECT id FROM workflow_stages WHERE workflow_id=? AND stage_name='music'", (workflow_id,))
    if existing:
        await db.close()
        return {"status": "already_exists", "stage_id": existing[0]["id"]}
    cursor = await db.execute(
        "INSERT INTO workflow_stages (workflow_id, stage_number, stage_name, agent_role, status) VALUES (?,?,?,?,?)",
        (workflow_id, max_num + 1, "music", "designer", "waiting"),
    )
    stage_id = cursor.lastrowid
    await db.commit()
    await db.close()
    return {"status": "added", "stage_id": stage_id}


@router.post("/workflows/{workflow_id}/publish")
async def publish_workflow(workflow_id: int):
    db = await get_db()
    await db.execute("UPDATE workflows SET status='published' WHERE id=?", (workflow_id,))
    await db.commit()
    await db.close()
    return {"status": "published"}


# --- Vibe Prospecting ---

class CampaignReq(BaseModel):
    location: str
    target_count: int = 50
    industries: list[str] = []
    exclude_industries: list[str] = []
    project_name: str = ""
    require_email: bool = True
    require_phone: bool = False
    require_website: bool = True


@router.post("/prospect/run")
async def run_campaign(req: CampaignReq):
    """Run a prospecting campaign — finds companies, scrapes contacts, qualifies leads."""
    from agents.prospecting import run_prospecting_campaign
    result = await run_prospecting_campaign(
        location=req.location,
        target_count=req.target_count,
        industries=req.industries if req.industries else None,
        exclude_industries=req.exclude_industries if req.exclude_industries else None,
        project_name=req.project_name or None,
        require_email=req.require_email,
        require_phone=req.require_phone,
        require_website=req.require_website,
    )
    return result


@router.post("/prospect/outreach/{project_id}")
async def run_outreach(project_id: int, max_sends: int = 10):
    """Auto-generate proposals for qualified leads in a project."""
    from agents.prospecting import auto_outreach
    result = await auto_outreach(project_id, max_sends)
    return result


# --- Notifications ---

@router.get("/notifications/config")
async def get_notification_config():
    """Get current notification settings."""
    from agents.notify import _get_config
    config = _get_config()
    return {
        "ntfy_enabled": config["ntfy_enabled"],
        "ntfy_topic": config["ntfy_topic"],
        "ntfy_url": f"{config['ntfy_server']}/{config['ntfy_topic']}",
        "telegram_enabled": config["telegram_enabled"],
    }


@router.post("/notifications/test")
async def test_notification():
    """Send a test notification."""
    from agents.notify import notify
    await notify("Test Notification 🔔", "Dubai Prod Agent notifications are working!", "default", "bell")
    return {"status": "sent"}


# --- Music Library ---

MUSIC_DIR = UPLOADS_DIR / "music"
MUSIC_DIR.mkdir(exist_ok=True)


@router.get("/music")
async def list_music():
    """List all music tracks in the library."""
    tracks = []
    for f in sorted(MUSIC_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file() and f.suffix.lower() in (".mp3", ".wav", ".ogg", ".m4a"):
            stat = f.stat()
            tracks.append({
                "name": f.stem,
                "filename": f.name,
                "path": f"/uploads/music/{f.name}",
                "size_mb": round(stat.st_size / (1024*1024), 2),
                "ext": f.suffix,
            })
    return tracks


@router.post("/music/upload")
async def upload_music(file: UploadFile = File(...)):
    """Upload a music track to the library."""
    safe_name = "".join(c if c.isalnum() or c in "_-. " else "_" for c in file.filename)
    dest = MUSIC_DIR / safe_name
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": safe_name, "path": f"/uploads/music/{safe_name}"}


@router.delete("/music/{filename}")
async def delete_music(filename: str):
    filepath = MUSIC_DIR / filename
    if filepath.exists():
        filepath.unlink()
        return {"status": "deleted"}
    return {"error": "Not found"}


@router.get("/music/free")
async def search_free_music(query: str = "corporate", limit: int = 10):
    """Search Pixabay for royalty-free music tracks."""
    import httpx
    try:
        # Pixabay has a free API for music
        url = f"https://pixabay.com/api/?key=placeholder&q={query}&media_type=music&per_page={limit}"
        # Since we may not have Pixabay API key, use a direct search approach
        search_url = f"https://pixabay.com/music/search/{query.replace(' ', '%20')}/"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(search_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
        import re
        # Extract track info from page
        tracks = []
        matches = re.findall(r'data-audio-url="([^"]+)".*?class="title"[^>]*>([^<]+)', resp.text, re.DOTALL)
        for audio_url, title in matches[:limit]:
            tracks.append({"title": title.strip(), "url": audio_url, "source": "pixabay"})
        return tracks
    except Exception as e:
        return []


# --- Agent Profiles & Memory ---

@router.get("/agents")
async def list_agents():
    from agents.brain import AGENTS
    return AGENTS


@router.get("/agents/{agent_key}/memory")
async def get_agent_memory(agent_key: str):
    from agents.memory import load_memory
    return load_memory(agent_key)


@router.delete("/agents/{agent_key}/memory")
async def clear_agent_memory(agent_key: str):
    from agents.memory import clear_memory
    clear_memory(agent_key)
    return {"status": "cleared"}


@router.delete("/agents/{agent_key}/chat")
async def clear_agent_chat_history(agent_key: str):
    from agents.brain import clear_agent_chat
    clear_agent_chat(agent_key)
    return {"status": "cleared"}


@router.delete("/chat/meeting")
async def clear_meeting_history():
    from agents.brain import clear_meeting_chat
    clear_meeting_chat()
    return {"status": "cleared"}


@router.post("/tasks/cleanup")
async def cleanup_stale_tasks():
    """Mark tasks stuck in_progress for over 1 hour as failed."""
    db = await get_db()
    result = await db.execute(
        "UPDATE tasks SET status='failed', completed_at=CURRENT_TIMESTAMP "
        "WHERE status='in_progress' AND created_at < datetime('now', '-1 hour')"
    )
    count = result.rowcount
    await db.commit()
    await db.close()
    return {"cleaned": count}


@router.delete("/chat/main")
async def clear_main_history():
    from agents.brain import clear_main_chat
    clear_main_chat()
    return {"status": "cleared"}


# --- Media Library ---

@router.get("/media")
async def list_media(media_type: str = None):
    """List all files in uploads folder with metadata."""
    if not UPLOADS_DIR.exists():
        return []

    files = []
    for f in sorted(UPLOADS_DIR.iterdir(), key=lambda x: x.stat().st_mtime if x.is_file() else 0, reverse=True):
        if f.is_dir():
            continue  # Skip _temp/ and other subdirs
        if f.is_file() and not f.name.startswith(".") and not f.name.startswith("thumb_") and not f.name.endswith(".txt") and not f.name.endswith(".srt"):
            ext = f.suffix.lower()
            if ext in (".mp4", ".mov", ".webm"):
                ftype = "video"
            elif ext in (".mp3", ".wav", ".ogg"):
                ftype = "audio"
            elif ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                ftype = "image"
            elif ext == ".srt":
                ftype = "subtitle"
            elif ext == ".pdf":
                ftype = "document"
            else:
                ftype = "other"

            if media_type and ftype != media_type:
                continue

            stat = f.stat()
            size_mb = round(stat.st_size / (1024 * 1024), 2)
            files.append({
                "name": f.name,
                "path": f"/uploads/{f.name}",
                "type": ftype,
                "size_mb": size_mb,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    return files


@router.delete("/media/{filename}")
async def delete_media(filename: str):
    filepath = UPLOADS_DIR / filename
    if filepath.exists() and filepath.is_file():
        filepath.unlink()
        return {"status": "deleted", "filename": filename}
    return {"error": "File not found"}


# --- Models ---

class ClientIn(BaseModel):
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    platform: str = ""
    status: str = "active"
    notes: str = ""
    monthly_fee: float = 0


class TaskIn(BaseModel):
    title: str
    description: str = ""
    client_id: int | None = None
    assigned_agent: str = "manager"
    priority: str = "medium"
    status: str = "pending"
    due_date: str | None = None


class ContentIn(BaseModel):
    client_id: int | None = None
    platform: str = ""
    content_type: str = "post"
    caption: str = ""
    media_url: str = ""
    status: str = "draft"
    scheduled_at: str | None = None
    notes: str = ""


# --- Clients ---

@router.get("/clients")
async def list_clients():
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM clients ORDER BY created_at DESC")
    await db.close()
    return [dict(r) for r in rows]


@router.post("/clients")
async def create_client(client: ClientIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO clients (name, company, email, phone, platform, status, notes, monthly_fee) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (client.name, client.company, client.email, client.phone,
         client.platform, client.status, client.notes, client.monthly_fee),
    )
    await db.commit()
    client_id = cursor.lastrowid
    await db.close()
    return {"id": client_id, "status": "created"}


@router.get("/clients/{client_id}")
async def get_client(client_id: int):
    db = await get_db()
    row = await db.execute_fetchall("SELECT * FROM clients WHERE id = ?", (client_id,))
    await db.close()
    return dict(row[0]) if row else {"error": "Not found"}


@router.put("/clients/{client_id}")
async def update_client(client_id: int, client: ClientIn):
    db = await get_db()
    await db.execute(
        "UPDATE clients SET name=?, company=?, email=?, phone=?, platform=?, "
        "status=?, notes=?, monthly_fee=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (client.name, client.company, client.email, client.phone,
         client.platform, client.status, client.notes, client.monthly_fee, client_id),
    )
    await db.commit()
    await db.close()
    return {"status": "updated"}


@router.delete("/clients/{client_id}")
async def delete_client(client_id: int):
    db = await get_db()
    await db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


# --- Tasks ---

@router.get("/tasks")
async def list_tasks():
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT t.*, c.name as client_name FROM tasks t "
        "LEFT JOIN clients c ON t.client_id = c.id "
        "ORDER BY CASE t.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, t.created_at DESC"
    )
    await db.close()
    return [dict(r) for r in rows]


@router.post("/tasks")
async def create_task(task: TaskIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO tasks (title, description, client_id, assigned_agent, priority, status, due_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task.title, task.description, task.client_id, task.assigned_agent,
         task.priority, task.status, task.due_date),
    )
    await db.commit()
    task_id = cursor.lastrowid
    await db.close()
    return {"id": task_id, "status": "created"}


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, task: TaskIn):
    db = await get_db()
    completed = datetime.now().isoformat() if task.status == "completed" else None
    await db.execute(
        "UPDATE tasks SET title=?, description=?, client_id=?, assigned_agent=?, "
        "priority=?, status=?, due_date=?, completed_at=? WHERE id=?",
        (task.title, task.description, task.client_id, task.assigned_agent,
         task.priority, task.status, task.due_date, completed, task_id),
    )
    await db.commit()
    await db.close()
    return {"status": "updated"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    db = await get_db()
    await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


# --- Content ---

@router.get("/content")
async def list_content():
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT co.*, c.name as client_name FROM content co "
        "LEFT JOIN clients c ON co.client_id = c.id "
        "ORDER BY co.created_at DESC"
    )
    await db.close()
    return [dict(r) for r in rows]


@router.post("/content")
async def create_content(content: ContentIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO content (client_id, platform, content_type, caption, media_url, status, scheduled_at, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (content.client_id, content.platform, content.content_type, content.caption,
         content.media_url, content.status, content.scheduled_at, content.notes),
    )
    await db.commit()
    content_id = cursor.lastrowid
    await db.close()
    return {"id": content_id, "status": "created"}


class ContentStatusUpdate(BaseModel):
    status: str


@router.put("/content/{content_id}/status")
async def update_content_status(content_id: int, update: ContentStatusUpdate):
    db = await get_db()
    await db.execute(
        "UPDATE content SET status = ? WHERE id = ?",
        (update.status, content_id),
    )
    await db.commit()
    await db.close()
    return {"status": "updated", "content_id": content_id}


# --- Design Projects ---

class DesignProjectIn(BaseModel):
    name: str = "Untitled Design"
    canvas_json: str = "{}"
    thumb_url: str = ""
    format: str = "1024x1024"
    width: int = 1080
    height: int = 1080


@router.get("/design-projects")
async def list_design_projects():
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM design_projects ORDER BY updated_at DESC"
        )
    except Exception:
        # Table might not exist yet, create it
        await db.execute("""
            CREATE TABLE IF NOT EXISTS design_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT 'Untitled Design',
                canvas_json TEXT DEFAULT '{}',
                thumb_url TEXT DEFAULT '',
                format TEXT DEFAULT '1024x1024',
                width INTEGER DEFAULT 1080,
                height INTEGER DEFAULT 1080,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        rows = []
    await db.close()
    return [dict(r) for r in rows]


@router.post("/design-projects")
async def create_design_project(proj: DesignProjectIn):
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO design_projects (name, canvas_json, thumb_url, format, width, height) VALUES (?,?,?,?,?,?)",
            (proj.name, proj.canvas_json, proj.thumb_url, proj.format, proj.width, proj.height),
        )
    except Exception:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS design_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT 'Untitled Design',
                canvas_json TEXT DEFAULT '{}',
                thumb_url TEXT DEFAULT '',
                format TEXT DEFAULT '1024x1024',
                width INTEGER DEFAULT 1080,
                height INTEGER DEFAULT 1080,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        cursor = await db.execute(
            "INSERT INTO design_projects (name, canvas_json, thumb_url, format, width, height) VALUES (?,?,?,?,?,?)",
            (proj.name, proj.canvas_json, proj.thumb_url, proj.format, proj.width, proj.height),
        )
    await db.commit()
    pid = cursor.lastrowid
    await db.close()
    return {"id": pid, "status": "created"}


@router.put("/design-projects/{project_id}")
async def update_design_project(project_id: int, proj: DesignProjectIn):
    db = await get_db()
    await db.execute(
        "UPDATE design_projects SET name=?, canvas_json=?, thumb_url=?, format=?, width=?, height=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (proj.name, proj.canvas_json, proj.thumb_url, proj.format, proj.width, proj.height, project_id),
    )
    await db.commit()
    await db.close()
    return {"status": "updated"}


@router.delete("/design-projects/{project_id}")
async def delete_design_project(project_id: int):
    db = await get_db()
    await db.execute("DELETE FROM design_projects WHERE id=?", (project_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


# --- Stock Photos Proxy ---

@router.get("/stock-photos")
async def search_stock_photos(query: str = "business", per_page: int = 20):
    """Search Pexels for free stock photos. Falls back to Unsplash URLs if no key."""
    import httpx, os, hashlib
    pexels_key = os.getenv("PEXELS_API_KEY", "")

    # If Pexels key is available and valid, use it
    if pexels_key and not pexels_key.startswith("YOUR_"):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}&orientation=square",
                    headers={"Authorization": pexels_key}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    photos = []
                    for p in data.get("photos", []):
                        photos.append({
                            "id": p["id"],
                            "thumb": p["src"]["small"],
                            "medium": p["src"]["medium"],
                            "large": p["src"]["large"],
                            "original": p["src"]["original"],
                            "alt": p.get("alt", query),
                            "photographer": p.get("photographer", ""),
                        })
                    return photos
        except Exception:
            pass

    # Fallback: Unsplash source URLs (no key needed, random photos)
    photos = []
    for i in range(per_page):
        seed = hashlib.md5(f"{query}_{i}".encode()).hexdigest()[:8]
        photos.append({
            "id": seed,
            "thumb": f"https://source.unsplash.com/200x200/?{query}&sig={seed}",
            "medium": f"https://source.unsplash.com/600x600/?{query}&sig={seed}",
            "large": f"https://source.unsplash.com/1200x1200/?{query}&sig={seed}",
            "original": f"https://source.unsplash.com/1920x1920/?{query}&sig={seed}",
            "alt": query,
            "photographer": "Unsplash",
        })
    return photos


# --- Agent Logs ---

@router.get("/agent-logs")
async def list_agent_logs(agent: str = None, limit: int = 50):
    db = await get_db()
    if agent:
        rows = await db.execute_fetchall(
            "SELECT * FROM agent_logs WHERE agent = ? ORDER BY created_at DESC LIMIT ?",
            (agent, limit),
        )
    else:
        rows = await db.execute_fetchall(
            "SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
    await db.close()
    return [dict(r) for r in rows]


@router.get("/agent-logs/{log_id}")
async def get_agent_log(log_id: int):
    db = await get_db()
    row = await db.execute_fetchall("SELECT * FROM agent_logs WHERE id = ?", (log_id,))
    await db.close()
    return dict(row[0]) if row else {"error": "Not found"}


# --- Dashboard Stats ---

@router.get("/dashboard")
async def dashboard_stats():
    db = await get_db()

    clients = await db.execute_fetchall("SELECT COUNT(*) as count FROM clients WHERE status='active'")
    total_clients = clients[0]["count"]

    revenue = await db.execute_fetchall("SELECT COALESCE(SUM(monthly_fee), 0) as total FROM clients WHERE status='active'")
    monthly_revenue = revenue[0]["total"]

    pending = await db.execute_fetchall("SELECT COUNT(*) as count FROM tasks WHERE status='pending'")
    pending_tasks = pending[0]["count"]

    drafts = await db.execute_fetchall("SELECT COUNT(*) as count FROM content WHERE status='draft'")
    draft_content = drafts[0]["count"]

    scheduled = await db.execute_fetchall("SELECT COUNT(*) as count FROM content WHERE status='scheduled'")
    scheduled_content = scheduled[0]["count"]

    recent_tasks = await db.execute_fetchall(
        "SELECT t.*, c.name as client_name FROM tasks t "
        "LEFT JOIN clients c ON t.client_id = c.id "
        "ORDER BY t.created_at DESC LIMIT 5"
    )

    recent_content = await db.execute_fetchall(
        "SELECT co.*, c.name as client_name FROM content co "
        "LEFT JOIN clients c ON co.client_id = c.id "
        "ORDER BY co.created_at DESC LIMIT 5"
    )

    await db.close()

    return {
        "total_clients": total_clients,
        "monthly_revenue": monthly_revenue,
        "pending_tasks": pending_tasks,
        "draft_content": draft_content,
        "scheduled_content": scheduled_content,
        "recent_tasks": [dict(r) for r in recent_tasks],
        "recent_content": [dict(r) for r in recent_content],
    }


# ---------------------------------------------------------------------------
# WhatsApp Bot Bridge endpoints
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str

class AgentChatRequest(BaseModel):
    agent: str
    message: str

@router.post("/chat")
async def whatsapp_chat(req: ChatRequest):
    """General brain chat — used by WhatsApp bot for unrouted messages."""
    from agents.brain import chat
    reply = await chat(req.message)
    return {"reply": reply}

@router.post("/agent-chat")
async def whatsapp_agent_chat(req: AgentChatRequest):
    """Direct agent chat — used by WhatsApp bot to talk to a specific agent."""
    from agents.brain import chat_agent, AGENTS
    agent_key = req.agent.lower()
    if agent_key not in AGENTS:
        agent_key = "sarah"
    reply = await chat_agent(req.message, agent_key, use_tools=True)
    return {"reply": reply, "agent": agent_key}

@router.post("/whatsapp/send")
async def send_to_whatsapp(payload: dict):
    """Send a WhatsApp message via Meta Cloud API."""
    import httpx
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    if not token or not phone_id:
        return {"ok": False, "error": "WhatsApp Cloud API not configured"}
    try:
        phone = payload.get("phone", os.getenv("WHATSAPP_OWNER_PHONE", ""))
        message = payload.get("message", "")
        url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, json={
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": message},
            }, headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            })
            return {"ok": r.status_code == 200}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# WhatsApp Cloud API Webhook — receives inbound messages from Meta
# ---------------------------------------------------------------------------

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "theagency-verify-2026")

from fastapi import Request

@router.api_route("/webhook/whatsapp", methods=["GET", "POST"])
async def whatsapp_webhook(request: Request):
    """Handle WhatsApp Cloud API webhooks — verification & incoming messages."""
    import httpx
    import logging
    logger = logging.getLogger("amine-agent")

    # GET = Meta verification challenge
    if request.method == "GET":
        params = request.query_params
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            logger.info("[whatsapp] Webhook verified")
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(challenge)
        return {"error": "Verification failed"}, 403

    # POST = incoming message
    body = await request.json()
    logger.info(f"[whatsapp] Webhook received: {json.dumps(body)[:200]}")

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        for msg in messages:
            if msg.get("type") != "text":
                continue

            from_number = msg.get("from", "")
            text = msg.get("text", {}).get("body", "").strip()
            if not text:
                continue

            logger.info(f"[whatsapp] Message from {from_number}: {text[:80]}")

            # Route to agent — detect agent name or default to Sarah
            agent_key = "sarah"
            lower = text.lower()
            agent_names = {"marcus": "marcus", "zara": "zara", "kai": "kai",
                          "elena": "elena", "alex": "alex", "sarah": "sarah"}
            for name, key in agent_names.items():
                if lower.startswith(name) or lower.startswith(f"@{name}"):
                    agent_key = key
                    break

            # Save as task in the platform database
            from agents.brain import chat_agent, AGENTS
            agent = AGENTS.get(agent_key, AGENTS["sarah"])
            logger.info(f"[whatsapp] Routing to {agent['name']} ({agent_key})...")

            try:
                db = await get_db()
                await db.execute(
                    "INSERT INTO tasks (title, description, assigned_agent, priority, status, source) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (text[:100], f"WhatsApp command from {from_number}: {text}",
                     agent_key, "medium", "in_progress", "whatsapp"),
                )
                await db.commit()
                await db.close()
                logger.info(f"[whatsapp] Task saved to platform")
            except Exception as db_err:
                logger.warning(f"[whatsapp] Could not save task: {db_err}")

            # Get agent reply
            try:
                reply = await chat_agent(text, agent_key, use_tools=True)
                logger.info(f"[whatsapp] Agent replied: {reply[:100]}")
            except Exception as agent_err:
                logger.error(f"[whatsapp] Agent error: {agent_err}")
                reply = f"Sorry, I encountered an error: {str(agent_err)[:200]}"

            # Update task to completed
            try:
                db = await get_db()
                await db.execute(
                    "UPDATE tasks SET status='completed', completed_at=? "
                    "WHERE source='whatsapp' AND title=? AND status='in_progress'",
                    (datetime.now().isoformat(), text[:100]),
                )
                await db.commit()
                await db.close()
            except Exception:
                pass

            # Format and send reply back via Cloud API
            formatted = f"{agent['emoji']} *{agent['name']}* _({agent['role']})_\n{'─' * 25}\n{reply[:3500]}"

            token_val = os.getenv("WHATSAPP_TOKEN")
            wa_phone_id = os.getenv("WHATSAPP_PHONE_ID")
            url = f"https://graph.facebook.com/v22.0/{wa_phone_id}/messages"

            async with httpx.AsyncClient(timeout=30) as c:
                wa_res = await c.post(url, json={
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "type": "text",
                    "text": {"body": formatted},
                }, headers={
                    "Authorization": f"Bearer {token_val}",
                    "Content-Type": "application/json",
                })
                logger.info(f"[whatsapp] Send status: {wa_res.status_code} - {wa_res.text[:200]}")

            logger.info(f"[whatsapp] Replied to {from_number} via {agent['name']}")

    except Exception as e:
        import traceback
        logger.error(f"[whatsapp] Webhook error: {e}\n{traceback.format_exc()}")

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# AI Image Generation API
# ---------------------------------------------------------------------------

class ImageGenRequest(BaseModel):
    prompt: str
    count: int = 1
    size: str = "1024x1024"
    style: str = "natural"


@router.post("/generate-images")
async def generate_images(req: ImageGenRequest):
    """Generate 1-4 images using DALL-E 3."""
    import openai, httpx
    from pathlib import Path as _P

    count = min(max(req.count, 1), 4)
    oa = openai.AsyncOpenAI()
    results = []

    for i in range(count):
        try:
            response = await oa.images.generate(
                model="dall-e-3",
                prompt=req.prompt,
                size=req.size,
                style=req.style,
                quality="hd",
                n=1,
            )
            image_url = response.data[0].url
            revised = response.data[0].revised_prompt

            # Download and save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}_{i+1}.png"
            save_path = _P(__file__).resolve().parent.parent / "uploads" / filename

            async with httpx.AsyncClient(timeout=30) as http:
                img_r = await http.get(image_url)
                save_path.write_bytes(img_r.content)

            results.append({
                "filename": filename,
                "url": f"/uploads/{filename}",
                "revised_prompt": revised,
            })
        except Exception as e:
            results.append({"error": str(e)})

    return {"images": results, "count": len(results)}


# ---------------------------------------------------------------------------
# AI Video Generation API
# ---------------------------------------------------------------------------

class VideoGenRequest(BaseModel):
    prompt: str
    duration: int = 30


@router.post("/generate-video")
async def generate_video(req: VideoGenRequest):
    """Generate a video using the agent pipeline."""
    try:
        from agents.brain import chat_agent
        reply = await chat_agent(
            f"Create a {req.duration}s video about: {req.prompt}",
            "zara",
            use_tools=True,
        )
        return {"status": "processing", "reply": reply}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Email Campaign Builder API
# ---------------------------------------------------------------------------

class EmailCampaignIn(BaseModel):
    campaign_name: str = "Untitled Campaign"
    subject: str = ""
    preview_text: str = ""
    sender_name: str = "Dubai Prod"
    sender_email: str = "info@dubaiprod.com"
    template_json: str = "[]"
    rendered_html: str = ""
    target_segment: str = ""
    selected_leads: str = "[]"
    status: str = "draft"
    scheduled_at: str | None = None


class SendTestReq(BaseModel):
    email: str


class SendCampaignReq(BaseModel):
    lead_emails: list[str]


@router.get("/campaigns")
async def list_campaigns():
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM email_campaigns ORDER BY updated_at DESC")
    await db.close()
    return [dict(r) for r in rows]


@router.post("/campaigns")
async def create_campaign(data: EmailCampaignIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO email_campaigns (campaign_name, subject, preview_text, sender_name, sender_email, "
        "template_json, rendered_html, target_segment, selected_leads, status, scheduled_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data.campaign_name, data.subject, data.preview_text, data.sender_name, data.sender_email,
         data.template_json, data.rendered_html, data.target_segment, data.selected_leads,
         data.status, data.scheduled_at),
    )
    await db.commit()
    cid = cursor.lastrowid
    await db.close()
    return {"id": cid, "status": "created"}


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int):
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM email_campaigns WHERE id=?", (campaign_id,))
    await db.close()
    if not rows:
        return {"error": "Not found"}
    return dict(rows[0])


@router.put("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: int, data: EmailCampaignIn):
    db = await get_db()
    await db.execute(
        "UPDATE email_campaigns SET campaign_name=?, subject=?, preview_text=?, sender_name=?, sender_email=?, "
        "template_json=?, rendered_html=?, target_segment=?, selected_leads=?, status=?, scheduled_at=?, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (data.campaign_name, data.subject, data.preview_text, data.sender_name, data.sender_email,
         data.template_json, data.rendered_html, data.target_segment, data.selected_leads,
         data.status, data.scheduled_at, campaign_id),
    )
    await db.commit()
    await db.close()
    return {"id": campaign_id, "status": "updated"}


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int):
    db = await get_db()
    await db.execute("DELETE FROM email_campaigns WHERE id=?", (campaign_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


@router.post("/campaigns/{campaign_id}/send-test")
async def send_test_campaign(campaign_id: int, data: SendTestReq):
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM email_campaigns WHERE id=?", (campaign_id,))
    await db.close()
    if not rows:
        return {"error": "Campaign not found"}
    campaign = dict(rows[0])
    html_body = campaign.get("rendered_html", "")
    subject = campaign.get("subject", "Test Email")
    if not html_body:
        return {"error": "No rendered HTML — save the campaign first"}
    try:
        from email_agent.sender import send_email
        sent = await asyncio.to_thread(
            send_email,
            to=data.email,
            subject=f"[TEST] {subject}",
            body=html_body,
            confirm_callback=lambda _: True,
        )
        if sent:
            return {"status": "sent", "to": data.email}
        return {"status": "failed", "error": "send_email returned False"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: int, data: SendCampaignReq):
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM email_campaigns WHERE id=?", (campaign_id,))
    if not rows:
        await db.close()
        return {"error": "Campaign not found"}
    campaign = dict(rows[0])
    html_body = campaign.get("rendered_html", "")
    subject = campaign.get("subject", "")
    if not html_body:
        await db.close()
        return {"error": "No rendered HTML — save the campaign first"}
    sent_count = 0
    errors = []
    from email_agent.sender import send_email
    for email_addr in data.lead_emails:
        try:
            sent = await asyncio.to_thread(
                send_email,
                to=email_addr,
                subject=subject,
                body=html_body,
                confirm_callback=lambda _: True,
            )
            if sent:
                sent_count += 1
        except Exception as e:
            errors.append({"email": email_addr, "error": str(e)})
    # Update campaign status
    await db.execute(
        "UPDATE email_campaigns SET status='sent', sent_count=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (sent_count, campaign_id),
    )
    await db.commit()
    await db.close()
    return {"status": "sent", "sent_count": sent_count, "errors": errors}


@router.get("/all-leads")
async def get_all_leads():
    """Get all leads across all projects (for campaign targeting)."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT l.*, rp.name as project_name FROM leads l "
        "LEFT JOIN research_projects rp ON l.project_id = rp.id "
        "WHERE l.email != '' ORDER BY l.created_at DESC"
    )
    await db.close()
    return [dict(r) for r in rows]


@router.get("/gallery")
async def get_gallery():
    """Return all generated images and videos."""
    from pathlib import Path as _P
    uploads = _P(__file__).resolve().parent.parent / "uploads"
    files = []
    for f in sorted(uploads.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov'):
            files.append({
                "filename": f.name,
                "url": f"/uploads/{f.name}",
                "type": "video" if f.suffix.lower() in ('.mp4', '.mov') else "image",
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    return files[:50]


# ═══ EMAIL TEMPLATES ═══

class EmailTemplateIn(BaseModel):
    name: str
    sections_json: str = "[]"
    rendered_html: str = ""
    language: str = "en"


@router.get("/email-templates")
async def list_email_templates():
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, name, language, created_at, updated_at FROM email_templates ORDER BY updated_at DESC"
    )
    await db.close()
    return [dict(r) for r in rows]


@router.get("/email-templates/{template_id}")
async def get_email_template(template_id: int):
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM email_templates WHERE id=?", (template_id,))
    await db.close()
    if not rows:
        return {"error": "Not found"}
    return dict(rows[0])


@router.post("/email-templates")
async def create_email_template(data: EmailTemplateIn):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO email_templates (name, sections_json, rendered_html, language) VALUES (?, ?, ?, ?)",
        (data.name, data.sections_json, data.rendered_html, data.language),
    )
    await db.commit()
    tid = cursor.lastrowid
    await db.close()
    return {"id": tid, "status": "created"}


@router.put("/email-templates/{template_id}")
async def update_email_template(template_id: int, data: EmailTemplateIn):
    db = await get_db()
    await db.execute(
        "UPDATE email_templates SET name=?, sections_json=?, rendered_html=?, language=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (data.name, data.sections_json, data.rendered_html, data.language, template_id),
    )
    await db.commit()
    await db.close()
    return {"id": template_id, "status": "updated"}


@router.delete("/email-templates/{template_id}")
async def delete_email_template(template_id: int):
    db = await get_db()
    await db.execute("DELETE FROM email_templates WHERE id=?", (template_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}


@router.post("/send-template-emails")
async def send_template_emails(data: dict):
    """Send personalized template emails to selected leads.

    Expects: { template_id: int, lead_ids: [int], subject: str }
    Personalizes {{clientName}} in the HTML for each lead.
    """
    template_id = data.get("template_id")
    lead_ids = data.get("lead_ids", [])
    subject = data.get("subject", "Dubai Prod — Your Digital Growth Partner")

    if not template_id or not lead_ids:
        return {"error": "template_id and lead_ids required"}

    db = await get_db()

    # Get template
    tpl_rows = await db.execute_fetchall("SELECT * FROM email_templates WHERE id=?", (template_id,))
    if not tpl_rows:
        await db.close()
        return {"error": "Template not found"}
    tpl = dict(tpl_rows[0])
    base_html = tpl.get("rendered_html", "")
    if not base_html:
        await db.close()
        return {"error": "Template has no rendered HTML"}

    # Get leads
    placeholders = ",".join("?" * len(lead_ids))
    lead_rows = await db.execute_fetchall(
        f"SELECT * FROM leads WHERE id IN ({placeholders})", lead_ids
    )
    await db.close()

    if not lead_rows:
        return {"error": "No leads found"}

    # Send personalized emails
    from email_agent.sender import send_email
    sent_count = 0
    errors = []
    for lead in lead_rows:
        lead = dict(lead)
        email_addr = lead.get("email", "")
        if not email_addr:
            continue
        # Personalize HTML
        name = lead.get("contact_name") or lead.get("company_name") or "there"
        company = lead.get("company_name") or ""
        personalized = base_html.replace("[First Name]", name).replace("{{First Name}}", name)
        personalized = personalized.replace("[Company]", company).replace("{{Company}}", company)
        personalized = personalized.replace("[Ime]", name)  # Slovenian
        try:
            sent = await asyncio.to_thread(
                send_email,
                to=email_addr,
                subject=subject.replace("[Company]", company).replace("{{Company}}", company),
                body=personalized,
                confirm_callback=lambda _: True,
            )
            if sent:
                sent_count += 1
        except Exception as e:
            errors.append({"email": email_addr, "error": str(e)})

    return {"status": "sent", "sent_count": sent_count, "total": len(lead_rows), "errors": errors}


# ═══ VIDEO TRANSCRIPTION ═══

class TranscribeRequest(BaseModel):
    url: str = ""
    language: str = ""  # auto-detect if empty


@router.post("/transcribe")
async def transcribe_video(data: TranscribeRequest):
    """Transcribe a video from URL (YouTube, Instagram, TikTok, etc.) or uploaded file.

    Uses yt-dlp to download audio, then OpenAI Whisper to transcribe.
    """
    if not data.url:
        return {"error": "URL is required"}

    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_path = uploads_dir / f"transcribe_{ts}.mp3"

    try:
        # Step 1: Download audio with yt-dlp
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "5",
            "--max-filesize", "50M",
            "--no-playlist",
            "--no-check-certificates",
            "--prefer-free-formats",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "-o", str(audio_path).replace(".mp3", ".%(ext)s"),
            data.url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        # Find the actual output file (yt-dlp may change extension)
        actual_file = None
        for ext in [".mp3", ".m4a", ".opus", ".webm"]:
            candidate = Path(str(audio_path).replace(".mp3", ext))
            if candidate.exists():
                actual_file = candidate
                break

        if not actual_file or not actual_file.exists():
            return {"error": f"Failed to download audio: {stderr.decode()[:300]}"}

        # Convert to mp3 if not already
        if actual_file.suffix != ".mp3":
            mp3_path = actual_file.with_suffix(".mp3")
            ffmpeg_proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", str(actual_file), "-vn", "-acodec", "libmp3lame",
                "-q:a", "5", str(mp3_path), "-y",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(ffmpeg_proc.communicate(), timeout=60)
            actual_file.unlink(missing_ok=True)
            actual_file = mp3_path

        file_size = actual_file.stat().st_size
        if file_size > 25 * 1024 * 1024:  # Whisper limit is 25MB
            return {"error": f"Audio file too large ({file_size // 1024 // 1024}MB). Max 25MB."}

        # Step 2: Transcribe with OpenAI Whisper
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(actual_file, "rb") as f:
            kwargs = {"model": "whisper-1", "file": f, "response_format": "verbose_json"}
            if data.language:
                kwargs["language"] = data.language
            result = await asyncio.to_thread(
                client.audio.transcriptions.create, **kwargs
            )

        # Clean up audio file
        actual_file.unlink(missing_ok=True)

        return {
            "text": result.text,
            "language": getattr(result, "language", ""),
            "duration": getattr(result, "duration", 0),
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in getattr(result, "segments", [])
            ],
        }

    except asyncio.TimeoutError:
        return {"error": "Download timed out (max 2 minutes)"}
    except Exception as e:
        # Clean up on error
        audio_path.unlink(missing_ok=True)
        return {"error": str(e)}


@router.post("/transcribe-upload")
async def transcribe_upload(file: UploadFile = File(...), language: str = ""):
    """Transcribe an uploaded video/audio file."""
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save uploaded file
    safe_name = f"transcribe_{ts}_{file.filename}"
    dest = uploads_dir / safe_name
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Extract audio if it's a video
        audio_path = dest
        if dest.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
            audio_path = dest.with_suffix(".mp3")
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", str(dest), "-vn", "-acodec", "libmp3lame",
                "-q:a", "5", str(audio_path), "-y",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=60)
            dest.unlink(missing_ok=True)

        file_size = audio_path.stat().st_size
        if file_size > 25 * 1024 * 1024:
            return {"error": f"File too large ({file_size // 1024 // 1024}MB). Max 25MB."}

        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(audio_path, "rb") as f:
            kwargs = {"model": "whisper-1", "file": f, "response_format": "verbose_json"}
            if language:
                kwargs["language"] = language
            result = await asyncio.to_thread(
                client.audio.transcriptions.create, **kwargs
            )

        audio_path.unlink(missing_ok=True)

        return {
            "text": result.text,
            "language": getattr(result, "language", ""),
            "duration": getattr(result, "duration", 0),
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in getattr(result, "segments", [])
            ],
        }
    except Exception as e:
        dest.unlink(missing_ok=True)
        return {"error": str(e)}
