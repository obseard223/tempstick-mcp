#!/usr/bin/env python3
"""Temp Stick MCP server.

Exposes Temp Stick (Ideal Sciences) WiFi temperature/humidity sensors to
any MCP client (Claude Desktop, Claude Code, Cursor, ...) over stdio,
using only the Python standard library — no dependencies to install.

Your API key is read from the TEMPSTICK_API_KEY environment variable and
is only ever sent to tempstickapi.com. Get your key from your Temp Stick
account: sign in at mytempstick.com, open the Account Page, choose the
Developers tab and click Show Key.

Run:  TEMPSTICK_API_KEY=<your key> python3 server.py
"""

from __future__ import annotations

import json
import sys

import tempstick_api as api

SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "tempstick-mcp", "version": "0.1.0"}

TOOLS = [
    {
        "name": "list_sensors",
        "description": "List the Temp Stick sensors visible to your API key, "
                       "with each sensor's latest temperature, humidity, "
                       "battery level and offline status.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_sensor",
        "description": "Get the latest reading for one sensor: temperature "
                       "(Celsius and Fahrenheit), humidity, last check-in, "
                       "battery level and offline status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sensor_id": {
                    "type": "string",
                    "description": "Sensor ID, as returned by list_sensors.",
                }
            },
            "required": ["sensor_id"],
        },
    },
    {
        "name": "get_freezer_status",
        "description": "One-call status check for a sensor (named for the "
                       "classic freezer use case): latest reading, recent "
                       "history summary and the account's alert definitions "
                       "together, so the assistant can answer 'is it OK?' "
                       "in a single call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sensor_id": {
                    "type": "string",
                    "description": "Sensor ID, as returned by list_sensors.",
                }
            },
            "required": ["sensor_id"],
        },
    },
    {
        "name": "get_readings_history",
        "description": "Summarize a sensor's recent readings: count, min, "
                       "max and average temperature (Fahrenheit), and the "
                       "first and last reading times.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sensor_id": {
                    "type": "string",
                    "description": "Sensor ID, as returned by list_sensors.",
                }
            },
            "required": ["sensor_id"],
        },
    },
    {
        "name": "get_alerts",
        "description": "List the alert definitions and state for the account "
                       "(thresholds, delivery channels, whether triggered).",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def call_tool(name: str, arguments: dict):
    if name == "list_sensors":
        return api.list_sensors()
    if name == "get_sensor":
        return api.get_sensor(_sensor_id(arguments))
    if name == "get_freezer_status":
        return api.get_freezer_status(_sensor_id(arguments))
    if name == "get_readings_history":
        return api.get_readings_history(_sensor_id(arguments))
    if name == "get_alerts":
        return api.get_alerts()
    raise api.ApiError(f"unknown tool: {name}")


def _sensor_id(arguments: dict) -> str:
    sensor_id = (arguments or {}).get("sensor_id")
    if not sensor_id or not isinstance(sensor_id, str):
        raise api.ApiError("sensor_id argument is required (see list_sensors)")
    return sensor_id


def handle(message: dict):
    """Return the JSON-RPC response dict, or None for notifications."""
    method = message.get("method", "")
    msg_id = message.get("id")
    if msg_id is None:
        return None  # notification: nothing to answer

    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
        result = {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        }
        return _ok(msg_id, result)

    if method == "ping":
        return _ok(msg_id, {})

    if method == "tools/list":
        return _ok(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
            text = json.dumps(result, indent=2)
            return _ok(msg_id, {"content": [{"type": "text", "text": text}], "isError": False})
        except Exception as exc:  # surface API errors as tool errors, not protocol errors
            text = json.dumps({"error": str(exc)})
            return _ok(msg_id, {"content": [{"type": "text", "text": text}], "isError": True})

    return _err(msg_id, -32601, f"method not found: {method}")


def _ok(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _err(msg_id, code, text):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": text}}


def main() -> int:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        response = handle(message)
        if response is not None:
            stdout.write((json.dumps(response) + "\n").encode("utf-8"))
            stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
