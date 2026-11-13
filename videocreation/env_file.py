"""Aggiorna il file env del backend VoiceStudio (`~/.config/omnivoice/env`).

Il backend lo legge all'avvio: dopo una modifica va riavviata l'app. Il formato
e la codifica dei valori sono gli stessi di VoiceStudio (backend/core/user_env.py),
così il file resta leggibile anche dalle impostazioni dell'app.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

DEFAULT_ENV_PATH = Path.home() / ".config" / "omnivoice" / "env"

_PLAIN_VALUE = re.compile(r"^[A-Za-z0-9_\-./:@%+=,~]*$")


def _encode_value(value: str) -> str:
    if re.search(r"[\0\r\n]", value):
        raise ValueError("il valore non può contenere a capo o caratteri NUL")
    if _PLAIN_VALUE.match(value):
        return value
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def upsert_env(path: Path, values: dict[str, str]) -> None:
    """Imposta le chiavi date preservando tutte le altre righe e il loro ordine."""
    path = Path(path)
    encoded = {key: _encode_value(value) for key, value in values.items()}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []

    pending = dict(encoded)
    for i, line in enumerate(lines):
        for key in list(pending):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={pending.pop(key)}"
                break
    lines.extend(f"{key}={value}" for key, value in pending.items())

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".env-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
