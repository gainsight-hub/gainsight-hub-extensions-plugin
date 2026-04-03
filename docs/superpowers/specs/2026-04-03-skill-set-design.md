# Gainsight Hub Extensions Plugin — Skill Set Design

## Overview

A Claude Code plugin providing the development experience for building Gainsight Customer Hub (Insided) extensions. Three skills, one hook, evals per skill.

**Design goals:**
- Invisible guidance — developer installs plugin, Claude just knows how to build extensions correctly
- Measurable quality — eval suite proves the plugin works and catches regressions
- Works both interactively (human-guided) and headlessly (automated eval)

## Plugin Structure

```
gainsight-hub-extensions-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── build-extension/
│   │   ├── SKILL.md
│   │   └── evals/
│   │       ├── trigger_eval.json
│   │       └── evals.json
│   ├── validate-extension/
│   │   ├── SKILL.md
│   │   └── evals/
│   │       ├── trigger_eval.json
│   │       └── evals.json
│   └── hub-reference/
│       ├── SKILL.md
│       └── evals/
│           ├── trigger_eval.json
│           └── evals.json
└── hooks/
    └── postToolUse.sh
```

## Skill 1: `build-extension`

**Description**: Build widgets, stylesheets, scripts, and connectors for Gainsight Customer Hub (Insided) Extensions. Triggers when the user asks to create, build, or modify any extension, or when working in `widgets/*/`, `scripts/*/`, `stylesheets/*/` paths.

### Interactive Workflow

1. **What to build?** — Ask extension type or infer from context (widget, script, stylesheet)
2. **What should it do?** — Gather purpose, behavior, data needs
3. **How should it look?** — Appearance, layout, design. If user references a URL ("style it like xyz.com"), fetch the page and extract design cues (colors, typography, layout patterns)
4. **Data needs** — For widgets: static config vs connector. If connector needed, identify API, fetch its docs, design the connector
5. **Build** — Create directory structure, config files, content files, rebuild registries with `./bin/build-registry.sh`

### Critical Rules (baked into SKILL.md)

- `content.html` must be an HTML fragment — no `<html>`, `<head>`, `<body>` tags
- All CSS/JS inline or from CDN URLs — no relative imports
- Shadow DOM: use `sdk.$()` and `sdk.$$()`, not `document.querySelector()`
- Branding: `var(--config--main-color-brand, #fallback)`
- Widget directory max: 100 files or 10 MB
- Connectors: `get_secret('key')` for credentials — never hardcode secrets

### Documentation Strategy

Layered lookup for framework knowledge:
1. Critical rules in SKILL.md (always available, zero latency)
2. Context7 MCP for Insided docs (on-demand, when available)
3. WebFetch to `https://developers.insided.com/docs/llms-full.txt` (fallback if Context7 unavailable)
4. WebFetch for third-party API docs when building connectors

### What This Skill Does NOT Do

- Validation — that's `validate-extension`'s job (and the PostToolUse hook handles it automatically)
- Answer framework questions without building — that's `hub-reference`

## Skill 2: `validate-extension`

**Description**: Validate Gainsight Hub extensions for correctness — structure, schema, content patterns, connector security. Triggers on "validate my widget", "check this extension", "is my widget correct", or invoked automatically by the PostToolUse hook.

### Two Modes

#### Quick Validation (hook-triggered)

Runs on every Write/Edit to extension paths. Fast, lightweight checks:

- JSON syntax valid (`widget.json`, `connectors.json`, `script.json`, `stylesheet.json`)
- HTML fragment check — reject `<html>`, `<head>`, `<body>` tags in `content.html`
- Required fields present in config files (`version`, `title`, `description`, `category`, `source`/`content`)

Reports issues as actionable messages. Advisory, not blocking.

#### Full Validation (user-triggered)

Everything from quick validation, plus:

- Schema completeness — configuration properties have types and rules
- Connector structure — auth types valid, `get_secret()` used, no hardcoded secrets
- Content quality heuristics — `sdk.$()` not `document.querySelector()`, no relative imports, CDN URLs use HTTPS
- Registry build — runs `./bin/build-registry.sh --validate`

Reports a structured checklist of pass/fail per category. No scoring — binary pass/fail per check.

