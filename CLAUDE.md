# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An MCP (Model Context Protocol) server that exposes the ORKL threat intelligence library (`https://orkl.eu/api/v1`) to LLM clients. The ORKL API is public and unauthenticated; there are no secrets to configure.

## The server

`orkl_final.py` — high-level `FastMCP` framework. Tools only: `search_threat_reports`, `get_report_details`, `get_threat_actor_info`. Verified working against `mcp` 1.27.1 / `fastmcp` 3.2.4. Registered as the `orkl` MCP server in Claude Code at user scope (`~/.claude.json`).

There used to be a second implementation at `server.py` (low-level `mcp.server` SDK, exposing Resources and six tools backed by an in-process cache). It silently stopped working after `mcp` SDK API drift and was deleted. If the richer Resources/six-tool surface is ever wanted back, re-implement it as FastMCP tools/resources in `orkl_final.py` rather than restoring the old file — the FastMCP version is the supported path.

## Running

The server runs over stdio for an MCP client to spawn — there is no HTTP server to start. A working venv is already set up at `.venv/` with the minimal deps (`mcp`, `httpx`, `fastmcp`, `pydantic`).

```bash
# Working server
.venv/bin/python orkl_final.py
```

To smoke-test the MCP handshake manually, pipe JSON-RPC into stdin:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | .venv/bin/python orkl_final.py
```

It's already registered as the `orkl` MCP in Claude Code (`claude mcp list` to confirm). Restart the Claude Code session after any change to the script for the new process to be picked up.

## Dependencies

Managed with [uv](https://docs.astral.sh/uv/). `pyproject.toml` declares three direct deps (`fastmcp`, `httpx`, `pydantic`); `uv.lock` pins the full transitive tree. `mcp` comes in via `fastmcp`. To recreate the venv from scratch: `uv sync`. Don't add a `requirements.txt`.

## ORKL API conventions used here

- Library entries (reports): `GET /library/entries` (list, supports `limit`, `order_by`, `order`), `GET /library/entry/{id}` (detail). **`/library/entries` does NOT support keyword search** — it silently ignores `q`/`query`/`search` params and just returns the latest reports. For keyword search, use `GET /library/search?query=...` (the param name *must* be `query`; `q` returns a 406 "query can't be empty" error). Some search results have `title: null` — fall back to `(untitled)`.
- Threat actors: `GET /ta/entries`, `GET /ta/entry/{id}`. Actor display name is `main_name`; `synonyms` is a list.
- Sources: `GET /source/entries`, `GET /source/entry/{id}`.
- All responses wrap payloads in `{"data": ...}`.

`get_threat_actor_info` in `orkl_final.py` does client-side substring matching against `main_name` over the full `/ta/entries` list — there is no server-side actor search endpoint in use.

## Repo state

- Git remote: `git@github.com:michaelbarry/orkl_mcp.git`.
- No tests, no lint config. If adding any, treat as new scaffolding rather than updating existing tooling.
