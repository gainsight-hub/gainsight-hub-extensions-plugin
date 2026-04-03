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
