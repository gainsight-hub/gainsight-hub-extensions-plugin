# Skill Set Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement three skills (build-extension, validate-extension, hub-reference), a PostToolUse auto-validation hook, and eval suites for all three skills.

**Architecture:** Each skill is a self-contained folder with `SKILL.md` and `evals/`. The hook is defined in `hooks/hooks.json` and implemented in `hooks/validate.sh`. Critical framework rules are baked into each skill that needs them; deeper reference uses Context7/WebFetch.

**Tech Stack:** Claude Code plugin system (SKILL.md with YAML frontmatter), shell scripting (hook), JSON (evals, hook config), `jq` (JSON validation in hook).

**Spec:** `docs/superpowers/specs/2026-04-03-skill-set-design.md`

---

## File Structure

```
gainsight-hub-extensions-plugin/
├── .claude-plugin/
│   └── plugin.json                          # Exists — no changes
├── skills/
│   ├── build-extension/
│   │   ├── SKILL.md                         # Rewrite — interactive build workflow
│   │   └── evals/
│   │       ├── trigger_eval.json            # Create — ~15 trigger cases
│   │       └── evals.json                   # Create — 6 behavior scenarios
│   ├── validate-extension/
│   │   ├── SKILL.md                         # Create — validation checks
│   │   └── evals/
│   │       ├── trigger_eval.json            # Create — ~10 trigger cases
│   │       └── evals.json                   # Create — 4 broken-fixture scenarios
│   └── hub-reference/
│       ├── SKILL.md                         # Create — framework knowledge base
│       └── evals/
│           ├── trigger_eval.json            # Create — ~10 trigger cases
│           └── evals.json                   # Create — 4 accuracy scenarios
└── hooks/
    ├── hooks.json                           # Create — PostToolUse hook config
    └── validate.sh                          # Create — quick validation script
```

**Files to delete after implementation:**
- `skills/build-extension/references/framework-rules.md` — content absorbed into skills
- `skills/build-extension/references/` — empty directory

---

### Task 1: Rewrite `build-extension` Skill

**Files:**
- Rewrite: `skills/build-extension/SKILL.md`
- Delete: `skills/build-extension/references/framework-rules.md`
- Delete: `skills/build-extension/references/` (directory)

- [ ] **Step 1: Write new SKILL.md**

Replace the entire contents of `skills/build-extension/SKILL.md` with:

```markdown
---
name: build-extension
description: Build widgets, stylesheets, scripts, and connectors for Gainsight Customer Hub (Insided) Extensions. Use when the user asks to create, build, or modify any extension — widgets, scripts, stylesheets, or connectors. Also triggers on file patterns in widgets/*/, scripts/*/, stylesheets/*/.
paths:
  - "widgets/*/**"
  - "scripts/*/**"
  - "stylesheets/*/**"
---

# Build Gainsight Hub Extension

Guide the developer through building extensions for the Gainsight Customer Hub (Insided) platform.

## Before You Start

Fetch the official documentation for deeper reference beyond the critical rules below:
1. **Try Context7 first** — resolve "insided" or "gainsight customer hub" and query for widget/extension docs
2. **Fallback** — WebFetch `https://developers.insided.com/docs/llms-full.txt`

If the user references a URL for design inspiration ("style it like xyz.com"), fetch that page and extract design cues (colors, typography, layout patterns) before proceeding.

If building a connector that calls a third-party API, fetch that API's documentation before designing the connector.

## Interactive Workflow

### Step 1: What do you want to build?

Ask the user which type of extension (or infer from context):
- **Widget** — Self-contained HTML component rendered in Shadow DOM (`widgets/<name>/`)
- **Global script** — Page-level JavaScript injected on matching pages (`scripts/<name>/`)
- **Global stylesheet** — Shared CSS applied on matching pages (`stylesheets/<name>/`)

### Step 2: What should it do?

Gather purpose and behavior:
- **Widgets**: Content, interactions, configurability (colors, layout, text via `{{ property_name }}` templates)
- **Scripts**: Page-level behavior (analytics, DOM manipulation, integrations), page targeting rules
- **Stylesheets**: Design tokens, style overrides, target elements, page targeting rules

### Step 3: How should it look?

For widgets and stylesheets, ask about appearance:
- Layout style (grid, list, cards, banner, sidebar)
- Color scheme (brand colors via `var(--config--main-color-brand)`, accent colors)
- Typography (font size, weight, family)
- Responsive behavior

### Step 4: Does the widget need external data?

For widgets, determine data needs:
- **No** — Static content or user-configurable via `configuration` properties and `{{ variable_name }}` templates
- **Yes** — Needs a **connector** for API access via `WidgetServiceSDK`

If yes:
1. Ask where the data comes from (which API/service)
2. Fetch the third-party API documentation
3. Ask what the widget should do with the data
4. Design the connector (`connectors.json`) with URL, method, headers, auth type
5. Widget calls connector via: `const data = await sdk.connectors.execute({ permalink: "name", method: "GET" });`

### Step 5: Build and validate

1. Create directory structure and config files
2. Write content files (HTML/JS/CSS)
3. Run `./bin/build-registry.sh` to rebuild registries
4. Run `./bin/build-registry.sh --validate` to confirm validity

## Critical Rules

### HTML Content (`content.html`)
- Must be an HTML **fragment** — no `<html>`, `<head>`, `<body>` tags
- All CSS must be in `<style>` tags, all JS in `<script>` tags — inline
- No relative imports — use absolute CDN URLs (HTTPS only)
- Template variables: `{{ property_name }}` replaced at runtime from configuration

