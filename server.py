"""Local HTTP server and Ollama adapter for QuoteForge."""

from __future__ import annotations

import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).parent
STATIC = ROOT / "static"
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
HOST = os.environ.get("APP_HOST", "127.0.0.1")
PORT = int(os.environ.get("APP_PORT", "8000"))


def draft_proposal(payload: dict) -> dict:
    client = str(payload.get("client", "")).strip()[:100]
    service = str(payload.get("service", "")).strip()[:100]
    brief = str(payload.get("brief", "")).strip()[:3000]
    currency = str(payload.get("currency", "USD")).strip()[:8]
    if not client or not service or not brief:
        raise ValueError("Add a client, service, and project brief first.")
    if currency not in {"USD", "INR", "EUR", "GBP", "CAD", "AUD"}:
        raise ValueError("Choose a supported currency.")

    try:
        rate = float(payload.get("rate", 0))
        hours = float(payload.get("hours", 0))
        expenses = float(payload.get("expenses", 0))
    except (TypeError, ValueError):
        raise ValueError("Rate, hours, and expenses must be valid numbers.") from None
    if not all(math.isfinite(number) and number >= 0 for number in (rate, hours, expenses)):
        raise ValueError("Rate, hours, and expenses must be finite, non-negative numbers.")
    if rate > 1_000_000 or expenses > 1_000_000 or hours > 100_000:
        raise ValueError("The estimate is above the supported limit.")

    total = round(rate * hours + expenses, 2)
    prompt = f"""Write a concise, warm freelance project proposal using only the facts below.
Do not invent experience, credentials, dates, deliverables, guarantees, client facts, or terms.
If something important is missing, write [confirm with client]. Keep the language specific and plain.
Include: a short opening, understanding of the work, proposed approach, scope boundaries,
timeline as [confirm with client], price summary, payment/approval next step, and one useful question.
The freelancer must review the draft before sending it.

Client: {client}
Service: {service}
Project brief: {brief}
Rate: {rate:g} {currency}/hour
Estimated hours: {hours:g}
Additional expenses: {expenses:g} {currency}
Calculated estimate (fixed arithmetic, do not change): {total:g} {currency}
"""
    request = Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 600},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            result = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Could not reach local Ollama ({MODEL}). Start the app with Docker Compose "
            "and wait for the model download to finish."
        ) from error

    return {
        "proposal": str(result.get("response", "")).strip(),
        "currency": currency,
        "rate": rate,
        "hours": hours,
        "expenses": expenses,
        "total": total,
        "model": MODEL,
    }


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        files = {
            "/": (STATIC / "index.html", "text/html; charset=utf-8"),
            "/styles.css": (STATIC / "styles.css", "text/css; charset=utf-8"),
            "/app.js": (STATIC / "app.js", "text/javascript; charset=utf-8"),
        }
        item = files.get(self.path)
        if item is None:
            self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
            return
        path, content_type = item
        self.send_bytes(path.read_bytes(), content_type)

    def do_POST(self) -> None:
        if self.path != "/api/draft":
            self.send_bytes(b'{"error":"Not found"}', "application/json", 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 10_000:
                raise ValueError("Request must be between 1 byte and 10 KB.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object.")
            result = draft_proposal(payload)
            body = json.dumps(result).encode("utf-8")
            self.send_bytes(body, "application/json; charset=utf-8")
        except ValueError as error:
            body = json.dumps({"error": str(error)}).encode("utf-8")
            self.send_bytes(body, "application/json; charset=utf-8", 400)
        except RuntimeError as error:
            body = json.dumps({"error": str(error)}).encode("utf-8")
            self.send_bytes(body, "application/json; charset=utf-8", 503)

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    print(f"QuoteForge ready at http://127.0.0.1:{PORT} (model: {MODEL})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
