"""Client minimo (solo libreria standard) per l'API locale di VoiceStudio."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:3900"


class VoiceStudioError(Exception):
    """Errore con un messaggio già pronto per l'utente."""


def _multipart(fields: list[tuple[str, str]], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )
    filename = file_path.name.replace('"', "_")
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
        f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
        + file_path.read_bytes()
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def transcribe_words(audio: Path, base_url: str | None = None, language: str | None = None,
                     api_key: str | None = None, timeout: float = 600) -> dict:
    """Trascrive `audio` e restituisce la risposta `verbose_json` con tempi per parola."""
    base_url = (base_url or os.environ.get("VOICESTUDIO_URL") or DEFAULT_URL).rstrip("/")
    api_key = api_key or os.environ.get("OMNIVOICE_API_KEY")
    fields = [
        ("response_format", "verbose_json"),
        ("timestamp_granularities[]", "word"),
        ("timestamp_granularities[]", "segment"),
    ]
    if language:
        fields.append(("language", language))
    body, content_type = _multipart(fields, "file", Path(audio))
    request = urllib.request.Request(
        f"{base_url}/v1/audio/transcriptions", data=body, method="POST",
        headers={"Content-Type": content_type},
    )
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as err:
        if err.code == 409:
            raise VoiceStudioError(
                "VoiceStudio non ha un modello di trascrizione installato: "
                "aprilo e scaricane uno (es. Whisper) dal Model Manager."
            ) from err
        if err.code in (401, 403):
            raise VoiceStudioError(
                "VoiceStudio ha rifiutato la richiesta: imposta OMNIVOICE_API_KEY "
                "con la chiave dell'app."
            ) from err
        detail = err.read().decode("utf-8", "replace")[:300]
        raise VoiceStudioError(f"Errore {err.code} da VoiceStudio durante la trascrizione: {detail}") from err
    except (urllib.error.URLError, ConnectionError, TimeoutError) as err:
        raise VoiceStudioError(
            f"Non riesco a raggiungere VoiceStudio su {base_url}. "
            "Apri VoiceStudio e riprova."
        ) from err
