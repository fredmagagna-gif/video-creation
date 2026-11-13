#!/usr/bin/env python3
"""Configura VoiceStudio per questo repo.

Scrive nel file env del backend (`~/.config/omnivoice/env`):
  OMNIVOICE_MCP_OUTPUT_MODE=files       -> l'audio generato resta su disco, non in chat
  OMNIVOICE_MCP_BASE_PATH=<repo>/progetti -> unica cartella che VoiceStudio può leggere/scrivere
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from videocreation.env_file import DEFAULT_ENV_PATH, upsert_env  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_PATH,
                        help=f"file env di VoiceStudio (default: {DEFAULT_ENV_PATH})")
    args = parser.parse_args(argv)

    progetti = REPO / "progetti"
    progetti.mkdir(exist_ok=True)
    upsert_env(args.env_file, {
        "OMNIVOICE_MCP_OUTPUT_MODE": "files",
        "OMNIVOICE_MCP_BASE_PATH": str(progetti),
    })

    print(f"Configurazione scritta in {args.env_file}")
    print(f"  OMNIVOICE_MCP_OUTPUT_MODE=files")
    print(f"  OMNIVOICE_MCP_BASE_PATH={progetti}")
    print()
    print("Prossimi passi:")
    print("  1. Chiudi e riapri VoiceStudio (il backend legge il file all'avvio).")
    print(f"  2. Apri Claude Code in {REPO} e approva il server MCP 'voicestudio'.")
    print("  3. Chiedi a Claude: \"clona la mia voce\" (una volta sola).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
