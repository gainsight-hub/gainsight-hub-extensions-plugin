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

When presenting your questions to the user, always outline the planned extension structure (directory layout, config files, content files) so they understand what will be created. This helps them give better answers.

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