### Shadow DOM
- DOM queries: use `sdk.$('.selector')` or `sdk.$$('.selector')` — NOT `document.querySelector()`
- Branding: `var(--config--main-color-brand, #fallback)` for community colors
- CSS is automatically scoped — won't leak out, page styles won't affect widget

### widget.json Required Fields
- `version` — semver string (e.g. `"1.0.0"`)
- `title` — display name
- `description` — short description
- `category` — e.g. `"custom"`
- `source` or `content` — exactly one (mutually exclusive)
  - `source`: `{ "path": "dist", "entry": "content.html" }`
  - `content`: `{ "url": "https://..." }`

### Configuration Properties
Types: `text`, `number`, `color`, `select`, `toggle`, `date`, `boolean`
Rules: `required`, `maxLength`, `minLength`, `min`, `max`, `pattern`
Access at runtime: `sdk.getProps()` or `{{ property_name }}` in HTML

### Connectors (`connectors.json`)
- Auth types: `none`, `apikey`, `oauth_client_credentials`, `jwt`, `oauth_jwt_bearer`
- **NEVER hardcode secrets** — use `get_secret('key')` in Jinja2 templates
- Available template variables: `user.id`, `user.email`, `user.name`, `tenant_id`
- Functions: `get_secret(name)`, `now(offset_seconds?)`, `jwt_encode()`
- Filters: `from_json`, `json_encode`, `base64_encode`, `base64_decode`, `default(value)`

### Page Targeting Rules (Scripts & Stylesheets)
Fields: `authenticated` (`"true"`/`"false"`), `pageType` (e.g. `"home"`, `"article"`), `contentType`
Operators: `eq`, `neq`, `in`, `nin`
Default (no rules): loads on all pages

### Limits
- Widget directory: max 100 files or 10 MB total
- No path traversal (`../`)

## Directory Structures

**Widget:**
```
widgets/<name>/
├── widget.json
├── connectors.json      # Optional
└── dist/
    └── content.html
```

**Script:**
```
scripts/<name>/
├── script.json
└── script.js
```

**Stylesheet:**
```
stylesheets/<name>/
├── stylesheet.json
└── style.css
```

## What This Skill Does NOT Do

- **Validation** — the PostToolUse hook auto-validates on every file write. For manual validation, tell the user to ask "validate my widget."
- **Framework Q&A** — for questions like "how do connectors work?" without a build task, the `hub-reference` skill handles that.
```

- [ ] **Step 2: Delete the old references directory**

Run:
```bash
rm -rf skills/build-extension/references/
```

- [ ] **Step 3: Verify the skill file is valid**

Run:
```bash
head -5 skills/build-extension/SKILL.md
```

Expected: YAML frontmatter starting with `---` on line 1, containing `name:`, `description:`, `paths:`.

- [ ] **Step 4: Commit**

```bash
git add skills/build-extension/SKILL.md
git rm -r skills/build-extension/references/
git commit -m "Rewrite build-extension skill with layered docs strategy

Replace monolithic SKILL.md and separate references/ with a single
self-contained skill. Critical rules baked in, deeper reference via
Context7/WebFetch. Interactive 5-step workflow preserved."
```

---

### Task 2: Create `validate-extension` Skill

**Files:**
- Create: `skills/validate-extension/SKILL.md`

- [ ] **Step 1: Create skill directory**

Run:
```bash
mkdir -p skills/validate-extension
```

- [ ] **Step 2: Write SKILL.md**

Create `skills/validate-extension/SKILL.md` with:

```markdown
---
name: validate-extension
description: Validate Gainsight Hub extensions for correctness — structure, schema, content patterns, connector security. Use when the user asks to validate, check, or verify a widget, script, stylesheet, or connector. Triggers on "validate my widget", "check this extension", "is my widget correct".
---

# Validate Gainsight Hub Extension

Run validation checks on extensions in this repository. Reports a structured checklist of pass/fail per category.

## How to Validate

When the user asks to validate an extension, run all checks below against the specified extension (or all extensions if none specified). Report results as a checklist.

### 1. Structure Checks

- [ ] Extension directory exists (`widgets/<name>/`, `scripts/<name>/`, or `stylesheets/<name>/`)
- [ ] Required config file exists (`widget.json`, `script.json`, or `stylesheet.json`)
- [ ] For widgets: `dist/content.html` exists (or content URL in widget.json)
- [ ] Config file is valid JSON (parse with `jq .`)

### 2. Schema Checks

**widget.json:**
- [ ] Has `version` (string, semver format)
- [ ] Has `title` (string, non-empty)
- [ ] Has `description` (string, non-empty)
- [ ] Has `category` (string)
- [ ] Has exactly one of `source` or `content` (not both, not neither)
- [ ] If `source`: has `path` and `entry` fields
- [ ] If `content`: has `url` field (HTTPS)
- [ ] If `configuration` exists: each property has `type` field with valid value (`text`, `number`, `color`, `select`, `toggle`, `date`, `boolean`)

**script.json:**
- [ ] Has `name` (string)
- [ ] Has `description` (string)
- [ ] If `placement` exists: value is `"head"` or `"body"`

**stylesheet.json:**
- [ ] Has `name` (string)
- [ ] Has `description` (string)

### 3. Content Checks

**content.html (widgets):**
- [ ] No `<html>`, `<head>`, or `<body>` tags (must be HTML fragment)
- [ ] No `document.querySelector` or `document.querySelectorAll` — use `sdk.$()` / `sdk.$$()`
- [ ] No relative imports (no `src="./` or `href="./` patterns)
- [ ] CDN URLs use HTTPS (no `http://` URLs)

