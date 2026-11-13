#!/usr/bin/env python3
"""Monta voce, musica e sottotitoli su un video. Uso: python scripts/monta.py --help"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from videocreation.montaggio import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
