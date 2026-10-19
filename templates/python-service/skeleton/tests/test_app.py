import json
import threading
import urllib.error
import urllib.request

import pytest

from app import main


@pytest.fixture(scope="module")
def base_url():
    srv = main.serve(port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_healthz(base_url):
    assert get(base_url + "/healthz") == (200, '{"status":"ok"}')


def test_readyz(base_url):
    code, body = get(base_url + "/readyz")
    assert code == 200 and json.loads(body)["ready"] is True


def test_not_ready_returns_503(base_url, monkeypatch):
    monkeypatch.setattr(main, "ready", lambda: False)
    assert get(base_url + "/readyz")[0] == 503


def test_metrics_count_requests(base_url):
    get(base_url + "/")
    get(base_url + "/nope")
    code, body = get(base_url + "/metrics")
    assert code == 200
    assert f'job="{main.SERVICE}",path="/",code="200"' in body
    assert 'path="/nope",code="404"' in body
