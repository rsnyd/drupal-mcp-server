
# drupal-mcp-server

An MCP server exposing Drupal development tools to any MCP-compatible AI
assistant (Claude Desktop, Claude Code, Cursor, ChatGPT). Built with the
official `mcp` Python SDK's `MCPServer` (the mcp 2.x name for FastMCP).

Drupal + MCP is a near-empty intersection. This server lets an AI coding
assistant work with Drupal conventions natively - explaining hooks, parsing
service definitions, and scaffolding entities - without you pasting Drupal
context into every prompt.

## Tools

- `explain_hook(hook_name)` - hook purpose, signature, parameters, use cases
- `list_services(services_yml_content)` - parse a .services.yml file
- `scaffold_content_entity(entity_id, label, fields)` - generate entity boilerplate

## Resources

- `drupal://hooks/common` - reference list of common Drupal hooks

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/rsnyd/drupal-mcp-server
cd drupal-mcp-server
uv sync
```

## Use with Claude Code

```bash
claude mcp add drupal-dev -- uv --directory /absolute/path/to/drupal-mcp-server run server.py
```

Then ask something like "I need to normalize a field value before a node is
saved - what's the right hook?" and Claude Code will call `explain_hook`.

## Use with Claude Desktop

Add the server to `claude_desktop_config.json`
(`%APPDATA%\Claude\` on Windows, `~/Library/Application Support/Claude/` on macOS):

```json
{
  "mcpServers": {
    "drupal-dev": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/drupal-mcp-server", "run", "server.py"]
    }
  }
}
```

Use an absolute path and restart the app. The `drupal-dev` tools then appear in
the tools menu.

On Windows with the repo inside WSL2, Claude Desktop cannot launch a WSL path
directly. Either point `command` at `wsl.exe` with the uv invocation as its
arguments, or run Claude Code inside WSL2 where the paths line up.

## Develop / test

The MCP Inspector lists the tools, lets you call them with arguments, and shows
the raw protocol traffic - test here before touching any client config:

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

## Version note

Older tutorials import `from mcp.server.fastmcp import FastMCP`. In mcp 2.x that
class was renamed to `MCPServer` at `mcp.server.mcpserver`; the decorators and
`run()` are unchanged. This project requires `mcp[cli]>=2.2.0`.
