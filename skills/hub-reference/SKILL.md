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