**script.js (scripts):**
- [ ] File exists and is non-empty

**style.css (stylesheets):**
- [ ] File exists and is non-empty

### 4. Connector Checks (if `connectors.json` exists)

- [ ] Valid JSON
- [ ] Each connector has `name`, `url`, `method`
- [ ] Auth type is valid: `none`, `apikey`, `oauth_client_credentials`, `jwt`, `oauth_jwt_bearer`
- [ ] No hardcoded secrets — credentials use `get_secret('key')` pattern
- [ ] No plaintext API keys, tokens, or passwords in values

### 5. Registry Check

- [ ] Run `./bin/build-registry.sh --validate` — exits with code 0

## Output Format

Report results grouped by category:

```
## Validation: <extension_name>

### Structure ✓
- ✓ Directory exists
- ✓ widget.json exists
- ✓ dist/content.html exists

### Schema (2 issues)
- ✓ Has version
- ✗ Missing description
- ✗ Has both source and content (must be exactly one)
...

### Summary: 15/18 checks passed
```

## What This Skill Does NOT Do

- **Build extensions** — that's `build-extension`
- **Answer framework questions** — that's `hub-reference`
- **Score or grade** — this is binary pass/fail per check, not a quality score
```

- [ ] **Step 3: Commit**

```bash
git add skills/validate-extension/SKILL.md
git commit -m "Create validate-extension skill

Structured validation with 5 check categories: structure, schema,
content patterns, connector security, and registry build. Reports
pass/fail checklist per category."
```

---

### Task 3: Create `hub-reference` Skill

**Files:**
- Create: `skills/hub-reference/SKILL.md`

- [ ] **Step 1: Create skill directory**

Run:
```bash
mkdir -p skills/hub-reference
```

- [ ] **Step 2: Write SKILL.md**

Create `skills/hub-reference/SKILL.md` with:

```markdown
---
name: hub-reference
description: Answer questions about the Gainsight Customer Hub (Insided) Extensions framework — widget structure, configuration schemas, connector auth types, Shadow DOM patterns, SDK usage, page targeting rules, registry commands. Use when the user asks how something works in the framework without asking to build anything.
---

# Gainsight Hub Extensions Framework Reference

Answer framework questions using this knowledge base. For deeper or more current information:
1. **Try Context7 first** — resolve "insided" or "gainsight customer hub" and query for the specific topic
2. **Fallback** — WebFetch `https://developers.insided.com/docs/llms-full.txt`

When relevant, point to existing extensions in the repo as examples.

## Extension Types

| Type | Directory | Config File | Content File |
|------|-----------|-------------|-------------|
| Widget | `widgets/<name>/` | `widget.json` | `dist/content.html` |
| Script | `scripts/<name>/` | `script.json` | `script.js` |
| Stylesheet | `stylesheets/<name>/` | `stylesheet.json` | `style.css` |

## widget.json Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Semver (e.g. `"1.0.0"`) |
| `title` | string | Display name |
| `description` | string | Short description |
| `category` | string | e.g. `"custom"` |
| `source` or `content` | object | Exactly one — mutually exclusive |

`source` (repo-hosted): `{ "path": "dist", "entry": "content.html" }`
`content` (external): `{ "url": "https://..." }`

### Optional Fields

- `containers`: array of layouts (`"Full width"`, `"Left container"`, `"Sidebar"`)
- `widgetsLibrary`: boolean
- `imageSrc` or `imageName`: only one
- `settings`: `configurable`, `editable`, `removable`, `shared`, `movable`
- `configuration`: array of property definitions
- `defaultConfig`: default values

### Configuration Properties

Types: `text`, `number`, `color`, `select`, `toggle`, `date`, `boolean`
Rules: `required`, `maxLength`, `minLength`, `min`, `max`, `pattern`
Access at runtime: `sdk.getProps()` and `{{ property_name }}` template variables

### Limits

- Widget directory: max 100 files or 10 MB total
- No path traversal (`../`)

## Shadow DOM and content.html

- Widgets render inside Shadow DOM — styles are scoped and isolated
- CSS won't leak out; page styles won't affect the widget
- DOM queries: `sdk.$('.selector')` or `sdk.$$('.selector')` — NOT `document.querySelector()`
- Branding: `var(--config--main-color-brand, #fallback)`
- Must be HTML fragment — no `<html>`, `<head>`, `<body>` tags
- All CSS/JS inline or from CDN URLs — no relative file references

## Connector Authentication Types

Always use `get_secret('key')` for credentials — never hardcode.

| Type | Description | Key Config Fields |
|------|-------------|-------------------|
| `none` | No authentication | — |
| `apikey` | API key in header or query | `key`, `value`, `in` (`"header"` or `"query"`) |
| `oauth_client_credentials` | Client credentials grant, auto token caching | `client_id`, `client_secret`, `token_url`, `scope` |
| `jwt` | Signed JWT on every request | `private_key`, `algorithm`, `claims`, `headers` |
| `oauth_jwt_bearer` | JWT assertion exchanged for access token | `client_id`, `private_key`, `token_url`, `subject`, `audience`, `token_ttl`, `algorithm` |

### Jinja2 Template Variables

Variables: `user.id`, `user.email`, `user.name`, `tenant_id`, `body_text`, `body_raw`
Functions: `get_secret(name)`, `now(offset_seconds?)`, `jwt_encode()`
Filters: `from_json`, `json_encode`, `base64_encode`, `base64_decode`, `default(value)`

