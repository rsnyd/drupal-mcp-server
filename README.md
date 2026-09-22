
# drupal-mcp-server

An MCP server exposing Drupal development tools to any MCP-compatible AI
assistant (Claude Desktop, Claude Code, Cursor, ChatGPT). Built with FastMCP.

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

```bash
git clone https://github.com/rsnyd/drupal-mcp-server
cd drupal-mcp-server
uv sync
```

## Use with Claude Desktop

(config snippet + screenshots)

## Develop / test

```bash
npx @modelcontextprotocol/inspector uv run server.py
```
