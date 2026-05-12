# orkl-mcp

A Model Context Protocol (MCP) server that exposes the [ORKL](https://orkl.eu) threat intelligence library to LLM clients (Claude Code, Claude Desktop, MCP Inspector, etc.).

ORKL aggregates public threat reports, threat-actor profiles, and source metadata. The API is public and unauthenticated, so there are no secrets to configure.

## Tools provided

| Tool | Purpose |
| --- | --- |
| `search_threat_reports(query, limit=10)` | Keyword search across the ORKL library. |
| `get_report_details(report_id)` | Full JSON for a single report (IOCs, hashes, references, body). |
| `get_threat_actor_info(name_or_id)` | Lookup a threat actor by display name (substring match) or ID. |

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency and venv management

```sh
brew install uv
```

## Setup

```sh
git clone git@github.com:michaelbarry/orkl_mcp.git
cd orkl_mcp
uv sync
```

`uv sync` creates `.venv/` from the lockfile.

## Run

The server speaks MCP over stdio — there is no HTTP listener. It expects an MCP client to spawn it.

```sh
.venv/bin/python orkl_final.py
# or
uv run python orkl_final.py
```

## Register with Claude Code

```sh
claude mcp add --scope user orkl -- \
  /absolute/path/to/orkl_mcp/.venv/bin/python \
  /absolute/path/to/orkl_mcp/orkl_final.py
```

Confirm with `claude mcp list`. Restart Claude Code for the new server to load.

## Register with Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) and add an entry under `mcpServers`:

```json
{
  "mcpServers": {
    "orkl": {
      "command": "/absolute/path/to/orkl_mcp/.venv/bin/python",
      "args": ["/absolute/path/to/orkl_mcp/orkl_final.py"]
    }
  }
}
```

Replace `/absolute/path/to/orkl_mcp` with the real checkout path. Restart Claude Desktop afterwards.

## Smoke-test the MCP handshake

To verify the server starts cleanly without an MCP client:

```sh
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | .venv/bin/python orkl_final.py
```

You should see two JSON-RPC responses on stdout (`initialize` and `tools/list`).

## ORKL API quirks worth knowing

- **Keyword search uses `GET /library/search?query=<term>`.** The list endpoint `GET /library/entries` does *not* support search — it silently ignores `q`/`query`/`search` and just returns the latest reports. `/library/search` requires the parameter name `query`; `q` returns a 406 with "query can't be empty".
- Some report records have `title: null`; the server falls back to `(untitled)`.
- Threat-actor lookup is client-side: `get_threat_actor_info` fetches the full `/ta/entries` list and does substring matching against `main_name`. There is no server-side actor search endpoint.
- All ORKL responses wrap payloads in `{"data": ...}`.
