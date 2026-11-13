import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from videocreation.voicestudio import VoiceStudioError, transcribe_words

RESPONSE = {"text": "ciao", "segments": [], "words": [{"word": "ciao", "start": 0, "end": 0.5}]}


@pytest.fixture
def server():
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        status = 200

        def do_POST(self):
            length = int(self.headers["Content-Length"])
            seen["path"] = self.path
            seen["headers"] = dict(self.headers)
            seen["body"] = self.rfile.read(length)
            body = json.dumps(seen.get("reply", RESPONSE)).encode()
            self.send_response(seen.get("status", 200))
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    seen["url"] = f"http://127.0.0.1:{httpd.server_port}"
    yield seen
    httpd.shutdown()


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / "voce di prova.wav"
    path.write_bytes(b"RIFF....WAVEfake")
    return path


def test_sends_multipart_with_word_granularity(server, audio):
    result = transcribe_words(audio, base_url=server["url"], language="it")
    assert result == RESPONSE
    assert server["path"] == "/v1/audio/transcriptions"
    assert server["headers"]["Content-Type"].startswith("multipart/form-data; boundary=")
    body = server["body"]
    assert b'name="response_format"\r\n\r\nverbose_json\r\n' in body
    assert b'name="timestamp_granularities[]"\r\n\r\nword\r\n' in body
    assert b'name="timestamp_granularities[]"\r\n\r\nsegment\r\n' in body
    assert b'name="language"\r\n\r\nit\r\n' in body
    assert b'filename="voce di prova.wav"' in body
    assert b"RIFF....WAVEfake" in body
    assert "Authorization" not in server["headers"]


def test_bearer_when_api_key(server, audio):
    transcribe_words(audio, base_url=server["url"], api_key="k")
    assert server["headers"]["Authorization"] == "Bearer k"


def test_connection_refused_message(audio):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    with pytest.raises(VoiceStudioError, match="Apri VoiceStudio"):
        transcribe_words(audio, base_url=f"http://127.0.0.1:{port}")


def test_409_asr_missing_message(server, audio):
    server["status"] = 409
    server["reply"] = {"detail": {"message": "no ASR"}}
    with pytest.raises(VoiceStudioError, match="modello di trascrizione"):
        transcribe_words(audio, base_url=server["url"])


def test_other_http_error_message(server, audio):
    server["status"] = 500
    server["reply"] = {"error": {"message": "boom"}}
    with pytest.raises(VoiceStudioError, match="500"):
        transcribe_words(audio, base_url=server["url"])
