import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Callable

import yt_dlp

DOWNLOADS_DIR = Path(__file__).parent / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

URL_RE = re.compile(r"https?://\S+")

# Cap video height so files usually stay under Telegram's 50MB bot upload limit.
MAX_HEIGHT = 720

# Session files older than this get swept up by cleanup_stale_files().
STALE_AFTER_SECONDS = 6 * 60 * 60

ProgressHook = Callable[[dict], None]


def extract_url(text: str) -> str | None:
    match = URL_RE.search(text)
    return match.group(0) if match else None


def cleanup_session(chat_id: int) -> None:
    """Wipe any leftover files from a chat's previous download chain."""
    session_dir = DOWNLOADS_DIR / str(chat_id)
    shutil.rmtree(session_dir, ignore_errors=True)


def cleanup_stale_files(max_age_seconds: int = STALE_AFTER_SECONDS) -> None:
    """Remove session files the user never finished processing."""
    cutoff = time.time() - max_age_seconds
    for session_dir in DOWNLOADS_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        for file in session_dir.iterdir():
            if file.stat().st_mtime < cutoff:
                file.unlink(missing_ok=True)
        if not any(session_dir.iterdir()):
            session_dir.rmdir()


def download_video(url: str, chat_id: int, progress_hook: ProgressHook | None = None) -> Path:
    session_dir = DOWNLOADS_DIR / str(chat_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:8]
    out_template = str(session_dir / f"{file_id}.%(ext)s")

    ydl_opts = {
        "format": f"bv*[height<={MAX_HEIGHT}]+ba/b[height<={MAX_HEIGHT}]/best",
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook] if progress_hook else [],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if info.get("requested_downloads"):
            filepath = info["requested_downloads"][0]["filepath"]

    return Path(filepath)
