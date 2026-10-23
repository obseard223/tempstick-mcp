#!/usr/bin/env python3
"""Offline selftest for tempstick-mcp. No network, no real API key.

Runs three layers of checks:
  1. Fixture parsing checks (unit level, shared with the CLI selftest).
  2. A stub Temp Stick API on 127.0.0.1 that enforces the X-API-KEY
     header and answers with the documented envelope shapes.
  3. A real end-to-end drive of server.py over stdio: initialize,
     tools/list, and a tools/call for every tool, plus the bad-key
     error path.

Run:  python3 selftest.py     (exit code 0 and a PASS line on success)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tempstick_api as api  # noqa: E402
from tempstick import cmd_selftest, FIXTURE_SENSOR, FIXTURE_READINGS  # noqa: E402

TEST_KEY = "TESTKEY123"
SENSOR_ID = FIXTURE_SENSOR["data"]["sensor_id"]

FIXTURE_SENSORS = {"type": "success", "data": [FIXTURE_SENSOR["data"]]}
FIXTURE_ALERTS = {
    "type": "success",
    "data": [
        {
            "alert_id": 1,
            "name": "High temperature",
            "type": "temperature_above",
            "threshold_f": 15,
            "triggered": False,
        }
    ],
}
ROUTES = {
    "/api/v1/sensors": FIXTURE_SENSORS,
    f"/api/v1/sensor/{SENSOR_ID}": FIXTURE_SENSOR,
    f"/api/v1/sensor/{SENSOR_ID}/readings": FIXTURE_READINGS,
    "/api/v1/alerts": FIXTURE_ALERTS,
}


class StubHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (http.server naming)
        if self.headers.get("X-API-KEY") != TEST_KEY:
            body = {"type": "error", "message": "Invalid X-API-KEY"}
        elif self.path in ROUTES:
            body = ROUTES[self.path]
        else:
            body = {"type": "error", "message": "Unknown endpoint"}
        raw = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep the test output clean
        pass


def drive_server(env_extra, calls):
    """Spawn server.py, run a JSON-RPC conversation, return responses by id."""
    env = dict(os.environ)
    env.update(env_extra)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "server.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        env=env,
    )
    lines = []
    msg_id = 0

    def send(obj):
        proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
        proc.stdin.flush()

    def request(method, params=None):
        nonlocal msg_id
        msg_id += 1
        send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})
        while True:
            line = proc.stdout.readline()
            assert line, f"server closed stdout waiting for {method}"
            resp = json.loads(line.decode("utf-8"))
            if resp.get("id") == msg_id:
                return resp

    init = request("initialize", {"protocolVersion": "2025-03-26"})
    assert init["result"]["serverInfo"]["name"] == "tempstick-mcp", init
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    listing = request("tools/list")
    names = [t["name"] for t in listing["result"]["tools"]]
    for expected in ("list_sensors", "get_sensor", "get_freezer_status",
                     "get_readings_history", "get_alerts"):
        assert expected in names, names
    results = {}
    for label, tool, args in calls:
        resp = request("tools/call", {"name": tool, "arguments": args})
        results[label] = resp["result"]
    proc.stdin.close()
    proc.wait(timeout=10)
    return results


def main() -> int:
    # 1. Fixture/unit layer (also exposed as `tempstick.py selftest`).
    unit = cmd_selftest(None)
    assert unit["selftest"] == "PASS", unit
    print("unit fixtures: PASS")

    # 2 + 3. Stub API + full stdio drive of the MCP server.
    stub = HTTPServer(("127.0.0.1", 0), StubHandler)
    port = stub.server_address[1]
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}/api/v1"
    try:
        calls = [
            ("list_sensors", "list_sensors", {}),
            ("get_sensor", "get_sensor", {"sensor_id": SENSOR_ID}),
            ("get_freezer_status", "get_freezer_status", {"sensor_id": SENSOR_ID}),
            ("get_readings_history", "get_readings_history", {"sensor_id": SENSOR_ID}),
            ("get_alerts", "get_alerts", {}),
        ]
        results = drive_server(
            {"TEMPSTICK_API_KEY": TEST_KEY, "TEMPSTICK_API_BASE": base}, calls
        )
        for label, _tool, _args in calls:
            assert results[label]["isError"] is False, (label, results[label])
        sensor_text = results["get_sensor"]["content"][0]["text"]
        assert '"last_temp_f": -4.0' in sensor_text, sensor_text
        status = json.loads(results["get_freezer_status"]["content"][0]["text"])
        assert status["latest"]["battery_pct"] == 99, status
        assert status["alerts"]["count"] == 1, status
        print("mcp stdio end-to-end (stub API): PASS")

        # Bad key: the API's error envelope must surface as a tool error.
        bad = drive_server(
            {"TEMPSTICK_API_KEY": "WRONGKEY", "TEMPSTICK_API_BASE": base},
            [("list_sensors", "list_sensors", {})],
        )
        assert bad["list_sensors"]["isError"] is True, bad
        assert "Invalid X-API-KEY" in bad["list_sensors"]["content"][0]["text"], bad
        print("bad-key error envelope: PASS")
    finally:
        stub.shutdown()

    print("SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
