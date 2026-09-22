# I Built an MCP Server for Drupal Development

*Draft — publish Week 12. Target: personal blog (canonical), then LinkedIn, then Show HN + r/drupal.*

---

AI coding assistants are extraordinary until the moment they aren't, and the moment is always the same one: the code is syntactically perfect and conventionally wrong.

Ask one to write a Drupal hook that adjusts an entity before save, and you'll get something that runs. You'll also get `hook_entity_presave()` when the situation called for `hook_ENTITY_TYPE_presave()`, because the model has no way to know that the first fires for every entity in the system and the second fires only for the one you care about. Ask for an entity type and you'll get an annotation that's *almost* right, missing the one handler key that makes the thing show up in the admin UI. The assistant isn't hallucinating. It's just working from a general impression of Drupal rather than from Drupal.

You can fix this per-conversation by pasting context in. I did that for months. It works, and it's a tax you pay every single time.

So I stopped paying it and built a tool instead. This is how I taught a general-purpose coding assistant to speak Drupal — and, more usefully, how the protocol that made it possible means I only had to teach it once.

## What MCP actually is

Model Context Protocol is an open standard for connecting AI assistants to tools and data. The pitch that matters to a working developer is narrow and concrete:

**Write your tool once. Use it in every assistant that speaks the protocol.**

Before MCP, giving an AI assistant a custom capability meant building against whatever that particular product exposed. A Claude Desktop integration and a Cursor integration were two different projects with two different lifespans. MCP replaces that with one interface. You run a small server that advertises what it can do; the assistant discovers those capabilities and calls them when relevant.

A server can expose three kinds of thing. **Tools** are functions the model can invoke — they take arguments and do work. **Resources** are read-only context the model can pull in, addressed by URI. **Prompts** are reusable templates a user can invoke directly. This project uses the first two.

The important architectural detail: *the model decides when to call your tool.* You don't write routing logic or intent detection. You write a good docstring, and the assistant reads it the way a new team member reads your API docs. That shapes how you build — more on that below, because it's the part that surprised me.

## The tools

Drupal and MCP is a nearly empty intersection, which is exactly why it was worth building. Three tools, each aimed at a specific way assistants get Drupal wrong.

### `explain_hook(hook_name)`

Returns a hook's purpose, signature, parameters, common use cases, and — the part that earns its keep — its gotcha.

```
# hook_entity_presave

Purpose: Act on an entity before it is saved to storage.

Signature: function hook_entity_presave(EntityInterface $entity)

Parameters: EntityInterface $entity - the entity about to be saved

Common use cases: Set computed field values, normalize data,
enforce invariants before write.

Note: Fires for every entity type. For one type, use
hook_ENTITY_TYPE_presave.
```

That last line is the whole point. Anyone can look up a signature. The `hook_ENTITY_TYPE_*` distinction is the kind of thing you learn by shipping a performance regression, and it's precisely the kind of thing a model trained on a broad sweep of PHP will smooth over. Encoding it once means the assistant stops making that mistake — not because it got smarter, but because it now has somewhere to look.

### `list_services(services_yml_content)`

Takes the raw contents of a `*.services.yml` file and returns the service IDs, their classes, and their arguments in a flat, readable list.

Dependency injection is where Drupal's learning curve gets steep, and service wiring is the specific cliff. When you're staring at a container error, the question is almost always "what's actually registered, and what does it depend on?" — and the answer is spread across YAML files that are structurally simple but visually dense. This flattens them into something both you and the model can scan.

It also means an assistant can answer "which service should I inject here?" against *your* module's real service definitions, rather than against a plausible-sounding invention.

### `scaffold_content_entity(entity_id, label, fields)`

Generates the boilerplate for a custom content entity type: namespace, imports, the `@ContentEntityType` annotation with entity keys and handlers, and a `baseFieldDefinitions()` stub for each field you name.

```python
scaffold_content_entity(
    entity_id="product_review",
    label="Product Review",
    fields=["title", "rating", "body"],
)
```

