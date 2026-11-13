"""Monta voice-over, musica e sottotitoli su un video con FFmpeg."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from videocreation.media import MediaInfo, probe
from videocreation.subtitles import transcript_to_srt
from videocreation.voicestudio import VoiceStudioError, transcribe_words

CODA_VOCE_S = 0.5
SUB_STYLE = (
    "Fontname=Arial,FontSize=14,Bold=1,PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=60"
)
_AFMT = "aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"


def _durata_output(info_video: MediaInfo, durata_voce: float) -> float:
    return max(info_video.duration, durata_voce + CODA_VOCE_S)


def build_command(video: Path, voce: Path, out: Path, *, info_video: MediaInfo,
                  durata_voce: float, musica: Path | None = None,
                  srt_name: str | None = None, audio_originale: str = "abbassa",
                  volume_musica: float = 0.25) -> list[str]:
    if audio_originale not in ("abbassa", "togli"):
        raise ValueError("audio_originale deve essere 'abbassa' o 'togli'")
    durata = _durata_output(info_video, durata_voce)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(voce)]
    if musica:
        cmd += ["-stream_loop", "-1", "-i", str(musica)]

    graph: list[str] = []
    video_filters = []
    extra = durata - info_video.duration
    if extra > 0.01:
        video_filters.append(f"tpad=stop_mode=clone:stop_duration={extra:.3f}")
    if srt_name:
        video_filters.append(f"subtitles={srt_name}:force_style='{SUB_STYLE}'")
    graph.append(f"[0:v]{','.join(video_filters) or 'null'}[v]")

    fondo = []
    if info_video.has_audio and audio_originale == "abbassa":
        graph.append(f"[0:a]{_AFMT},apad[orig]")
        fondo.append("[orig]")
    if musica:
        graph.append(f"[2:a]{_AFMT},volume={volume_musica}[mus]")
        fondo.append("[mus]")

    graph.append(f"[1:a]{_AFMT},apad[vo]")
    if fondo:
        if len(fondo) == 2:
            graph.append(f"{''.join(fondo)}amix=inputs=2:duration=longest:normalize=0[bg]")
        else:
            graph.append(f"{fondo[0]}anull[bg]")
        graph.append("[vo]asplit=2[vo1][vo2]")
        graph.append("[bg][vo1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]")
        graph.append("[duck][vo2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
    else:
        graph.append("[vo]alimiter=limit=0.95[a]")

    cmd += [
        "-filter_complex", ";".join(graph),
        "-map", "[v]", "-map", "[a]", "-t", f"{durata:.3f}",
        "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(out),
    ]
    return cmd


def _avviso(msg: str) -> None:
    print(f"Attenzione: {msg}", file=sys.stderr)


def monta(video: Path, voce: Path, *, musica: Path | None = None, sottotitoli: bool = True,
          audio_originale: str = "abbassa", out_dir: Path | None = None) -> tuple[Path, Path | None]:
    video, voce = Path(video).resolve(), Path(voce).resolve()
    musica = Path(musica).resolve() if musica else None
    out_dir = Path(out_dir).resolve() if out_dir else video.parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / f"{video.stem}_vo.mp4"

    info_video = probe(video)
    durata_voce = probe(voce).duration
    if durata_voce + CODA_VOCE_S > info_video.duration:
        _avviso(
            f"la voce ({durata_voce:.1f}s) è più lunga del video ({info_video.duration:.1f}s): "
            "allungo il video fermando l'ultimo fotogramma."
        )

    srt_text = ""
    if sottotitoli:
        srt_text = transcript_to_srt(transcribe_words(voce))
        if not srt_text:
            _avviso("la trascrizione è vuota, monto il video senza sottotitoli.")

    with tempfile.TemporaryDirectory(prefix="monta-") as tmp:
        srt_name = None
        if srt_text:
            srt_name = "subs.srt"
            (Path(tmp) / srt_name).write_text(srt_text, encoding="utf-8")
        cmd = build_command(video, voce, out_mp4, info_video=info_video, durata_voce=durata_voce,
                            musica=musica, srt_name=srt_name, audio_originale=audio_originale)
        result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg non è riuscito a montare il video:\n{result.stderr[-2000:]}")
        out_srt = None
        if srt_name:
            out_srt = out_dir / f"{video.stem}_vo.srt"
            shutil.copyfile(Path(tmp) / srt_name, out_srt)
    return out_mp4, out_srt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="monta.py",
        description="Monta il voice-over sul video: voce sopra, musica/audio originale "
                    "abbassati quando parli, sottotitoli bruciati e .srt a parte.",
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("voce", type=Path, help="WAV generato da VoiceStudio")
    parser.add_argument("--musica", type=Path, help="musica di sottofondo (va in loop)")
    parser.add_argument("--no-sottotitoli", action="store_true", help="non generare sottotitoli")
    parser.add_argument("--togli-audio-originale", action="store_true",
                        help="elimina l'audio del video invece di abbassarlo")
    parser.add_argument("--out-dir", type=Path, help="cartella di uscita (default: <video>/../out)")
    args = parser.parse_args(argv)

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("FFmpeg non trovato. Installalo con: brew install ffmpeg", file=sys.stderr)
        return 1
    for path in (args.video, args.voce, args.musica):
        if path and not path.is_file():
            print(f"File non trovato: {path}", file=sys.stderr)
            return 1

    try:
        mp4, srt = monta(
            args.video, args.voce, musica=args.musica, sottotitoli=not args.no_sottotitoli,
            audio_originale="togli" if args.togli_audio_originale else "abbassa",
            out_dir=args.out_dir,
        )
    except VoiceStudioError as err:
        print(err, file=sys.stderr)
        print("Per montare senza sottotitoli aggiungi --no-sottotitoli.", file=sys.stderr)
        return 2
    except RuntimeError as err:
        print(err, file=sys.stderr)
        return 1

    print(f"Video: {mp4}")
    if srt:
        print(f"Sottotitoli: {srt}")
    return 0
