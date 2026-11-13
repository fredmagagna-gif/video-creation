"""Sottotitoli brevi, in stile social, dalla trascrizione di VoiceStudio."""
from __future__ import annotations


def _timestamp(seconds: float) -> str:
    ms = max(0, round(float(seconds) * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _render(cues: list[tuple[float, float, str]]) -> str:
    blocks = [
        f"{i}\n{_timestamp(start)} --> {_timestamp(end)}\n{text}"
        for i, (start, end, text) in enumerate(cues, 1)
    ]
    return "\n\n".join(blocks) + "\n" if blocks else ""


def words_to_srt(words: list[dict], max_words: int = 4, max_chars: int = 28,
                 max_gap: float = 0.6) -> str:
    """Raggruppa le parole in cue brevi: nuova cue a `max_words` parole,
    oltre `max_chars` caratteri o dopo una pausa più lunga di `max_gap` secondi."""
    cues: list[tuple[float, float, str]] = []
    current: list[dict] = []

    def flush() -> None:
        if current:
            text = " ".join(w["text"] for w in current)
            cues.append((current[0]["start"], current[-1]["end"], text))
            current.clear()

    for word in words:
        text = str(word.get("word", word.get("text", ""))).strip()
        if not text:
            continue
        item = {"text": text, "start": float(word["start"]), "end": float(word["end"])}
        if current:
            length = len(" ".join(w["text"] for w in current)) + 1 + len(text)
            if (len(current) >= max_words or length > max_chars
                    or item["start"] - current[-1]["end"] > max_gap):
                flush()
        current.append(item)
    flush()
    return _render(cues)


def transcript_to_srt(result: dict) -> str:
    """SRT dalla risposta `verbose_json`: parole se ci sono, altrimenti segmenti."""
    if result.get("words"):
        return words_to_srt(result["words"])
    cues = [
        (float(seg["start"]), float(seg["end"]), str(seg.get("text", "")).strip())
        for seg in result.get("segments") or []
    ]
    return _render([cue for cue in cues if cue[2]])
