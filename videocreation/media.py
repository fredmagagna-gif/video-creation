"""FFmpeg/ffprobe: quale binario usare e informazioni sui file media."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

# L'ffmpeg standard di Homebrew non include libass (niente filtro `subtitles`);
# `brew install ffmpeg-full` sì, ma non lo mette nel PATH.
FFMPEG_FULL_DIRS = [
    Path("/opt/homebrew/opt/ffmpeg-full/bin"),
    Path("/usr/local/opt/ffmpeg-full/bin"),
]
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}


@dataclass
class MediaInfo:
    duration: float
    has_audio: bool
    width: int | None
    height: int | None
    color_transfer: str | None = None
    color_primaries: str | None = None
    color_space: str | None = None

    @property
    def is_hdr(self) -> bool:
        return self.color_transfer in HDR_TRANSFERS


def _executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def find_ffmpeg() -> Path | None:
    """Ordine: $VIDEOCREATION_FFMPEG_DIR, ffmpeg-full di Homebrew, ffmpeg nel PATH."""
    dirs = []
    if os.environ.get("VIDEOCREATION_FFMPEG_DIR"):
        dirs.append(Path(os.environ["VIDEOCREATION_FFMPEG_DIR"]))
    dirs += FFMPEG_FULL_DIRS
    for folder in dirs:
        if _executable(folder / "ffmpeg"):
            return folder / "ffmpeg"
    found = shutil.which("ffmpeg")
    return Path(found) if found else None


def ffprobe_for(ffmpeg: Path) -> Path | None:
    sibling = Path(ffmpeg).with_name("ffprobe")
    if _executable(sibling):
        return sibling
    found = shutil.which("ffprobe")
    return Path(found) if found else None


def has_subtitles_filter(ffmpeg: Path) -> bool:
    result = subprocess.run([str(ffmpeg), "-hide_banner", "-filters"],
                            capture_output=True, text=True)
    return any(line.split()[1:2] == ["subtitles"] for line in result.stdout.splitlines())


def probe(path: Path, ffprobe: Path | str = "ffprobe") -> MediaInfo:
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe non riesce a leggere {path}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams
                  if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    duration = float(data.get("format", {}).get("duration") or 0.0)
    return MediaInfo(
        duration=duration,
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
        width=int(video["width"]) if video and "width" in video else None,
        height=int(video["height"]) if video and "height" in video else None,
        color_transfer=video.get("color_transfer") if video else None,
        color_primaries=video.get("color_primaries") if video else None,
        color_space=video.get("color_space") if video else None,
    )
