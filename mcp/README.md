# Nuance MCP Server

A Model Context Protocol server that exposes Nuance's cultural-intelligence
capabilities to any MCP-compatible AI agent: Claude Desktop, Claude Code,
Cursor, ChatGPT Desktop, and enterprise agents (LangGraph, AutoGPT, etc.).

This is the **strategic 2026 feature**: Nuance becomes the cultural-context
substrate that every enterprise AI agent can call. It is the lever for the
Brand-tier ($1,290/mo) → Enterprise expansion motion.

## Tools

| Tool | What it does |
|---|---|
| `nuance.score_content` | Pre-Launch Cultural Risk Score (0-100) for draft content |
| `nuance.translate_culture` | Frame-preserving content adaptation, 2-3 variants |
| `nuance.get_divergence` | Cultural Divergence Score lookup |
| `nuance.find_analogs` | k nearest historical campaign-launch analogs |
| `nuance.generate_brief` | 2-page AI Cultural Intelligence Brief |
| `nuance.list_events` | Inventory of analyzable events |
| `nuance.list_tracked_entities` | Active drift-monitoring subscriptions |

## Local install (Claude Desktop / Claude Code / Cursor)

```bash
# 1. Install deps
pip install -r mcp/requirements.txt

# 2. Configure Snowflake creds (~/.snowflake/config.toml or env vars)
#    See ../data/snowflake_config.template.toml

# 3. Add to your Claude Desktop config
#    (macOS: ~/Library/Application Support/Claude/claude_desktop_config.json)
#    (Windows: %APPDATA%\Claude\claude_desktop_config.json)
```

Example Claude Desktop config:

```json
{
  "mcpServers": {
    "nuance": {
      "command": "python",
      "args": ["C:/Users/micha/Nuance/mcp/nuance_mcp_server.py"],
      "env": {
        "SNOWFLAKE_CONNECTION": "default"
      }
    }
  }
}
```

Restart Claude Desktop. The `nuance` tools should appear.

## Hosted deployment (for paying customers)

For Brand-tier customers, Nuance hosts an MCP HTTP endpoint that authenticates
against their own Snowflake account via OAuth 2.1 — so every tool call runs SQL
against *their* tables, not ours. Their data never leaves their boundary.

### Fly.io (recommended for v1)

```bash
fly launch --name nuance-mcp-customer-xxx --no-deploy
fly secrets set \
    SNOWFLAKE_ACCOUNT=... \
    SNOWFLAKE_USER=... \
    SNOWFLAKE_PRIVATE_KEY_PATH=/secrets/sf_key.p8 \
    NUANCE_MCP_TRANSPORT=http
fly deploy
```

A minimal `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp/nuance_mcp_server.py .
ENV NUANCE_MCP_TRANSPORT=http
EXPOSE 8000
CMD ["python", "nuance_mcp_server.py"]
```

### Cloud Run / Render / Railway

All work the same — set the env vars listed above and expose port 8000.

## Try it (after install)

In Claude Desktop, ask:

> "Use nuance.score_content to evaluate this tagline for the Japanese market: 'Live free, drive fast — your personal speed machine.'"

Or in Cursor:

> "Call nuance.translate_culture to adapt 'Be your own boss' for the Korean market."

## Security model

- The MCP server authenticates only against the configured Snowflake account.
- Per-tool calls go through Snowflake's RBAC — the customer controls grants.
- All inputs/outputs are logged to `internal.inference_logs` (audit trail).
- The server itself stores no customer data.

## Roadmap

- OAuth 2.1 customer-account auth (currently key-pair only).
- Streaming responses for `generate_brief`.
- Multi-tenant hosted version with per-customer SQL connection pools.
- `nuance.subscribe_drift` and `nuance.unsubscribe_drift` tools.