## Skill 3: `hub-reference`

**Description**: Answer questions about the Gainsight Customer Hub Extensions framework — widget structure, configuration schemas, connector auth types, Shadow DOM patterns, page targeting rules. Triggers on framework questions like "how do connectors work?", "what auth types are available?", "what configuration property types can I use?".

### Behavior

- Answers framework questions using the layered documentation strategy (critical rules → Context7 → WebFetch)
- Provides code examples and references to existing extensions in the repo when relevant
- Does NOT build anything — purely informational

### Knowledge Baked In

- Extension types and directory structures
- `widget.json` schema (required/optional fields, configuration property types)
- Connector auth types (none, apikey, oauth_client_credentials, jwt, oauth_jwt_bearer)
- Jinja2 template variables (`user.id`, `user.email`, `get_secret()`, `now()`, `jwt_encode()`)
- Shadow DOM patterns and SDK usage
- Page targeting rules for scripts/stylesheets
- Registry build commands

## Hook: PostToolUse Auto-Validation

**Triggers on**: Write or Edit tool calls where the file path matches `widgets/**`, `scripts/**`, or `stylesheets/**`.

**Implementation**: Shell script (`hooks/postToolUse.sh`) that:
1. Checks if the written file matches extension paths
2. Runs quick validation checks (JSON parse via `jq`, grep for forbidden tags, required field checks)
3. Outputs issues to stdout — Claude sees them as hook feedback and self-corrects

Fast, advisory, not blocking. Requires `jq` (listed as a dependency in AGENTS.md setup commands). If `jq` is not available, the hook silently skips — validation still happens via the skill workflow.

## Eval Suite

All evals use Claude Code's native skill eval framework (`run_eval.py`). All behavior evals run with `--runs-per-query 3` for multi-trial reliability.

### `build-extension` Evals

**Trigger evals** (~15 cases):
- Should trigger: "build me a widget", "I need a script for analytics", "make something that shows blog posts", "create a stylesheet for our community"
- Should NOT trigger: "write a Python API", "fix this React component", "deploy to production"

**Behavior evals** (~6 scenarios with realistic, vague prompts):

| Scenario | Prompt | Key Assertions |
|----------|--------|----------------|
| Simple widget | "Make a hello world widget" | Creates valid structure, validates, HTML fragment |
| Vague widget | "I want to show our latest blog posts" | Asks clarifying questions, identifies connector need, asks about API source |
| Styled widget | "Build a banner widget, style it like example.com" | Fetches URL, extracts design cues, applies consistent styling |
| Script | "Add analytics tracking to our community" | Asks about page targeting, creates script structure |
| Stylesheet | "Make the community match our brand" | Asks about colors/typography, creates stylesheet with rules |
| Complex widget | "Build a dashboard showing support metrics" | Identifies connector + auth need, asks about API, handles config properties |

Assertions check both **process quality** (asked clarifying questions, fetched docs, followed workflow) and **output quality** (valid structure, correct patterns, no rule violations).

### `validate-extension` Evals

**Trigger evals**: "validate my widget", "check this extension", "is my widget.json correct?" vs "build me a widget", "how do connectors work?"

**Behavior evals**: Pre-built broken extensions as test fixtures — missing required fields, hardcoded secrets, `document.querySelector` instead of `sdk.$()`, `<html>` tags in content.html. Assertions check that the skill identifies each specific issue.

### `hub-reference` Evals

**Trigger evals**: "what auth types exist?", "how does Shadow DOM work here?" vs "build me a widget", "validate this extension"

**Behavior evals**: Framework questions with accuracy assertions — "correctly lists all 5 auth types", "explains sdk.$() vs document.querySelector()", "mentions get_secret() for credentials".

## Implementation Tasks

Replaces original project tasks #2-#5 (port test infra, LLM-as-judge, interactive tests, multi-trial scoring) — all absorbed by the native eval framework.

1. Rewrite `build-extension` skill (from current premature SKILL.md)
2. Create `validate-extension` skill
3. Create `hub-reference` skill (from existing `references/framework-rules.md` content)
4. Create PostToolUse hook (`hooks/postToolUse.sh`)
5. Write eval suites for all three skills (trigger + behavior)