## Page Targeting Rules (Scripts & Stylesheets)

| Field | Values |
|-------|--------|
| `authenticated` | `"true"` / `"false"` |
| `pageType` | `"home"`, `"article"`, etc. |
| `contentType` | `"article"`, `"question"`, `"conversation"`, `"idea"`, `"productUpdate"` |

Operators: `eq`, `neq`, `in`, `nin`

Default (no rules): `[{"field":"pageType","operator":"in","value":["global"]}]` — loads on all pages.

Example — only authenticated, non-home pages:
```json
"rules": [
  { "field": "authenticated", "operator": "eq", "value": "true" },
  { "field": "pageType", "operator": "neq", "value": "home" }
]
```

## Commands

| Command | Description |
|---------|-------------|
| `./bin/build-registry.sh` | Build widget and connector registries |
| `./bin/build-registry.sh --dry-run` | Preview without writing files |
| `./bin/build-registry.sh --validate` | Validate existing registries |
| `jq . widgets/<name>/widget.json` | Check JSON syntax |

## What This Skill Does NOT Do

- **Build extensions** — that's `build-extension`
- **Validate extensions** — that's `validate-extension`
```

- [ ] **Step 3: Commit**

```bash
git add skills/hub-reference/SKILL.md
git commit -m "Create hub-reference skill

Framework knowledge base covering widget.json schema, Shadow DOM
patterns, connector auth types, page targeting rules, and commands.
Layered docs: critical rules in-skill, Context7/WebFetch for deeper ref."
```

---

### Task 4: Create PostToolUse Hook

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/validate.sh`

- [ ] **Step 1: Create hooks directory**

Run:
```bash
mkdir -p hooks
```

- [ ] **Step 2: Write hooks.json**

Create `hooks/hooks.json` with:

```json
{
  "description": "Auto-validate extension files on write/edit",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/validate.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Write validate.sh**

Create `hooks/validate.sh` with:

```bash
#!/usr/bin/env bash
# PostToolUse hook: quick validation of extension files
# Receives tool input via stdin as JSON. Checks JSON syntax,
# HTML fragment rules, and required fields.

set -euo pipefail

# Read stdin (tool use data from Claude Code)
INPUT=$(cat)

