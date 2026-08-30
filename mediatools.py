import re
import subprocess
from pathlib import Path

TIME_RANGE_RE = re.compile(
    r"^\s*(\d{1,2}:)?\d{1,2}:\d{2}\s*-\s*(\d{1,2}:)?\d{1,2}:\d{2}\s*$"
)


def _run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:])


def to_mp3(src: Path) -> Path:
    dst = src.with_suffix(".mp3")
    _run_ffmpeg(
        ["-i", str(src), "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", str(dst)]
    )
    return dst


def parse_time_range(text: str) -> tuple[str, str] | None:
    if not TIME_RANGE_RE.match(text):
        return None
    start, end = (part.strip() for part in text.split("-"))
    return start, end


def trim(src: Path, start: str, end: str) -> Path:
    dst = src.with_name(f"{src.stem}_trim{src.suffix}")
    _run_ffmpeg(["-i", str(src), "-ss", start, "-to", end, "-c", "copy", str(dst)])
    return dst


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def rename(src: Path, artist: str, title: str) -> Path:
    dst = src.with_name(f"{sanitize_filename(artist)} - {sanitize_filename(title)}{src.suffix}")
    _run_ffmpeg(
        [
            "-i", str(src),
            "-c", "copy",
            "-metadata", f"artist={artist}",
            "-metadata", f"title={title}",
            str(dst),
        ]
    )
    return dst
