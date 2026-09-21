"""drupal-mcp-server: MCP tools for Drupal development.

Run: uv run server.py
Test: npx @modelcontextprotocol/inspector uv run server.py
"""
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("drupal-dev")


@mcp.tool()
def explain_hook(hook_name: str) -> str:
    """Explain a Drupal hook: its purpose, signature, parameters, and common use cases.

    Args:
        hook_name: The hook name, e.g. 'hook_entity_presave' or 'hook_form_alter'.
    """
    # Static knowledge base for common hooks. In a fuller version this would
    # query api.drupal.org or your RAG index.
    hooks = {
        "hook_entity_presave": {
            "purpose": "Act on an entity before it is saved to storage.",
            "signature": "function hook_entity_presave(EntityInterface $entity)",
            "params": "EntityInterface $entity - the entity about to be saved",
            "use_cases": "Set computed field values, normalize data, enforce invariants before write.",
            "note": "Fires for every entity type. For one type, use hook_ENTITY_TYPE_presave.",
        },
        "hook_form_alter": {
            "purpose": "Modify any form before it is rendered.",
            "signature": "function hook_form_alter(array &$form, FormStateInterface $form_state, $form_id)",
            "params": "&$form (by reference), $form_state, $form_id",
            "use_cases": "Add/remove fields, attach validation or submit handlers, alter UI.",
            "note": "For one form, prefer hook_form_FORM_ID_alter for efficiency.",
        },
    }
    h = hooks.get(hook_name)
    if not h:
        return f"Hook '{hook_name}' not in the local knowledge base. Check api.drupal.org."
    return (
        f"# {hook_name}\n\n"
        f"Purpose: {h['purpose']}\n\n"
        f"Signature: {h['signature']}\n\n"
        f"Parameters: {h['params']}\n\n"
        f"Common use cases: {h['use_cases']}\n\n"
        f"Note: {h['note']}"
    )


if __name__ == "__main__":
    mcp.run()