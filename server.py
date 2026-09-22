"""drupal-mcp-server: MCP tools for Drupal development.

Run: uv run server.py
Test: npx @modelcontextprotocol/inspector uv run server.py
"""
from mcp.server.mcpserver import MCPServer
import re
from pathlib import Path

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

@mcp.tool()
def list_services(services_yml_content: str) -> str:
    """Parse a Drupal *.services.yml file and list the service IDs, classes, and arguments.

    Args:
        services_yml_content: The raw content of a .services.yml file.
    """
    # Lightweight YAML-ish parse (a fuller version would use the yaml library)
    import yaml
    try:
        data = yaml.safe_load(services_yml_content)
    except Exception as e:
        return f"Could not parse YAML: {e}"
    services = data.get("services", {})
    if not services:
        return "No services found."
    lines = []
    for sid, sdef in services.items():
        cls = sdef.get("class", "?") if isinstance(sdef, dict) else "?"
        args = sdef.get("arguments", []) if isinstance(sdef, dict) else []
        lines.append(f"- {sid}\n    class: {cls}\n    arguments: {args}")
    return "Services:\n" + "\n".join(lines)


@mcp.tool()
def scaffold_content_entity(entity_id: str, label: str, fields: list[str]) -> str:
    """Generate boilerplate for a custom Drupal content entity type.

    Args:
        entity_id: Machine name, e.g. 'product_review'.
        label: Human label, e.g. 'Product Review'.
        fields: List of base field machine names to scaffold, e.g. ['title', 'rating', 'body'].
    """
    class_name = "".join(p.capitalize() for p in entity_id.split("_"))
    field_methods = "\n".join(
        f"    // baseFieldDefinitions would define: {f}" for f in fields
    )
    return f"""<?php

namespace Drupal\\my_module\\Entity;

use Drupal\\Core\\Entity\\ContentEntityBase;
use Drupal\\Core\\Entity\\EntityTypeInterface;
use Drupal\\Core\\Field\\BaseFieldDefinition;

/**
 * Defines the {label} entity.
 *
 * @ContentEntityType(
 *   id = "{entity_id}",
 *   label = @Translation("{label}"),
 *   base_table = "{entity_id}",
 *   entity_keys = {{
 *     "id" = "id",
 *     "uuid" = "uuid",
 *     "label" = "title",
 *   }},
 *   handlers = {{
 *     "list_builder" = "Drupal\\Core\\Entity\\EntityListBuilder",
 *     "form" = {{
 *       "default" = "Drupal\\Core\\Entity\\ContentEntityForm",
 *     }},
 *   }},
 * )
 */
class {class_name} extends ContentEntityBase {{

  public static function baseFieldDefinitions(EntityTypeInterface $entity_type) {{
    $fields = parent::baseFieldDefinitions($entity_type);
{field_methods}
    return $fields;
  }}

}}
"""


@mcp.resource("drupal://hooks/common")
def common_hooks() -> str:
    """A reference list of commonly used Drupal entity and form hooks."""
    return (
        "Common Drupal hooks:\n"
        "- hook_entity_presave / hook_ENTITY_TYPE_presave\n"
        "- hook_entity_insert / hook_entity_update / hook_entity_delete\n"
        "- hook_form_alter / hook_form_FORM_ID_alter\n"
        "- hook_entity_access / hook_ENTITY_TYPE_access\n"
        "- hook_views_data / hook_views_data_alter\n"
        "- hook_cron, hook_theme, hook_preprocess_HOOK\n"
    )


if __name__ == "__main__":
    mcp.run()