#!/usr/bin/env python3
"""Temp Stick (Ideal Sciences) read-only CLI.

A small command-line companion to the Temp Stick MCP server in this repo —
handy for a quick terminal check or a cron job without an MCP client.

Your API key is read from the TEMPSTICK_API_KEY environment variable and
is only ever sent to tempstickapi.com. Get your key from your Temp Stick
account: sign in at mytempstick.com, open the Account Page, choose the
Developers tab and click Show Key.

Commands:
  list-sensors            List sensors visible to the API key
  latest --sensor ID      Latest reading for one sensor
  history --sensor ID     Summarize readings from the readings endpoint
  alerts                  Show alert definitions and state
  freezer --sensor ID     latest + history + alerts for one sensor
  selftest                Offline parse test against fixture payloads

Example:
  TEMPSTICK_API_KEY=<your key> python3 tempstick.py list-sensors
"""

from __future__ import annotations

import argparse
import json
import sys

import tempstick_api as api

FIXTURE_SENSOR = {
    "type": "success",
    "data": {
        "sensor_id": "TS00TEST0000",
        "sensor_name": "Test Freezer",
        "last_temp": -20.0,
        "last_humidity": 40.5,
        "last_checkin": "2026-01-01 12:00:00",
        "offline": 0,
        "battery_pct": 99,
    },
}

FIXTURE_READINGS = {
    "type": "success",
    "data": [
        {"temp": -20.0, "reading_time": "2026-01-01 00:00:00"},
        {"temp": -15.6, "reading_time": "2026-01-01 06:00:00"},
        {"temp": -19.4, "reading_time": "2026-01-01 12:00:00"},
    ],
}


def cmd_selftest(_args) -> dict:
    summary = api.summarize_sensor(FIXTURE_SENSOR["data"])
    assert summary["last_temp_f"] == -4.0, summary
    assert summary["battery_pct"] == 99, summary
    assert summary["offline"] is False, summary
    history = api.summarize_readings(api.extract_readings(FIXTURE_READINGS["data"]))
    assert history["reading_count"] == 3, history
    assert history["temp_max_f"] == round(api.c_to_f(-15.6), 1), history
    err = {"type": "error", "message": "Invalid X-API-KEY"}
    assert err.get("type") == "error"
    return {"selftest": "PASS", "sensor_summary": summary, "history_summary": history}


def main() -> int:
    parser = argparse.ArgumentParser(description="Temp Stick read-only CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-sensors")
    p_latest = sub.add_parser("latest")
    p_latest.add_argument("--sensor", required=True)
    p_history = sub.add_parser("history")
    p_history.add_argument("--sensor", required=True)
    sub.add_parser("alerts")
    p_freezer = sub.add_parser("freezer")
    p_freezer.add_argument("--sensor", required=True)
    sub.add_parser("selftest")
    args = parser.parse_args()

    handlers = {
        "list-sensors": lambda a: api.list_sensors(),
        "latest": lambda a: api.get_sensor(a.sensor),
        "history": lambda a: api.get_readings_history(a.sensor),
        "alerts": lambda a: api.get_alerts(),
        "freezer": lambda a: api.get_freezer_status(a.sensor),
        "selftest": cmd_selftest,
    }
    try:
        result = handlers[args.command](args)
    except (api.ApiError, RuntimeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