# Extract file path from tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Exit silently if no file path (shouldn't happen for Write/Edit)
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Only validate files in extension directories
case "$FILE_PATH" in
  */widgets/*|*/scripts/*|*/stylesheets/*) ;;
  *) exit 0 ;;
esac

ISSUES=()

# Get the filename
FILENAME=$(basename "$FILE_PATH")

# --- JSON syntax check ---
case "$FILENAME" in
  widget.json|connectors.json|script.json|stylesheet.json)
    if command -v jq &>/dev/null; then
      if ! jq empty "$FILE_PATH" 2>/dev/null; then
        ISSUES+=("ERROR: $FILENAME has invalid JSON syntax")
      fi
    fi
    ;;
esac

# --- widget.json required fields ---
if [[ "$FILENAME" == "widget.json" ]] && command -v jq &>/dev/null && jq empty "$FILE_PATH" 2>/dev/null; then
  for field in version title description category; do
    val=$(jq -r ".$field // empty" "$FILE_PATH" 2>/dev/null)
    if [[ -z "$val" ]]; then
      ISSUES+=("ERROR: widget.json missing required field: $field")
    fi
  done
  has_source=$(jq -r '.source // empty' "$FILE_PATH" 2>/dev/null)
  has_content=$(jq -r '.content // empty' "$FILE_PATH" 2>/dev/null)
  if [[ -z "$has_source" && -z "$has_content" ]]; then
    ISSUES+=("ERROR: widget.json must have either 'source' or 'content'")
  fi
  if [[ -n "$has_source" && -n "$has_content" ]]; then
    ISSUES+=("ERROR: widget.json must have 'source' or 'content', not both")
  fi
fi

# --- HTML fragment check ---
if [[ "$FILENAME" == "content.html" ]]; then
  if grep -qiE '<html[ >]|<head[ >]|<body[ >]' "$FILE_PATH" 2>/dev/null; then
    ISSUES+=("ERROR: content.html must be an HTML fragment — remove <html>, <head>, <body> tags")
  fi
  if grep -qE 'document\.querySelector|document\.querySelectorAll' "$FILE_PATH" 2>/dev/null; then
    ISSUES+=("WARNING: Use sdk.\$() or sdk.\$\$() instead of document.querySelector() — widgets run in Shadow DOM")
  fi
  if grep -qE 'src="\.\/|href="\.\/|src="\.\.|href="\.\.' "$FILE_PATH" 2>/dev/null; then
    ISSUES+=("ERROR: No relative imports — use absolute CDN URLs")
  fi
  if grep -qE 'http://' "$FILE_PATH" 2>/dev/null; then
    ISSUES+=("WARNING: Use HTTPS for CDN URLs, not HTTP")
  fi
fi

# --- Connector security check ---
if [[ "$FILENAME" == "connectors.json" ]] && command -v jq &>/dev/null && jq empty "$FILE_PATH" 2>/dev/null; then
  # Check for hardcoded secrets (values that look like API keys/tokens but don't use get_secret)
  if jq -r '.. | strings' "$FILE_PATH" 2>/dev/null | grep -qiE '(api.?key|token|secret|password|bearer)' | grep -v 'get_secret'; then
    ISSUES+=("WARNING: Possible hardcoded secret detected — use get_secret('key') in connectors")
  fi
fi

# Output issues if any
if [[ ${#ISSUES[@]} -gt 0 ]]; then
  echo "⚠️ Extension validation issues:"
  for issue in "${ISSUES[@]}"; do
    echo "  • $issue"
  done
fi

exit 0
```

- [ ] **Step 4: Make validate.sh executable**

Run:
```bash
chmod +x hooks/validate.sh
```

- [ ] **Step 5: Test the hook script with a sample input**

Run:
```bash
echo '{"tool_input":{"file_path":"/tmp/test-widget.json","content":"{}"}}' | ./hooks/validate.sh
```

Expected output (missing required fields):
```
⚠️ Extension validation issues:
```

Note: This test won't find issues because `/tmp/test-widget.json` doesn't exist in an extension path. The path filter (`*/widgets/*`) will skip it. This just verifies the script runs without errors.

- [ ] **Step 6: Commit**

```bash
git add hooks/hooks.json hooks/validate.sh
git commit -m "Create PostToolUse auto-validation hook

Validates extension files on every Write/Edit: JSON syntax, widget.json
required fields, HTML fragment rules, Shadow DOM patterns, connector
security. Advisory only — reports issues, does not block."
```

---

### Task 5: Write `build-extension` Evals

**Files:**
- Create: `skills/build-extension/evals/trigger_eval.json`
- Create: `skills/build-extension/evals/evals.json`

- [ ] **Step 1: Create evals directory**

Run:
```bash
mkdir -p skills/build-extension/evals
```

- [ ] **Step 2: Write trigger_eval.json**

Create `skills/build-extension/evals/trigger_eval.json` with:

```json
[
  {"query": "Build me a widget that shows recent blog posts", "should_trigger": true},
  {"query": "Create a new widget for our community page", "should_trigger": true},
  {"query": "I need a script for analytics tracking", "should_trigger": true},
  {"query": "Make a stylesheet that matches our brand", "should_trigger": true},
  {"query": "Add a connector to the weather API", "should_trigger": true},
  {"query": "I want to show our latest blog posts on the community", "should_trigger": true},
  {"query": "Build a banner with a call to action button", "should_trigger": true},
  {"query": "Create something that shows support metrics from our API", "should_trigger": true},
  {"query": "Make the community look like our main website", "should_trigger": true},
  {"query": "I need a widget that lets users submit feedback", "should_trigger": true},

  {"query": "Write a Python API endpoint for user authentication", "should_trigger": false},
  {"query": "Fix this React component's rendering bug", "should_trigger": false},
  {"query": "Deploy our app to production", "should_trigger": false},
  {"query": "How do connectors work in Insided?", "should_trigger": false},
  {"query": "Validate my widget", "should_trigger": false},
  {"query": "What auth types are available for connectors?", "should_trigger": false},
  {"query": "Review this pull request", "should_trigger": false},
  {"query": "Set up CI/CD for this project", "should_trigger": false}
]
```

- [ ] **Step 3: Write evals.json**

Create `skills/build-extension/evals/evals.json` with:

```json
{
  "skill_name": "build-extension",
  "evals": [
    {
      "id": 1,
      "prompt": "Make a hello world widget",
      "expected_output": "Creates a widget with valid structure (widget.json + dist/content.html), HTML fragment with heading and paragraph, runs registry build.",
      "files": [],
      "assertions": [
        {
          "name": "creates-widget-json",
          "text": "Creates a widget.json file with required fields (version, title, description, category, source)",
          "type": "transcript"
        },
        {
          "name": "creates-content-html",
          "text": "Creates a dist/content.html file that is an HTML fragment (no <html>, <head>, <body> tags)",
          "type": "transcript"
        },
        {
          "name": "runs-registry-build",
          "text": "Runs ./bin/build-registry.sh or ./bin/build-registry.sh --validate",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 2,
      "prompt": "I want to show our latest blog posts on the community",
      "expected_output": "Asks clarifying questions about the data source (which blog API/RSS feed), identifies the need for a connector, asks what to display from each post. Does not immediately start building.",
      "files": [],
      "assertions": [
        {
          "name": "asks-about-data-source",
          "text": "Asks the user where the blog posts come from (which API, RSS feed, or service) before building",
          "type": "transcript"
        },
        {
          "name": "identifies-connector-need",
          "text": "Identifies that this requires a connector for external data access",
          "type": "transcript"
        },
        {
          "name": "does-not-build-immediately",
          "text": "Does NOT create files or write code before gathering requirements from the user",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 3,
      "prompt": "Build a banner widget, style it like https://stripe.com",
      "expected_output": "Fetches stripe.com to extract design cues (colors, typography, layout). Creates a banner widget with styling inspired by the reference. Uses HTML fragment format.",
      "files": [],
      "assertions": [
        {
          "name": "fetches-reference-url",
          "text": "Uses WebFetch to retrieve the referenced URL (stripe.com) for design inspiration",
          "type": "transcript"
        },
        {
          "name": "extracts-design-cues",
          "text": "Identifies or describes design elements from the reference (colors, fonts, or layout patterns)",
          "type": "transcript"
        },
        {
          "name": "creates-valid-widget",
          "text": "Creates widget.json and dist/content.html with valid structure",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 4,
      "prompt": "Add analytics tracking to our community",
      "expected_output": "Identifies this as a global script (not a widget). Asks about which analytics provider and which pages to target. Creates script.json with appropriate page targeting rules.",
      "files": [],
      "assertions": [
        {
          "name": "identifies-script-type",
          "text": "Identifies this as a global script rather than a widget",
          "type": "transcript"
        },
        {
          "name": "asks-about-targeting",
          "text": "Asks which pages the script should load on, or which analytics provider to use",
          "type": "transcript"
        },
        {
          "name": "creates-script-structure",
          "text": "Creates script.json and script.js in a scripts/<name>/ directory",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 5,
      "prompt": "Make the community match our brand colors",
      "expected_output": "Identifies this as a global stylesheet. Asks about brand colors, typography, and which elements to target. Creates stylesheet.json with rules.",
      "files": [],
      "assertions": [
        {
          "name": "identifies-stylesheet-type",
          "text": "Identifies this as a global stylesheet rather than a widget",
          "type": "transcript"
        },
        {
          "name": "asks-about-brand",
          "text": "Asks about specific brand colors, typography, or which elements to style",
          "type": "transcript"
        },
        {
          "name": "creates-stylesheet-structure",
          "text": "Creates stylesheet.json and style.css in a stylesheets/<name>/ directory",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 6,
      "prompt": "Build a dashboard showing support metrics from our internal API at api.example.com/metrics. It requires an API key.",
      "expected_output": "Creates a widget with a connector using apikey auth and get_secret(). Asks what metrics to display and how to visualize them. Uses configuration properties for customization.",
      "files": [],
      "assertions": [
        {
          "name": "creates-connector-with-auth",
          "text": "Creates connectors.json with apikey authentication type using get_secret() for the API key",
          "type": "transcript"
        },
        {
          "name": "asks-about-visualization",
          "text": "Asks what metrics to show or how to visualize the data",
          "type": "transcript"
        },
        {
          "name": "uses-sdk-connector-execute",
          "text": "Widget code calls sdk.connectors.execute() to fetch data from the connector",
          "type": "transcript"
        },
        {
          "name": "no-hardcoded-secrets",
          "text": "Does NOT hardcode any API keys or secrets in the connector config — uses get_secret()",
          "type": "transcript"
        }
      ]
    }
  ]
}
```

- [ ] **Step 4: Commit**

```bash
git add skills/build-extension/evals/
git commit -m "Add build-extension eval suite

18 trigger evals (10 should-trigger, 8 should-not) and 6 behavior
scenarios testing realistic vague prompts. Assertions check both
process quality and output correctness."
```

---

### Task 6: Write `validate-extension` Evals

**Files:**
- Create: `skills/validate-extension/evals/trigger_eval.json`
- Create: `skills/validate-extension/evals/evals.json`

- [ ] **Step 1: Create evals directory**

Run:
```bash
mkdir -p skills/validate-extension/evals
```

- [ ] **Step 2: Write trigger_eval.json**

Create `skills/validate-extension/evals/trigger_eval.json` with:

```json
[
  {"query": "Validate my widget", "should_trigger": true},
  {"query": "Check this extension for errors", "should_trigger": true},
  {"query": "Is my widget.json correct?", "should_trigger": true},
  {"query": "Are there any issues with my connector config?", "should_trigger": true},
  {"query": "Run validation on the blog_posts widget", "should_trigger": true},

  {"query": "Build me a widget", "should_trigger": false},
  {"query": "How do connectors work?", "should_trigger": false},
  {"query": "Create a stylesheet for our community", "should_trigger": false},
  {"query": "What auth types are available?", "should_trigger": false},
  {"query": "Deploy this widget to production", "should_trigger": false}
]
```

- [ ] **Step 3: Write evals.json**

Create `skills/validate-extension/evals/evals.json` with:

```json
{
  "skill_name": "validate-extension",
  "evals": [
    {
      "id": 1,
      "prompt": "Validate the broken_widget widget",
      "expected_output": "Identifies missing required fields in widget.json, reports structured checklist.",
      "files": [
        "widgets/broken_widget/widget.json",
        "widgets/broken_widget/dist/content.html"
      ],
      "assertions": [
        {
          "name": "checks-required-fields",
          "text": "Identifies missing or invalid required fields in widget.json (version, title, description, category, source/content)",
          "type": "transcript"
        },
        {
          "name": "reports-structured-output",
          "text": "Reports results in a structured format with categories (structure, schema, content, etc.)",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 2,
      "prompt": "Check the insecure_widget for issues",
      "expected_output": "Identifies hardcoded secrets in connectors.json, flags document.querySelector usage, reports security issues.",
      "files": [
        "widgets/insecure_widget/widget.json",
        "widgets/insecure_widget/dist/content.html",
        "widgets/insecure_widget/connectors.json"
      ],
      "assertions": [
        {
          "name": "flags-hardcoded-secrets",
          "text": "Identifies hardcoded secrets or API keys in connectors.json and recommends get_secret()",
          "type": "transcript"
        },
        {
          "name": "flags-document-queryselector",
          "text": "Identifies document.querySelector usage and recommends sdk.$() for Shadow DOM",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 3,
      "prompt": "Validate the invalid_html widget",
      "expected_output": "Identifies <html>, <head>, or <body> tags in content.html and explains it must be an HTML fragment.",
      "files": [
        "widgets/invalid_html/widget.json",
        "widgets/invalid_html/dist/content.html"
      ],
      "assertions": [
        {
          "name": "flags-non-fragment-html",
          "text": "Identifies that content.html contains <html>, <head>, or <body> tags and must be an HTML fragment",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 4,
      "prompt": "Run validation on all widgets in this repo",
      "expected_output": "Validates all widgets found in the widgets/ directory, reports per-widget results.",
      "files": [],
      "assertions": [
        {
          "name": "discovers-all-widgets",
          "text": "Scans the widgets/ directory to find all widgets rather than asking which one to validate",
          "type": "transcript"
        },
        {
          "name": "validates-each-widget",
          "text": "Runs validation checks against each discovered widget and reports results per widget",
          "type": "transcript"
        }
      ]
    }
  ]
}
```

- [ ] **Step 4: Commit**

```bash
git add skills/validate-extension/evals/
git commit -m "Add validate-extension eval suite

10 trigger evals and 4 behavior scenarios testing detection of broken
widgets, hardcoded secrets, invalid HTML, and batch validation."
```

---

### Task 7: Write `hub-reference` Evals

**Files:**
- Create: `skills/hub-reference/evals/trigger_eval.json`
- Create: `skills/hub-reference/evals/evals.json`

- [ ] **Step 1: Create evals directory**

Run:
```bash
mkdir -p skills/hub-reference/evals
```

- [ ] **Step 2: Write trigger_eval.json**

Create `skills/hub-reference/evals/trigger_eval.json` with:

```json
[
  {"query": "What auth types are available for connectors?", "should_trigger": true},
  {"query": "How does Shadow DOM work in Insided widgets?", "should_trigger": true},
  {"query": "What configuration property types can I use?", "should_trigger": true},
  {"query": "How do page targeting rules work for scripts?", "should_trigger": true},
  {"query": "What's the widget.json schema?", "should_trigger": true},

  {"query": "Build me a widget", "should_trigger": false},
  {"query": "Validate my extension", "should_trigger": false},
  {"query": "Create a stylesheet for the community", "should_trigger": false},
  {"query": "Write a Python script", "should_trigger": false},
  {"query": "Check my widget.json for errors", "should_trigger": false}
]
```

- [ ] **Step 3: Write evals.json**

Create `skills/hub-reference/evals/evals.json` with:

```json
{
  "skill_name": "hub-reference",
  "evals": [
    {
      "id": 1,
      "prompt": "What authentication types can I use for connectors?",
      "expected_output": "Lists all 5 connector auth types with descriptions: none, apikey, oauth_client_credentials, jwt, oauth_jwt_bearer. Mentions get_secret() for credentials.",
      "files": [],
      "assertions": [
        {
          "name": "lists-all-auth-types",
          "text": "Lists all 5 authentication types: none, apikey, oauth_client_credentials, jwt, oauth_jwt_bearer",
          "type": "transcript"
        },
        {
          "name": "mentions-get-secret",
          "text": "Mentions get_secret() as the way to handle credentials securely",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 2,
      "prompt": "How do I query the DOM from inside a widget?",
      "expected_output": "Explains Shadow DOM isolation, recommends sdk.$() and sdk.$$() instead of document.querySelector, mentions branding CSS custom properties.",
      "files": [],
      "assertions": [
        {
          "name": "explains-shadow-dom",
          "text": "Explains that widgets run inside Shadow DOM and standard DOM queries won't work",
          "type": "transcript"
        },
        {
          "name": "recommends-sdk-selectors",
          "text": "Recommends sdk.$() and sdk.$$() as replacements for document.querySelector and document.querySelectorAll",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 3,
      "prompt": "What types can I use for configuration properties?",
      "expected_output": "Lists all configuration property types: text, number, color, select, toggle, date, boolean. Explains how to access them at runtime.",
      "files": [],
      "assertions": [
        {
          "name": "lists-property-types",
          "text": "Lists the configuration property types including at least: text, number, color, select, toggle, boolean",
          "type": "transcript"
        },
        {
          "name": "explains-runtime-access",
          "text": "Explains how to access configuration values at runtime (sdk.getProps() or {{ property_name }} templates)",
          "type": "transcript"
        }
      ]
    },
    {
      "id": 4,
      "prompt": "How do page targeting rules work for scripts and stylesheets?",
      "expected_output": "Explains the rules system with fields (authenticated, pageType, contentType), operators (eq, neq, in, nin), and default behavior.",
      "files": [],
      "assertions": [
        {
          "name": "explains-rule-fields",
          "text": "Describes the available rule fields: authenticated, pageType, and contentType",
          "type": "transcript"
        },
        {
          "name": "explains-operators",
          "text": "Lists the available operators: eq, neq, in, nin",
          "type": "transcript"
        }
      ]
    }
  ]
}
```

- [ ] **Step 4: Commit**

```bash
git add skills/hub-reference/evals/
git commit -m "Add hub-reference eval suite

10 trigger evals and 4 behavior scenarios testing accuracy of
framework knowledge: auth types, Shadow DOM, config properties,
page targeting rules."
```

---

### Task 8: Create Test Fixtures for Validate Evals

The `validate-extension` behavior evals reference broken widget fixtures that need to exist in the target repo for evals to work. These should be created as part of the eval setup.

**Files:**
- Create: `skills/validate-extension/evals/fixtures/broken_widget/widget.json`
- Create: `skills/validate-extension/evals/fixtures/broken_widget/dist/content.html`
- Create: `skills/validate-extension/evals/fixtures/insecure_widget/widget.json`
- Create: `skills/validate-extension/evals/fixtures/insecure_widget/dist/content.html`
- Create: `skills/validate-extension/evals/fixtures/insecure_widget/connectors.json`
- Create: `skills/validate-extension/evals/fixtures/invalid_html/widget.json`
- Create: `skills/validate-extension/evals/fixtures/invalid_html/dist/content.html`
- Create: `skills/validate-extension/evals/fixtures/README.md`

- [ ] **Step 1: Create fixture directories**

Run:
```bash
mkdir -p skills/validate-extension/evals/fixtures/broken_widget/dist
mkdir -p skills/validate-extension/evals/fixtures/insecure_widget/dist
mkdir -p skills/validate-extension/evals/fixtures/invalid_html/dist
```

- [ ] **Step 2: Create broken_widget fixture (missing required fields)**

Create `skills/validate-extension/evals/fixtures/broken_widget/widget.json` with:
```json
{
  "version": "1.0.0",
  "title": "Broken Widget"
}
```

Create `skills/validate-extension/evals/fixtures/broken_widget/dist/content.html` with:
```html
<div>
  <h2>Broken Widget</h2>
  <p>This widget is missing required fields in widget.json.</p>
</div>
```

- [ ] **Step 3: Create insecure_widget fixture (hardcoded secrets + bad DOM access)**

Create `skills/validate-extension/evals/fixtures/insecure_widget/widget.json` with:
```json
{
  "version": "1.0.0",
  "title": "Insecure Widget",
  "description": "Widget with security issues",
  "category": "custom",
  "source": { "path": "dist", "entry": "content.html" }
}
```

Create `skills/validate-extension/evals/fixtures/insecure_widget/dist/content.html` with:
```html
<div id="data-container">
  <h2>Dashboard</h2>
  <div class="content"></div>
</div>
<script>
  const sdk = new window.WidgetServiceSDK();
  // BUG: Should use sdk.$() not document.querySelector
  const container = document.querySelector('.content');
  const data = await sdk.connectors.execute({ permalink: "my-api", method: "GET" });
  container.innerHTML = JSON.stringify(data);
</script>
```

Create `skills/validate-extension/evals/fixtures/insecure_widget/connectors.json` with:
```json
[
  {
    "name": "my-api",
    "url": "https://api.example.com/data",
    "method": "GET",
    "authentication": {
      "type": "apikey",
      "config": {
        "key": "X-API-Key",
        "value": "sk-1234567890abcdef",
        "in": "header"
      }
    }
  }
]
```

- [ ] **Step 4: Create invalid_html fixture (full HTML document instead of fragment)**

Create `skills/validate-extension/evals/fixtures/invalid_html/widget.json` with:
```json
{
  "version": "1.0.0",
  "title": "Invalid HTML Widget",
  "description": "Widget with full HTML document instead of fragment",
  "category": "custom",
  "source": { "path": "dist", "entry": "content.html" }
}
```

Create `skills/validate-extension/evals/fixtures/invalid_html/dist/content.html` with:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>My Widget</title>
  <style>
    .widget { padding: 20px; }
  </style>
</head>
<body>
  <div class="widget">
    <h2>Hello World</h2>
    <p>This is a widget that incorrectly uses a full HTML document.</p>
  </div>
</body>
</html>
```

- [ ] **Step 5: Create README explaining fixtures**

Create `skills/validate-extension/evals/fixtures/README.md` with:
```markdown
# Validation Eval Fixtures

Intentionally broken widgets used by the validate-extension behavior evals.

| Fixture | Issues |
|---------|--------|
| `broken_widget` | Missing `description`, `category`, and `source`/`content` in widget.json |
| `insecure_widget` | Hardcoded API key in connectors.json, `document.querySelector` instead of `sdk.$()` |
| `invalid_html` | Full HTML document (`<html>`, `<head>`, `<body>`) instead of HTML fragment |

These fixtures are copied into the eval workspace before running behavior evals.
```

- [ ] **Step 6: Update validate-extension evals.json to reference fixtures**

Edit `skills/validate-extension/evals/evals.json` — update the `files` arrays to point at fixture paths:

Replace the `files` field in eval id 1:
```json
"files": [
  "skills/validate-extension/evals/fixtures/broken_widget/widget.json",
  "skills/validate-extension/evals/fixtures/broken_widget/dist/content.html"
]
```

Replace the `files` field in eval id 2:
```json
"files": [
  "skills/validate-extension/evals/fixtures/insecure_widget/widget.json",
  "skills/validate-extension/evals/fixtures/insecure_widget/dist/content.html",
  "skills/validate-extension/evals/fixtures/insecure_widget/connectors.json"
]
```

Replace the `files` field in eval id 3:
```json
"files": [
  "skills/validate-extension/evals/fixtures/invalid_html/widget.json",
  "skills/validate-extension/evals/fixtures/invalid_html/dist/content.html"
]
```

- [ ] **Step 7: Commit**

```bash
git add skills/validate-extension/evals/fixtures/ skills/validate-extension/evals/evals.json
git commit -m "Add test fixtures for validate-extension evals

Three intentionally broken widgets: missing fields, hardcoded secrets
with bad DOM access, and full HTML document instead of fragment."
```

---

### Task 9: Update Project Tasks and Clean Up

**Files:**
- No files — task management only

- [ ] **Step 1: Delete obsolete project tasks**

Delete tasks #2 (port test infra), #3 (LLM-as-judge), #4 (interactive workflow tests), #5 (multi-trial scoring) — all absorbed by the native eval framework.

- [ ] **Step 2: Verify final plugin structure**

Run:
```bash
find . -type f -not -path './.git/*' -not -path './.claude/*' -not -path './docs/superpowers/*' | sort
```

Expected output should match the file structure defined at the top of this plan.

- [ ] **Step 3: Final commit (if any cleanup needed)**

```bash
git status
```

If clean, no commit needed. If there are leftover files to clean up, commit them.
