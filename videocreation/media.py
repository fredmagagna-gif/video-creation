"""Informazioni sui file media via ffprobe."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MediaInfo:
    duration: float
    has_audio: bool
    width: int | None
    height: int | None


def probe(path: Path) -> MediaInfo:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe non riesce a leggere {path}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    duration = float(data.get("format", {}).get("duration") or 0.0)
    return MediaInfo(
        duration=duration,
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
        width=int(video["width"]) if video and "width" in video else None,
        height=int(video["height"]) if video and "height" in video else None,
    )
