"""UMI-OCR HTTP API client.

Wraps the offline Umi-OCR engine (Rapid v2.1.5+) at http://127.0.0.1:1224.
Provides ping/ensure-running/recognize_image with graceful error handling.
"""
import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1224
DEFAULT_EXE = r"C:\Users\59620\Downloads\Programs\Umi-OCR_Rapid_v2.1.5\Umi-OCR.exe"
PING_PATH = "/umiocr"
OCR_PATH = "/api/ocr"
STARTUP_WAIT_SEC = 5


class OCRUnavailable(Exception):
    """Raised when Umi-OCR service cannot be reached."""


class OCRClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, exe_path=DEFAULT_EXE, timeout=10):
        self.host = host
        self.port = port
        self.exe_path = exe_path
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"

    def _http_get(self, path):
        req = urllib.request.Request(self.base_url + path)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def _http_post_json(self, path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def ping(self):
        """Return True if service responds. Raise OCRUnavailable if not."""
        try:
            self._http_get(PING_PATH)
            return True
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            raise OCRUnavailable(f"Umi-OCR not reachable at {self.base_url}: {e}")

    def ensure_running(self):
        """Ping; if down, start the exe and re-ping after wait. Return True if up."""
        try:
            self.ping()
            return True
        except OCRUnavailable:
            pass
        if not os.path.exists(self.exe_path):
            raise OCRUnavailable(f"Umi-OCR exe not found at {self.exe_path}")
        # Start the exe detached
        subprocess.Popen(
            [self.exe_path],
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
            close_fds=False,
        )
        time.sleep(STARTUP_WAIT_SEC)
        try:
            self.ping()
            return True
        except OCRUnavailable as e:
            raise OCRUnavailable(f"Umi-OCR started but did not respond: {e}")

    def recognize_image(self, image_path, language="简体中文"):
        """Run OCR on a local image file. Return extracted text (may be empty)."""
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        payload = {
            "base64": b64,
            "options": {
                "ocr.language": language,
                "tbpu.parser": "multi_para",
                "data.format": "text",
            },
        }
        resp = self._http_post_json(OCR_PATH, payload)
        if resp.get("code") != 100:
            raise OCRUnavailable(f"OCR error: {resp.get('data')}")
        return (resp.get("data") or "").strip()
