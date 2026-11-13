import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_mcp_json_valid():
    config = json.loads((ROOT / ".mcp.json").read_text())
    server = config["mcpServers"]["voicestudio"]
    assert server["url"] == "http://localhost:3900/mcp/"
    assert server["headers"]["X-OmniVoice-Client-Id"] == "video-creation"


def test_skills_have_frontmatter():
    skills = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    assert {p.parent.name for p in skills} == {"voce-clonata", "voiceover"}
    for path in skills:
        text = path.read_text()
        assert text.startswith("---\n")
        header = text.split("---\n")[1]
        assert f"name: {path.parent.name}\n" in header
        assert "description:" in header


def test_readme_mentions_setup():
    readme = (ROOT / "README.md").read_text()
    assert "setup_voicestudio.py" in readme
    assert "monta.py" in readme
    assert (ROOT / "docs" / "doppiaggio.md").exists()


def test_docs_require_ffmpeg_full_and_mention_srt_override():
    readme = (ROOT / "README.md").read_text()
    skill = (ROOT / ".claude" / "skills" / "voiceover" / "SKILL.md").read_text()
    assert "brew install ffmpeg-full" in readme
    assert "brew install ffmpeg\n" not in readme and "brew install ffmpeg`" not in readme
    assert "--srt" in readme and "--srt" in skill
