"""Video generation pipeline — DALL-E + OpenAI TTS + FFmpeg.

Pipeline: prompt → scene images → voiceover → music → Ken Burns video → final mix
"""

import json
import logging
import os
import subprocess
import asyncio
import time
from pathlib import Path
from datetime import datetime

import httpx
import openai

logger = logging.getLogger("amine-agent")

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


# ---- Voiceover Generation (ElevenLabs + OpenAI TTS) ----

def _get_elevenlabs_key():
    return os.getenv("ELEVENLABS_API_KEY", "")


async def generate_voiceover(
    text: str,
    voice: str = "onyx",
    speed: float = 1.0,
    use_elevenlabs: bool = True,
) -> str:
    """Generate voiceover audio.

    Uses ElevenLabs if API key is set (supports custom/cloned voices).
    Falls back to OpenAI TTS otherwise.

    Args:
        text: Script to speak
        voice: Voice name/ID. For ElevenLabs: voice name or ID from your library.
               For OpenAI: alloy, echo, fable, onyx, nova, shimmer.
        speed: Speech speed (OpenAI only, 0.25-4.0)
        use_elevenlabs: Try ElevenLabs first if available
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"voiceover_{timestamp}.mp3"
    filepath = UPLOADS_DIR / filename

    # Try ElevenLabs first
    el_key = _get_elevenlabs_key()
    if use_elevenlabs and el_key:
        try:
            audio_data = await _generate_elevenlabs(text, voice, el_key)
            filepath.write_bytes(audio_data)
            logger.info(f"[video] ElevenLabs voiceover: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.warning(f"[video] ElevenLabs failed ({e}), falling back to OpenAI TTS")

    # Fallback: OpenAI TTS
    client = openai.AsyncOpenAI()
    # Map ElevenLabs voice names to OpenAI voices if needed
    openai_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
    if voice not in openai_voices:
        voice = "onyx"  # Default fallback

    response = await client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text,
        speed=speed,
    )

    filepath.write_bytes(response.content)
    logger.info(f"[video] OpenAI voiceover: {filepath}")
    return str(filepath)


async def _generate_elevenlabs(text: str, voice: str, api_key: str) -> bytes:
    """Generate audio with ElevenLabs API."""
    import asyncio
    from elevenlabs import ElevenLabs

    def _sync_generate():
        client = ElevenLabs(api_key=api_key)

        # Find voice ID from name
        voice_id = voice
        try:
            voices_list = client.voices.get_all()
            for v in voices_list.voices:
                # Match by name (case-insensitive, partial match)
                if voice.lower() in v.name.lower() or v.name.lower().startswith(voice.lower()):
                    voice_id = v.voice_id
                    break
        except Exception:
            pass

        # If still not a valid ID, use first available voice
        if len(voice_id) > 30 or not any(c.isalnum() for c in voice_id[:5]):
            pass  # Already a valid ID
        elif len(voice_id) < 15:
            # Probably still a name that wasn't found — use default
            try:
                voice_id = voices_list.voices[0].voice_id
            except Exception:
                pass

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        # audio is a generator, collect all chunks
        chunks = b""
        for chunk in audio:
            chunks += chunk
        return chunks

    return await asyncio.to_thread(_sync_generate)


async def list_elevenlabs_voices() -> list[dict]:
    """List all available ElevenLabs voices (including cloned ones)."""
    el_key = _get_elevenlabs_key()
    if not el_key:
        return []

    import asyncio
    from elevenlabs import ElevenLabs

    def _sync_list():
        client = ElevenLabs(api_key=el_key)
        voices = client.voices.get_all()
        return [{"id": v.voice_id, "name": v.name, "category": v.category or "custom"}
                for v in voices.voices]

    try:
        return await asyncio.to_thread(_sync_list)
    except Exception as e:
        logger.error(f"[video] ElevenLabs list voices error: {e}")
        return []


def _to_web_path(filepath: str) -> str:
    """Convert full filesystem path to /uploads/filename web path."""
    return f"/uploads/{Path(filepath).name}"


def _get_audio_duration(path: str) -> float:
    """Get duration of audio file via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        data = json.loads(r.stdout)
        return float(data.get("format", {}).get("duration", 0))
    return 0


# ---- Subtitle Generation ----

def generate_subtitles(text: str, duration: float) -> str:
    """Generate SRT subtitle file from text."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"subtitles_{timestamp}.srt"
    filepath = UPLOADS_DIR / filename

    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return str(filepath)

    # ~4-6 words per chunk, timed to fill the duration
    chunk_size = max(3, min(6, total_words // max(1, int(duration / 2.5))))
    chunks = []
    for i in range(0, total_words, chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))

    time_per_chunk = duration / len(chunks) if chunks else 1

    srt_lines = []
    for i, chunk in enumerate(chunks):
        start = i * time_per_chunk
        end = min((i + 1) * time_per_chunk, duration)
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
        srt_lines.append(chunk)
        srt_lines.append("")

    filepath.write_text("\n".join(srt_lines))
    logger.info(f"[video] Subtitles generated: {filepath}")
    return str(filepath)


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ---- Scene Generation with GPT ----

async def _generate_scene_descriptions(prompt: str, num_scenes: int, script: str) -> list[str]:
    """Use GPT to create distinct, vivid scene descriptions for each image."""
    client = openai.AsyncOpenAI()

    system = """You are a visual director for short-form social media videos.
