"""${{ values.name }}: ${{ values.description }}

Stdlib-only starter so the service runs anywhere. Swap in your framework of
choice; keep the contract the platform relies on:
  /healthz  liveness: the process is up
  /readyz   readiness: dependencies are reachable (return 503 while not)
  /metrics  Prometheus text format, scraped by the chart's ServiceMonitor
"""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE = "${{ values.name }}"
_lock = threading.Lock()
_requests: dict[tuple[str, int], int] = {}


def record(path: str, code: int) -> None:
    with _lock:
        _requests[(path, code)] = _requests.get((path, code), 0) + 1


def render_metrics() -> str:
    lines = [
        "# HELP http_requests_total Requests served, by path and status code.",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        for (path, code), count in sorted(_requests.items()):
            lines.append(f'http_requests_total{{job="{SERVICE}",path="{path}",code="{code}"}} {count}')
    return "\n".join(lines) + "\n"


def ready() -> bool:
    """Replace with real dependency checks (DB ping, downstream health)."""
    return True


class Handler(BaseHTTPRequestHandler):
    server_version = SERVICE

    def _send(self, code: int, body: str, content_type: str = "application/json") -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        if self.path != "/metrics":
            record(self.path, code)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send(200, '{"status":"ok"}')
        elif self.path == "/readyz":
            ok = ready()
            self._send(200 if ok else 503, json.dumps({"ready": ok}))
        elif self.path == "/metrics":
            self._send(200, render_metrics(), "text/plain; version=0.0.4")
        elif self.path == "/":
            self._send(200, json.dumps({"service": SERVICE}))
        else:
            self._send(404, '{"error":"not found"}')

    def log_message(self, fmt: str, *args) -> None:  # structured one-line access log
        print(json.dumps({"service": SERVICE, "client": self.client_address[0], "msg": fmt % args}), flush=True)


def serve(port: int | None = None) -> ThreadingHTTPServer:
    port = int(os.environ.get("PORT", "8080")) if port is None else port
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)  # noqa: S104 - container listens on all interfaces


if __name__ == "__main__":
    srv = serve()
    print(json.dumps({"service": SERVICE, "msg": f"listening on :{srv.server_address[1]}"}), flush=True)
    srv.serve_forever()
