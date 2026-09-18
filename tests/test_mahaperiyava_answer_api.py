#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from http.server import ThreadingHTTPServer
from product.http_server import Handler

srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
port = srv.server_address[1]
thread = threading.Thread(target=srv.serve_forever, daemon=True)
thread.start()

try:
    payload = json.dumps({
        "query": "What does Mahaperiyava say about Kamakshi and compassion?"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/mahaperiyava/answer",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        out = json.load(response)
        assert out["answerable"] is True
        assert out["status"] == "grounded_answer_packet"
        assert out["claims"]

    payload = json.dumps({
        "query": "What did Mahaperiyava say about smartphone push notifications?"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/mahaperiyava/answer",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        out = json.load(response)
        assert out["answerable"] is False
        assert out["status"] == "insufficient_evidence"
finally:
    srv.shutdown()

print("mahaperiyava-answer-api: PASS")
