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


def _norm(token: str) -> str:
    return "".join(ch for ch in str(token).lower() if ch.isalnum())


def _interpolate(seg: dict) -> list[dict]:
    """Tempi stimati per le parole del segmento, proporzionali alla lunghezza."""
    tokens = str(seg.get("text", "")).split()
    start, end = float(seg["start"]), float(seg["end"])
    weights = [len(t) + 1 for t in tokens]
    total = sum(weights) or 1
    out, t = [], start
    for token, weight in zip(tokens, weights):
        step = (end - start) * weight / total
        out.append({"word": token, "start": t, "end": t + step})
        t += step
    if out:
        out[-1]["end"] = end
    return out


def transcript_to_srt(result: dict) -> str:
    """SRT dalla risposta `verbose_json`.

    Il testo dei segmenti fa fede. Per ogni segmento si usano i tempi delle singole
    parole quando coincidono col testo; se mancano parole (VoiceStudio scarta i token
    senza tempi, tipicamente numeri e simboli) i tempi vengono stimati sul segmento.
    """
    words = [w for w in result.get("words") or [] if str(w.get("word", "")).strip()]
    segments = [s for s in result.get("segments") or [] if str(s.get("text", "")).strip()]
    if not segments:
        return words_to_srt(words)

    timed: list[dict] = []
    for seg in segments:
        start, end = float(seg["start"]) - 0.05, float(seg["end"]) + 0.05
        inside = [w for w in words if float(w["start"]) >= start and float(w["end"]) <= end]
        tokens = str(seg["text"]).split()
        if [_norm(w["word"]) for w in inside] == [_norm(t) for t in tokens]:
            timed.extend({**w, "word": token} for w, token in zip(inside, tokens))
        else:
            timed.extend(_interpolate(seg))
    return words_to_srt(timed)