Out comes a `ProductReview` class with the annotation filled in correctly — `base_table`, `entity_keys`, the handler map. This is the least intellectually interesting tool and possibly the most useful one. Custom entity boilerplate is long, structurally fussy, and *almost* memorable, which is the worst combination: you remember it well enough not to look it up and badly enough to get a key wrong.

### The resource: `drupal://hooks/common`

Alongside the tools, a read-only resource listing the hooks that actually come up — the entity lifecycle set, the form alters, `hook_views_data`, `hook_cron`, `hook_theme`, `hook_preprocess_HOOK`.

Tools answer questions. This resource helps the assistant know which questions are worth asking. When it can see the shape of the hook system, "you probably want `hook_form_FORM_ID_alter` here" becomes available as a suggestion rather than something you have to prompt for.

## The build

Here's the part I want to be honest about, because it's the most useful thing in this post for anyone thinking about building their own: **the entire server is about 140 lines of Python, and most of them are Drupal knowledge, not protocol code.**

The Python SDK does the heavy lifting. A tool is a decorated function:

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("drupal-dev")


@mcp.tool()
def explain_hook(hook_name: str) -> str:
    """Explain a Drupal hook: its purpose, signature, parameters,
    and common use cases.

    Args:
        hook_name: The hook name, e.g. 'hook_entity_presave'.
    """
    ...
```

That's it. That's the integration. The decorator reads your type hints to generate the JSON Schema the protocol requires, and reads your docstring to generate the description the model uses to decide whether to call it. A resource is the same idea with a URI:

```python
@mcp.resource("drupal://hooks/common")
def common_hooks() -> str:
    """A reference list of commonly used Drupal entity and form hooks."""
    ...
```

And the server runs on stdio with:

```python
if __name__ == "__main__":
    mcp.run()