Given a concept and script, create distinct scene descriptions for AI image generation.
Each scene must be DIFFERENT — different angle, composition, subject, mood.
Write in a visual, photographic style. Be specific about lighting, colors, composition.
Return ONLY a JSON array of strings, one per scene. No other text."""

    user_msg = f"""Concept: {prompt}
Script: {script}
Number of scenes: {num_scenes}

Create {num_scenes} distinct, cinematic scene descriptions. Each should be 1-2 sentences.
Make them visually diverse — wide shots, close-ups, details, aerial views, etc.
Return JSON array only."""

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.9,
            max_tokens=1000,
        )
        text = resp.choices[0].message.content.strip()
        # Parse JSON from response
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "").strip()
        scenes = json.loads(text)
        if isinstance(scenes, list) and len(scenes) >= num_scenes:
            return scenes[:num_scenes]
    except Exception as e:
        logger.warning(f"[video] Scene generation failed: {e}, using fallback")

    # Fallback: simple scene variations
    angles = ["wide establishing shot", "close-up detail", "dramatic low angle", "aerial view from above", "intimate medium shot", "dynamic tracking shot"]
    return [f"{prompt}. {angles[i % len(angles)]}. Ultra realistic, cinematic 4K." for i in range(num_scenes)]


# ---- Full Pipeline ----

async def create_full_video(
    prompt: str,
    script: str,
    num_clips: int = 4,
    clip_duration: int = 5,
    voice: str = "onyx",
    aspect_ratio: str = "9:16",
    target_duration: int = 0,
    image_urls: list[str] = None,
) -> dict:
    """Full video production pipeline.

    1. Generate voiceover → get real audio duration
    2. Generate diverse scene images with DALL-E
    3. Create Ken Burns slideshow matched to voiceover length
    4. Mix voiceover + video + subtitles

    Args:
        prompt: Visual concept for video
        script: Voiceover script
        num_clips: Number of scenes (2-8)
        clip_duration: Seconds per scene (3-8)
        voice: TTS voice
        aspect_ratio: 9:16, 16:9, 1:1
        target_duration: Desired total duration in seconds (0 = auto from voiceover)
    """
    result = {
        "clips": [],
        "voiceover": None,
        "subtitles": None,
        "final_video": None,
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Generate voiceover FIRST — its duration drives everything
    logger.info(f"[video] Step 1: Voiceover ({len(script)} chars, voice={voice})")
    voiceover_path = await generate_voiceover(script, voice=voice)
    result["voiceover"] = voiceover_path

    # Get actual voiceover duration
    vo_duration = _get_audio_duration(voiceover_path)
    logger.info(f"[video] Voiceover duration: {vo_duration:.1f}s")

    # Calculate actual video duration — match voiceover length
    if target_duration > 0:
        total_duration = target_duration
    elif vo_duration > 0:
        total_duration = vo_duration + 0.5  # Tiny pad
    else:
        total_duration = num_clips * clip_duration

    # Adjust num_clips and clip_duration to match total_duration
    if total_duration <= 10:
        num_clips = min(num_clips, 3)
    elif total_duration <= 20:
        num_clips = min(num_clips, 5)
    else:
        num_clips = min(num_clips, 8)

    actual_clip_dur = total_duration / num_clips
    logger.info(f"[video] Plan: {num_clips} scenes x {actual_clip_dur:.1f}s = {total_duration:.1f}s total")

    # Step 2: Generate subtitles timed to voiceover
    logger.info(f"[video] Step 2: Subtitles")
    subtitle_path = generate_subtitles(script, vo_duration or total_duration)
    result["subtitles"] = subtitle_path

    # Step 3: Generate scene images with DALL-E
    logger.info(f"[video] Step 3: Generating {num_clips} scene images")
    scene_descs = await _generate_scene_descriptions(prompt, num_clips, script)

    image_paths = []
    oa_client = openai.AsyncOpenAI()

    size_map = {"9:16": "1024x1792", "16:9": "1792x1024", "1:1": "1024x1024"}
    dalle_size = size_map.get(aspect_ratio, "1024x1792")

    for i, scene_desc in enumerate(scene_descs):
        full_prompt = f"{scene_desc} Ultra realistic, cinematic photography, 4K quality, dramatic lighting, professional color grading."
        logger.info(f"[video] Image {i+1}/{num_clips}: {scene_desc[:80]}...")

        try:
            response = await oa_client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size=dalle_size,
                style="vivid",
                quality="hd",
                n=1,
            )

            image_url = response.data[0].url
            img_file = UPLOADS_DIR / f"scene_{i}_{ts}.png"

            async with httpx.AsyncClient(timeout=60) as http:
                img_resp = await http.get(image_url)
                img_file.write_bytes(img_resp.content)

            image_paths.append(str(img_file))
            result["clips"].append(str(img_file))
        except Exception as e:
            logger.error(f"[video] Image {i+1} failed: {e}")

    if not image_paths:
        result["note"] = "Failed to generate images."
        return result

    # Step 4: Create Ken Burns slideshow — EXACT duration matching voiceover
    logger.info(f"[video] Step 4: Ken Burns slideshow ({len(image_paths)} images, {total_duration:.1f}s)")
    video_no_audio = UPLOADS_DIR / f"slideshow_{ts}.mp4"

    # Resolution based on aspect ratio
    res_map = {"9:16": "1080x1920", "16:9": "1920x1080", "1:1": "1080x1080"}
    resolution = res_map.get(aspect_ratio, "1080x1920")
    res_w, res_h = resolution.split("x")

    fps = 25
    inputs = []
    filter_parts = []

    for i, img in enumerate(image_paths):
        dur = actual_clip_dur
        frames = int(dur * fps)
        inputs.extend(["-loop", "1", "-t", str(dur), "-i", img])

        # Alternate Ken Burns effects — scale to 4000 (not 8000, faster)
        if i % 3 == 0:
            # Slow zoom in
            filter_parts.append(
                f"[{i}:v]scale=4000:-1,zoompan=z='min(zoom+0.002,1.3)'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={resolution}:fps={fps}[v{i}]"
            )
        elif i % 3 == 1:
            # Pan right
            filter_parts.append(
                f"[{i}:v]scale=4000:-1,zoompan=z='1.2'"
                f":x='if(eq(on,0),0,min(x+3,iw-iw/zoom))':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={resolution}:fps={fps}[v{i}]"
            )
        else:
            # Slow zoom out
            filter_parts.append(
                f"[{i}:v]scale=4000:-1,zoompan=z='if(eq(on,0),1.3,max(zoom-0.002,1.0))'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={resolution}:fps={fps}[v{i}]"
            )

    concat_inputs = "".join(f"[v{i}]" for i in range(len(image_paths)))
    filter_complex = ";".join(filter_parts) + f";{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[outv]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-t", str(total_duration),  # Force exact duration
        str(video_no_audio),
    ]

    proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        logger.error(f"[video] Ken Burns error: {proc.stderr[:300]}")
        # Fallback: simple crossfade slideshow
        logger.info("[video] Trying simple slideshow fallback")
        concat_file = UPLOADS_DIR / f"concat_{ts}.txt"
        lines = []
        for p in image_paths:
            lines.append(f"file '{p}'")
            lines.append(f"duration {actual_clip_dur}")
        # Last image needs no duration
        lines.append(f"file '{image_paths[-1]}'")
        concat_file.write_text("\n".join(lines))

        cmd_simple = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-vf", f"scale={res_w}:{res_h}:force_original_aspect_ratio=decrease,"
                   f"pad={res_w}:{res_h}:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-t", str(total_duration),
            str(video_no_audio),
        ]
        proc2 = await asyncio.to_thread(subprocess.run, cmd_simple, capture_output=True, text=True, timeout=120)
        if proc2.returncode != 0:
            logger.error(f"[video] Fallback failed: {proc2.stderr[:300]}")
            result["note"] = "Video compilation failed."
            return result

    # Step 5: Final mix — voiceover + subtitles burned in
    logger.info(f"[video] Step 5: Final mix (voiceover + subtitles)")
    final_path = UPLOADS_DIR / f"final_{ts}.mp4"
    sub_style = "FontSize=24,FontName=Arial,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=40,Bold=1"

    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(video_no_audio),
        "-i", voiceover_path,
        "-vf", f"subtitles={subtitle_path}:force_style='{sub_style}'",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(final_path),
    ]

    proc3 = await asyncio.to_thread(subprocess.run, cmd_final, capture_output=True, text=True, timeout=120)
    if proc3.returncode != 0:
        logger.error(f"[video] Subtitle burn failed: {proc3.stderr[:300]}")
        # Fallback: just voiceover, no subtitles
        cmd_nosub = [
            "ffmpeg", "-y",
            "-i", str(video_no_audio),
            "-i", voiceover_path,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            str(final_path),
        ]
        await asyncio.to_thread(subprocess.run, cmd_nosub, capture_output=True, timeout=60)

    # Verify final duration
    final_dur = _get_audio_duration(str(final_path))
    logger.info(f"[video] DONE! Final video: {final_path} ({final_dur:.1f}s)")

    # Return web-accessible paths (not filesystem paths)
    result["final_video"] = f"/uploads/{final_path.name}"
    result["voiceover"] = f"/uploads/{Path(voiceover_path).name}"
    result["subtitles"] = f"/uploads/{Path(subtitle_path).name}"
    result["clips"] = [f"/uploads/{Path(p).name}" for p in image_paths]
    result["duration"] = round(final_dur, 1)
    return result
