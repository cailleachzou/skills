"""Unit tests for ocr_client (UMI-OCR HTTP wrapper)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from scripts.ocr_client import OCRClient, OCRUnavailable


@pytest.fixture
def client():
    return OCRClient(host="127.0.0.1", port=1224, exe_path="C:/fake/Umi-OCR.exe")


def test_ping_returns_true_when_service_alive(client):
    with patch.object(client, "_http_get", return_value="pong"):
        assert client.ping() is True


def test_ping_raises_when_connection_refused(client):
    with patch.object(client, "_http_get", side_effect=OCRUnavailable("refused")):
        with pytest.raises(OCRUnavailable):
            client.ping()


def test_recognize_image_returns_text_on_success(client, tmp_path):
    img = tmp_path / "test.png"
    # Minimal valid 1x1 PNG
    img.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
        b"\xff?\x00\x05\xfe\x02\xfe\xa3W\xbd\xe0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    fake_resp = {"code": 100, "data": "识别结果"}
    with patch.object(client, "_http_post_json", return_value=fake_resp):
        result = client.recognize_image(str(img))
        assert result == "识别结果"


def test_recognize_image_raises_on_error_code(client, tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"not a real png")
    with patch.object(client, "_http_post_json", return_value={"code": 200, "data": "bad"}):
        with pytest.raises(OCRUnavailable):
            client.recognize_image(str(img))


def test_ensure_running_starts_exe_if_down(client):
    with patch.object(client, "ping", side_effect=[OCRUnavailable("down"), True]):
        with patch("scripts.ocr_client.os.path.exists", return_value=True):
            with patch("scripts.ocr_client.subprocess.Popen") as mock_popen:
                with patch("scripts.ocr_client.time.sleep"):
                    assert client.ensure_running() is True
                    mock_popen.assert_called_once()
                    args = mock_popen.call_args[0][0]
                    assert args[0] == client.exe_path