```

**A naming note, because it'll cost you twenty minutes otherwise:** most MCP tutorials you'll find refer to this API as `FastMCP` and import `from mcp.server.fastmcp import FastMCP`. In mcp 2.x, `FastMCP` was renamed to `MCPServer` and moved to `mcp.server.mcpserver`. Same API, same ergonomics, different import line. The old module path now exists only to raise an error telling you what happened, which is a genuinely considerate bit of API design.

### What the build actually taught me

Three things I didn't expect.

**The docstring is the interface.** Not documentation *about* the interface — the interface itself. It's the only thing the model sees when deciding whether your tool is relevant to what the user just asked. I rewrote `explain_hook`'s docstring more times than I rewrote its body. "Explains hooks" got ignored. "Explain a Drupal hook: its purpose, signature, parameters, and common use cases" got called. Including a concrete example in the `Args` section mattered too — `e.g. 'hook_entity_presave'` teaches the argument's shape in a way a type annotation can't.

If you've written OpenAPI descriptions with any care, the instinct transfers directly. If you haven't, the rule of thumb is: write it for a competent developer who's never seen your codebase and is deciding, in about two seconds, whether this function solves their problem.

**Return text, not data structures.** My first instinct was to return JSON, because that's what an API returns. Wrong instinct. The consumer here is a language model, and models read prose. Returning a formatted block with headers and labeled sections produced noticeably better answers than returning the same facts as a dict. The tool's output becomes part of the model's context; you're writing for a reader, not a parser.

**Scope small and ship.** `explain_hook` currently knows two hooks. Two. I could have spent the week loading a hundred of them in before showing anyone, and the result would have been a slower path to the thing that actually taught me something — which was watching a real assistant call a real tool and reason with what came back. The knowledge base is a stub. The interface is the product. Stubs are cheap to fill; interfaces are expensive to change.

## Using it

Testing first. The MCP Inspector gives you a browser UI against your server without wiring up an assistant at all:

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

You get a list of discovered tools, a form to invoke each one, and the raw protocol traffic. Do this before you touch any client config. It separates "my tool is broken" from "my config is broken," and those are very different afternoons.

To use it in Claude Desktop, add the server to your config:

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

Use an absolute path. Restart the app.

> **[SCREENSHOT 1]** — Claude Desktop's tools menu showing `drupal-dev` connected, with `explain_hook`, `list_services`, and `scaffold_content_entity` listed. *This is the "it's really there" shot — the proof the protocol handshake worked.*

> **[SCREENSHOT 2]** — A conversation where the assistant calls `explain_hook` unprompted. Ask something in plain language — "I need to normalize a field value before a node is saved, what's the right hook?" — and capture the tool-call indicator plus the answer. *This is the payoff shot. The user never said "use the tool." The model read the docstring and decided.*

> **[SCREENSHOT 3]** — `scaffold_content_entity` producing the `ProductReview` class. *Shows real generated output, not a toy string.*

And that unprompted call is the whole thing in one frame. I asked a question in ordinary English. The assistant recognized it as a Drupal hook question, called a tool it discovered thirty seconds after I edited a JSON file, and answered with the `hook_ENTITY_TYPE_presave` caveat included — the exact caveat it would have missed the week before.

There's no prompt engineering in that interaction. No system prompt stuffed with Drupal conventions, no pasted documentation, no "remember that in Drupal..." preamble. The knowledge lives in a tool, the tool lives in a server, and every assistant I point at that server gets it. Same server, unchanged, works in Claude Code from the terminal. That's the write-once-use-everywhere claim cashing out, and it's more satisfying in practice than it sounds in a spec.

## What's next

**Wire `explain_hook` to a live retrieval index.** This is the obvious next move and the one I'm most interested in. The hardcoded knowledge base is a placeholder for something I've already built separately: a RAG system over Drupal's Entity API documentation — scraped, chunked, embedded, with three retrieval strategies (vanilla cosine, hybrid BM25 + vector via reciprocal rank fusion, and hybrid plus a reranking pass) compared against a golden question set using an LLM-as-judge harness.

Those two projects are currently strangers. They shouldn't be. `explain_hook` becomes dramatically more useful the moment it queries that index instead of a dictionary with two keys in it — it stops being limited to hooks I thought to write down and starts answering from the documentation itself, with citations. The MCP server is the delivery mechanism the RAG system was missing; the RAG system is the knowledge the MCP server is standing in for.

That's also, I think, the more general lesson. A retrieval system with a CLI is a demo. A retrieval system behind an MCP tool is something that shows up inside the editor where the work actually happens.

**More scaffolding.** Config entities, plugin classes, custom field types, Views handlers. Each one is boilerplate with a shape, which is precisely the category that benefits from a generator that knows the shape exactly.

**Read the module, don't just take a paste.** `list_services` takes YAML content as a string today, which means someone has to paste it. Pointing it at a module directory — parsing `.info.yml`, `.services.yml`, `.routing.yml`, and `.permissions.yml` together — would let an assistant answer questions about a module's actual structure instead of a fragment of it.

**Drush integration.** Read-only to start: cache states, enabled modules, config diffs. There's a real design question here about where the boundary sits between an assistant that reads your site's state and one that changes it, and I'd rather earn trust on the read side first.

---

The server is open source: [github.com/rsnyd/drupal-mcp-server](https://github.com/rsnyd/drupal-mcp-server)

If you work in a framework with strong conventions — Drupal, Rails, Laravel, Django, anything where the right answer depends on knowing what the community settled on — the same approach applies almost unchanged. The protocol is not the hard part. It's a decorator. The hard part is knowing which conventions your assistant keeps getting wrong, and you already know that, because you've been correcting them by hand.

Write those down as tools instead.

---

## Pre-publication checklist

- [ ] Capture the three screenshots (none are in the repo yet — the Day 19 commit only touched the README)
- [ ] Confirm the GitHub URL is live and the repo is public
- [ ] Verify the Claude Desktop config snippet against the current config file location
- [ ] Decide whether to name the RAG project (`drupal-rag-cli`) and link it, or keep it as a forward reference until that post publishes
- [ ] Trim if over ~1,800 words for the blog version; the LinkedIn version wants ~150 words plus a link
- [ ] Show HN title: "Show HN: An MCP server for Drupal development"
