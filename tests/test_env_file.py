import stat

import pytest

from videocreation.env_file import upsert_env


def test_creates_file_with_0600(tmp_path):
    path = tmp_path / "omnivoice" / "env"
    upsert_env(path, {"OMNIVOICE_MCP_OUTPUT_MODE": "files"})
    assert path.read_text() == "OMNIVOICE_MCP_OUTPUT_MODE=files\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_preserves_other_keys_and_replaces_existing(tmp_path):
    path = tmp_path / "env"
    path.write_text("HF_TOKEN=abc\nOMNIVOICE_MCP_OUTPUT_MODE=resources\n# nota\n")
    upsert_env(path, {"OMNIVOICE_MCP_OUTPUT_MODE": "files"})
    assert path.read_text().splitlines() == [
        "HF_TOKEN=abc",
        "OMNIVOICE_MCP_OUTPUT_MODE=files",
        "# nota",
    ]


def test_appends_new_keys(tmp_path):
    path = tmp_path / "env"
    path.write_text("HF_TOKEN=abc\n")
    upsert_env(path, {"A": "1", "B": "2"})
    assert path.read_text().splitlines() == ["HF_TOKEN=abc", "A=1", "B=2"]


def test_quotes_paths_with_spaces_and_apostrophes(tmp_path):
    path = tmp_path / "env"
    upsert_env(path, {"OMNIVOICE_MCP_BASE_PATH": "/Users/fred/Video Lavoro/l'estate"})
    assert path.read_text() == (
        "OMNIVOICE_MCP_BASE_PATH='/Users/fred/Video Lavoro/l\\'estate'\n"
    )


def test_rejects_newlines(tmp_path):
    with pytest.raises(ValueError):
        upsert_env(tmp_path / "env", {"X": "a\nb"})
