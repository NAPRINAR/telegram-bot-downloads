import re
import uuid
from pathlib import Path

import yt_dlp

DOWNLOADS_DIR = Path(__file__).parent / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

URL_RE = re.compile(r"https?://\S+")

# Cap video height so files usually stay under Telegram's 50MB bot upload limit.
MAX_HEIGHT = 720


def extract_url(text: str) -> str | None:
    match = URL_RE.search(text)
    return match.group(0) if match else None


def download_video(url: str, chat_id: int) -> Path:
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
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if info.get("requested_downloads"):
            filepath = info["requested_downloads"][0]["filepath"]

    return Path(filepath)
