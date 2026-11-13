import re
import shutil
import subprocess

import pytest

from videocreation import montaggio
from videocreation.media import probe
from videocreation.montaggio import build_command, main, monta
from videocreation.voicestudio import VoiceStudioError

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg non installato")

WORDS = {"words": [
    {"word": "Ciao", "start": 0.1, "end": 0.5},
    {"word": "a", "start": 0.5, "end": 0.7},
    {"word": "tutti", "start": 0.7, "end": 1.2},
]}


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


@pytest.fixture(scope="module")
def clips(tmp_path_factory):
    d = tmp_path_factory.mktemp("clips")
    c = {
        "video": d / "video.mp4",
        "muto": d / "muto.mp4",
        "voce2": d / "voce2.wav",
        "voce5": d / "voce5.wav",
        "musica1": d / "musica1.wav",
    }
    _ff("-f", "lavfi", "-i", "testsrc=size=360x640:rate=25:duration=3",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(c["video"]))
    _ff("-f", "lavfi", "-i", "testsrc=size=360x640:rate=25:duration=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(c["muto"]))
    _ff("-f", "lavfi", "-i", "sine=frequency=880:duration=2", str(c["voce2"]))
    _ff("-f", "lavfi", "-i", "sine=frequency=880:duration=5", str(c["voce5"]))
    _ff("-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(c["musica1"]))
    return c


@pytest.fixture(autouse=True)
def fake_transcription(monkeypatch):
    monkeypatch.setattr(montaggio, "transcribe_words", lambda *a, **k: WORDS)


def _work(tmp_path, clips, *names):
    out = []
    for name in names:
        dest = tmp_path / clips[name].name
        shutil.copy(clips[name], dest)
        out.append(dest)
    return out


def _mean_volume(path, start, length):
    res = subprocess.run(
        ["ffmpeg", "-ss", str(start), "-t", str(length), "-i", str(path),
         "-af", "volumedetect", "-vn", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", res.stderr)
    return float(m.group(1)) if m else float("-inf")


def test_probe_detects_audio_and_size(clips):
    info = probe(clips["video"])
    assert info.has_audio is True
    assert (info.width, info.height) == (360, 640)
    assert info.duration == pytest.approx(3.0, abs=0.1)
    assert probe(clips["muto"]).has_audio is False
    assert probe(clips["voce2"]).duration == pytest.approx(2.0, abs=0.05)


def test_basic_mix_with_subtitles(tmp_path, clips):
    video, voce = _work(tmp_path, clips, "video", "voce2")
    mp4, srt = monta(video, voce)
    assert mp4 == tmp_path / "out" / "video_vo.mp4"
    info = probe(mp4)
    assert info.has_audio
    assert info.duration == pytest.approx(3.0, abs=0.2)
    assert srt == tmp_path / "out" / "video_vo.srt"
    assert "Ciao a tutti" in srt.read_text()


def test_silent_video(tmp_path, clips):
    video, voce = _work(tmp_path, clips, "muto", "voce2")
    mp4, _ = monta(video, voce)
    assert probe(mp4).has_audio
    assert _mean_volume(mp4, 0.5, 1.0) > -40


def test_voice_longer_than_video(tmp_path, clips, capsys):
    video, voce = _work(tmp_path, clips, "video", "voce5")
    mp4, _ = monta(video, voce)
    assert probe(mp4).duration == pytest.approx(5.5, abs=0.2)
    assert "più lunga del video" in capsys.readouterr().err


def test_odd_paths(tmp_path, clips):
    folder = tmp_path / "l'estate è qui"
    folder.mkdir()
    video = folder / "clip 1.mp4"
    voce = folder / "voce, prova.wav"
    shutil.copy(clips["video"], video)
    shutil.copy(clips["voce2"], voce)
    mp4, srt = monta(video, voce)
    assert mp4.exists() and probe(mp4).duration > 2.5
    assert srt is not None and srt.exists()


def test_short_music_loops(tmp_path, clips):
    video, voce, musica = _work(tmp_path, clips, "muto", "voce2", "musica1")
    mp4, _ = monta(video, voce, musica=musica)
    assert probe(mp4).duration == pytest.approx(3.0, abs=0.2)
    assert _mean_volume(mp4, 2.5, 0.4) > -60


def test_no_subtitles(tmp_path, clips, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("non deve trascrivere")
    monkeypatch.setattr(montaggio, "transcribe_words", boom)
    video, voce = _work(tmp_path, clips, "video", "voce2")
    mp4, srt = monta(video, voce, sottotitoli=False)
    assert mp4.exists() and srt is None


def test_empty_transcription_skips_subtitles(tmp_path, clips, monkeypatch, capsys):
    monkeypatch.setattr(montaggio, "transcribe_words", lambda *a, **k: {"text": ""})
    video, voce = _work(tmp_path, clips, "video", "voce2")
    mp4, srt = monta(video, voce)
    assert mp4.exists() and srt is None
    assert "sottotitoli" in capsys.readouterr().err


def test_togli_audio_originale(clips, tmp_path):
    info = probe(clips["video"])
    keep = build_command(clips["video"], clips["voce2"], tmp_path / "o.mp4",
                         info_video=info, durata_voce=2.0)
    drop = build_command(clips["video"], clips["voce2"], tmp_path / "o.mp4",
                         info_video=info, durata_voce=2.0, audio_originale="togli")
    graph = lambda cmd: cmd[cmd.index("-filter_complex") + 1]
    assert "[0:a]" in graph(keep)
    assert "[0:a]" not in graph(drop)


def test_cli_voicestudio_down(tmp_path, clips, monkeypatch, capsys):
    def down(*a, **k):
        raise VoiceStudioError("Non riesco a raggiungere VoiceStudio. Apri VoiceStudio e riprova.")
    monkeypatch.setattr(montaggio, "transcribe_words", down)
    video, voce = _work(tmp_path, clips, "video", "voce2")
    assert main([str(video), str(voce)]) == 2
    err = capsys.readouterr().err
    assert "Apri VoiceStudio" in err and "--no-sottotitoli" in err


def test_cli_success_prints_paths(tmp_path, clips, capsys):
    video, voce = _work(tmp_path, clips, "video", "voce2")
    assert main([str(video), str(voce), "--togli-audio-originale"]) == 0
    assert "video_vo.mp4" in capsys.readouterr().out
