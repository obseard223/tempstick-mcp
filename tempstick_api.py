"""Shared client for the official Temp Stick API (Ideal Sciences).

Used by both the MCP server (server.py) and the CLI (tempstick.py).

API facts, verified against the live API host and working community
configurations:

- Base URL: https://tempstickapi.com/api/v1 (override with the
  TEMPSTICK_API_BASE environment variable, mainly for testing).
- Authentication is a single API key sent in the ``X-API-KEY`` header.
- The API answers HTTP 200 even for failures, with a JSON envelope whose
  ``type`` reads ``error`` and whose ``message`` names the problem. A
  missing key returns "X-API-KEY is a required header" and a wrong key
  returns "Invalid X-API-KEY".
- The host refuses non-browser user agents with HTTP 406, so a browser
  user agent is sent on every request.
- ``last_temp`` is reported in Celsius; Fahrenheit is added alongside.
"""

from __future__ import annotations

import json
import os
import urllib.request

DEFAULT_API_BASE = "https://tempstickapi.com/api/v1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


class ApiError(RuntimeError):
    """Raised when the Temp Stick API returns a type=error envelope."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def api_base() -> str:
    return os.environ.get("TEMPSTICK_API_BASE", DEFAULT_API_BASE).rstrip("/")


def get_api_key() -> str:
    key = os.environ.get("TEMPSTICK_API_KEY", "").strip()
    if not key:
        raise ApiError(
            "TEMPSTICK_API_KEY is not set. Get your key from your Temp Stick "
            "account (Account Page -> Developers tab -> Show Key) and pass it "
            "in the TEMPSTICK_API_KEY environment variable."
        )
    return key


def api_get(path: str) -> dict:
    request = urllib.request.Request(
        api_base() + path,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "X-API-KEY": get_api_key(),
        },
    )
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict) and payload.get("type") == "error":
        raise ApiError(f"Temp Stick API error: {payload.get('message')}")
    return payload


def c_to_f(celsius: float) -> float:
    return celsius * 1.8 + 32.0


def data_of(payload):
    if isinstance(payload, dict):
        return payload.get("data", payload)
    return payload


def summarize_sensor(data: dict) -> dict:
    """Pull the documented fields out of one sensor payload."""
    out = {}
    if not isinstance(data, dict):
        return out
    for key in ("sensor_id", "sensor_name", "name", "type"):
        if data.get(key) is not None:
            out[key] = data[key]
    last_temp = data.get("last_temp")
    if isinstance(last_temp, (int, float)):
        out["last_temp_c"] = last_temp
        out["last_temp_f"] = round(c_to_f(last_temp), 1)
    if data.get("last_humidity") is not None:
        out["last_humidity_pct"] = data["last_humidity"]
    if data.get("last_checkin") is not None:
        out["last_checkin"] = data["last_checkin"]
    if data.get("offline") is not None:
        out["offline"] = bool(data["offline"])
    if data.get("battery_pct") is not None:
        out["battery_pct"] = data["battery_pct"]
    return out


def list_sensors() -> dict:
    payload = api_get("/sensors")
    data = data_of(payload)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("sensors") or [data]
    else:
        items = []
    sensors = []
    for item in items:
        if isinstance(item, dict):
            sensors.append(summarize_sensor(item) or item)
    return {"sensors": sensors, "count": len(sensors)}


def get_sensor(sensor_id: str) -> dict:
    payload = api_get(f"/sensor/{sensor_id}")
    data = data_of(payload)
    if isinstance(data, dict):
        return summarize_sensor(data)
    return {"data": data}


def extract_readings(data) -> list:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("readings", "history", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _reading_temp_c(reading: dict):
    for key in ("temp", "temperature", "temp_c", "temperature_c", "value"):
        value = reading.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _reading_time(reading: dict):
    for key in ("reading_time", "checkin", "last_checkin", "time", "timestamp",
                "created_at", "date", "datetime"):
        value = reading.get(key)
        if value:
            return str(value)
    return None


def summarize_readings(readings: list) -> dict:
    temps = [t for t in (_reading_temp_c(r) for r in readings) if t is not None]
    times = [t for t in (_reading_time(r) for r in readings) if t]
    out = {"reading_count": len(readings)}
    if temps:
        out["temp_min_f"] = round(c_to_f(min(temps)), 1)
        out["temp_max_f"] = round(c_to_f(max(temps)), 1)
        out["temp_avg_f"] = round(c_to_f(sum(temps) / len(temps)), 1)
    if times:
        out["first_reading_time"] = min(times)
        out["last_reading_time"] = max(times)
    return out


def get_readings_history(sensor_id: str) -> dict:
    payload = api_get(f"/sensor/{sensor_id}/readings")
    readings = extract_readings(data_of(payload))
    return summarize_readings(readings)


def get_alerts() -> dict:
    payload = api_get("/alerts")
    data = data_of(payload)
    if isinstance(data, list):
        return {"alerts": data, "count": len(data)}
    if isinstance(data, dict):
        alerts = data.get("alerts")
        if isinstance(alerts, list):
            return {"alerts": alerts, "count": len(alerts)}
    return {"alerts": data}


def get_freezer_status(sensor_id: str) -> dict:
    """One-call status for a sensor (named for the classic freezer use case).

    Combines the latest reading with the account's alert definitions so an
    assistant can answer "is my freezer OK?" in a single tool call.
    """
    return {
        "sensor_id": sensor_id,
        "latest": get_sensor(sensor_id),
        "history": get_readings_history(sensor_id),
        "alerts": get_alerts(),
    }
