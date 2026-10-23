# tempstick-mcp

**Temp Stick MCP server by OpenPandora — let your AI assistant check your
freezer and temperature sensors.**

> **New to this?** Follow the [plain-words setup guide](SETUP.md) —
> five minutes, short steps, no jargon.

tempstick-mcp is a free, open-source
[Model Context Protocol](https://modelcontextprotocol.io) (MCP) server
for [Temp Stick](https://tempstick.com) WiFi temperature sensors by Ideal
Sciences — a freezer monitor and temperature sensor reader for your AI
assistant. It was built for restaurant kitchens (nobody wants to discover
a warm walk-in at 6 AM), and it works anywhere a Temp Stick watches
something that matters: freezers, fridges, server rooms, greenhouses,
homes. Connect it to Claude, Cursor, or any MCP client and just ask:

> "What's my freezer at right now?"
> "Has the walk-in been above 40°F today?"
> "Is any sensor offline or low on battery?"

The server answers with live data from the official Temp Stick API:
temperature (Celsius and Fahrenheit), humidity, battery level, offline
status, alert definitions, and recent-reading summaries.

- **Zero dependencies.** Pure Python 3 standard library — no `pip install`
  of anything. Clone, add your key, go.
- **Read-only.** It cannot change a setting, a threshold, or an alert on
  your account.
- **Private by design.** Your API key stays on your machine in an
  environment variable. The server talks only to `tempstickapi.com`.

## Tools

| Tool | What it returns |
| --- | --- |
| `list_sensors` | Every sensor your key can see, with its latest temperature, humidity, battery and offline status. |
| `get_sensor` | The latest reading for one sensor (by `sensor_id`). |
| `get_freezer_status` | One-call check for a sensor: latest reading + recent history summary + alert definitions together. Named for the classic freezer use case; works for any sensor. |
| `get_readings_history` | A summary of a sensor's recent readings: count, min / max / average temperature, first and last reading times. |
| `get_alerts` | The account's alert definitions and whether they are triggered. |

A command-line twin is included for terminal checks and cron jobs:
`tempstick.py list-sensors`, `latest --sensor <ID>`, `history --sensor <ID>`,
`alerts`, `freezer --sensor <ID>`.

## Get your API key

1. Sign in at [mytempstick.com](https://mytempstick.com).
2. Open the **Account Page**.
3. Select the **Developers** tab.
4. Click **Show Key** to reveal your API key.

(Per Temp Stick's official developer documentation.)

## Install

```bash
git clone https://github.com/obseard223/tempstick-mcp
```

### Claude Desktop

Add to your `claude_desktop_config.json` (macOS:
`~/Library/Application Support/Claude/claude_desktop_config.json`;
Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tempstick": {
      "command": "python3",
      "args": ["/path/to/tempstick-mcp/server.py"],
      "env": { "TEMPSTICK_API_KEY": "paste-your-key-here" }
    }
  }
}
```

Restart Claude Desktop, then ask: "List my Temp Stick sensors."

### Claude Code

```bash
claude mcp add tempstick \
  --env TEMPSTICK_API_KEY=paste-your-key-here \
  -- python3 /path/to/tempstick-mcp/server.py
```

### Cursor

Add to `.cursor/mcp.json` in your project (or the global MCP config):

```json
{
  "mcpServers": {
    "tempstick": {
      "command": "python3",
      "args": ["/path/to/tempstick-mcp/server.py"],
      "env": { "TEMPSTICK_API_KEY": "paste-your-key-here" }
    }
  }
}
```

On Windows, use `python` instead of `python3` (and a Windows-style path).

## Test it offline

No key, no network:

```bash
python3 selftest.py            # full end-to-end test against a stub API
python3 tempstick.py selftest  # parsing/unit checks only
```

Both should end in PASS.

## Notes on the API

A few behaviors of the Temp Stick API this server handles for you:

- Errors come back as HTTP 200 with a JSON envelope (`type: "error"`), so
  the server checks the envelope and surfaces the real message — e.g.
  `Invalid X-API-KEY`.
- Temperatures arrive in Celsius; every reading is also reported in
  Fahrenheit.
- The API host rejects non-browser user agents, so the server sends a
  browser user agent.

## Status

Community project, built against the official Temp Stick API. It is not
affiliated with or endorsed by Ideal Sciences or Temp Stick. The parsing
and protocol layers are covered by offline fixture tests (see
`selftest.py`); readings and alerts shapes beyond the documented fields
are parsed defensively.

## Built by OpenPandora

Built by [OpenPandora](https://openpandora.tech) — AI tools for
independent restaurants. This is the same sensor watch that keeps an eye
on our pilot kitchen's walk-in freezer, released free because every
operator with a Temp Stick should be able to ask their AI about it.

## License

MIT — see [LICENSE](LICENSE).
