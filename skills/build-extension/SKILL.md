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

The goal is a natural, focused conversation — not an interrogation. Ask 2-3 questions at a time, propose a concrete direction, and wait for the user to respond before moving on. Users should feel like they're collaborating with a designer, not filling out a form.

### Conversational principles

- **2-3 questions max per turn.** Prioritize the questions that most change what you'd build. You can always ask follow-ups later.
- **Propose, don't just ask.** Instead of "what layout do you want?" say "I'm thinking a full-width banner with a gradient background and CTA button — does that sound right, or were you thinking more of a compact card?" Give the user something to react to.
- **Wait for the user.** Never self-answer your own questions. If the user hasn't responded, stop and wait. Do not proceed to build with assumed defaults unless the user explicitly says to go ahead.
- **Infer from context.** If the user says "small notification bar", you already know the layout — don't ask about layout. Focus questions on what you genuinely can't infer.

### Step 1: Identify the extension type

Determine which type (or infer from context):
- **Widget** — Self-contained HTML component rendered in Shadow DOM (`widgets/<name>/`)
- **Global script** — Page-level JavaScript injected on matching pages (`scripts/<name>/`)
- **Global stylesheet** — Shared CSS applied on matching pages (`stylesheets/<name>/`)

Outline the planned directory structure so the user understands what will be created.

### Step 2: Gather requirements (conversationally)

Combine purpose, appearance, and data questions into a natural flow rather than rigid separate steps. In your first response after identifying the type, ask the 2-3 most important questions and propose a direction:

**For widgets**, the key questions are:
- What content/data should it show? (And where does that data come from — manual config vs API?)
- What visual format fits? (Propose one based on context: banner, card, table, gauge, etc.)
- Any specific design inspiration? (If they mention a URL, fetch it for design cues)

**For scripts**: What behavior, which pages, which provider?
**For stylesheets**: What elements, brand colors, which pages?

**If the request implies external data (mentions an API, service name, or "pull/fetch/show data from X"), your first response MUST identify the connector need and propose a concrete auth pattern.** Don't defer this to a later turn — connector identification is as important as layout choice. Example: "Since the NPS data comes from Delighted, I'd set up a connector with apikey auth using `get_secret('delighted_api_key')` — the widget would call `sdk.connectors.execute({ permalink: 'delighted-nps', method: 'GET' })` to fetch the score. Sound right?"

### Step 3: Build and validate

Once you have enough context (the user has answered at least one round of questions, or the request is specific enough to build directly):

1. Create directory structure and config files
2. Write content files (HTML/JS/CSS)
3. Run `./bin/build-registry.sh` to rebuild registries
4. Run `./bin/build-registry.sh --validate` to confirm validity

## Design Quality

Widgets should look like they were built by an experienced frontend developer. Users notice when something feels "off" even if they can't articulate why. These patterns make the difference:

### Spacing and layout
- Use a consistent spacing scale — multiples of 4px or 8px (e.g., 4, 8, 12, 16, 24, 32, 48). Avoid arbitrary values like 13px or 37px.
- Use `rem` for typography and `px` for borders/shadows. This keeps text responsive while keeping decorative elements crisp.
- Use flexbox or CSS grid for layout — never rely on floats or manual positioning.

### Typography
- Establish clear hierarchy: at minimum 2 distinct levels (e.g., heading at 1.5rem/600 weight, body at 0.875rem/400 weight).
- Use a system font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` or load a specific font via HTTPS CDN.
- Consider `letter-spacing` for headings (tight: -0.02em) and small caps/labels (wide: 0.05em).

### Visual polish
- Every card/container needs at least 2 of: `border-radius`, `box-shadow`, subtle `border`, background differentiation.
- Interactive elements (buttons, links, clickable rows) need `:hover` and `:focus` states with transitions (`transition: all 0.15s ease`).
- Use `clamp()` for responsive font sizes: `font-size: clamp(1rem, 2.5vw, 1.5rem)`.
- Add `@media` queries for mobile breakpoints (typically 600px or 768px).

### Data display
- Right-align numeric columns in tables. Use `font-variant-numeric: tabular-nums` or a monospace font for numbers so digits line up.
- Color-code values where meaningful (green/amber/red for scores, up/down arrows for trends).
- Always include a non-happy-path state: loading spinner, empty state message, or error fallback.
- Table headers should be visually distinct: different background, font-weight, or border treatment.
- Use zebra striping or border-bottom for row separation.

### Color and theming
- Use `var(--config--main-color-brand, #fallback)` for brand integration.
- Use CSS custom properties for theming so admins can customize via configuration.
- Ensure sufficient contrast (WCAG AA: 4.5:1 for text, 3:1 for large text).
- Gradients and layered backgrounds make banners/heroes feel premium — avoid flat single-color backgrounds for promotional content.

## Critical Rules

### HTML Content (`content.html`)
- Must be an HTML **fragment** — no `<html>`, `<head>`, `<body>` tags
- All CSS must be in `<style>` tags or linked via relative paths
- **Relative file references work** — the platform deploys the entire `source.path` directory (e.g. `dist/`), so `<script src="./app.js">` and `<link href="./styles.css">` resolve correctly. Prefer a separate `app.js` module over inline `<script>` blocks.
- External CDN URLs must use HTTPS
- Template variables: `{{ property_name }}` replaced at runtime from configuration

### Shadow DOM
- DOM queries: use `sdk.$('.selector')` or `sdk.$$('.selector')` on the **in-widget SDK** (the `sdk` instance passed to your `init()` function) — NOT `document.querySelector()`. These methods are not available on `WidgetServiceSDK`.
- Branding: `var(--config--main-color-brand, #fallback)` for community colors
- CSS is automatically scoped — won't leak out, page styles won't affect widget

### Two SDKs — Widget SDK vs WidgetServiceSDK

Widgets use **two separate SDKs** loaded from different CDN URLs. Do not conflate them.

**1. In-widget SDK (`widget-sdk`)** — passed automatically to your `init()` function. Handles lifecycle, props, and DOM access inside the Shadow DOM.
- `sdk.whenReady()` — resolves when the widget is mounted
- `sdk.getProps()` — returns current configuration property values
- `sdk.$('.selector')` / `sdk.$$('.selector')` — Shadow DOM queries
- `sdk.on('propsChanged', cb)` — react to config changes
- `sdk.on('destroy', cb)` — cleanup hook

**2. WidgetServiceSDK (`widget-service-sdk`)** — instantiated manually via `new window.WidgetServiceSDK()`. Provides connector execution and HTTP helpers. It does **not** have `getProps`, `whenReady`, `$`, `on`, or any DOM/lifecycle methods.
- `serviceSDK.connectors.execute({ permalink, method, path?, payload?, queryParams?, headers? })` — call a configured connector. **Use `payload` (plain object) for POST/PUT/PATCH bodies — never `body` or `JSON.stringify()`.** The SDK serializes internally; using `body` silently sends an empty request.

**Required `content.html` structure:**
```html
<style>/* widget styles */</style>
<div id="root"></div>
<script src="https://static.customer-hub.northpass.com/widget-sdk/latest/index.umd.js"></script>
<script src="https://static.customer-hub.northpass.com/widget-service-sdk/latest/index.umd.js"></script>
<script type="module" src="./app.js"></script>
```

**Required `app.js` pattern:**
```js
export async function init(sdk) {
  await sdk.whenReady();
  var serviceSDK = new window.WidgetServiceSDK();
  var props = sdk.getProps();

  // Use sdk.$() for DOM, serviceSDK.connectors.execute() for data
  var container = sdk.$('#root');
  var data = await serviceSDK.connectors.execute({
    permalink: 'my-connector',
    method: 'GET'
  });

  // POST/PUT/PATCH: use `payload` (plain object), never `body` or JSON.stringify()
  await serviceSDK.connectors.execute({
    permalink: 'my-connector',
    method: 'POST',
    payload: { key: 'value' }
  });

  container.innerHTML = '...';

  sdk.on('propsChanged', function() {
    // re-render with updated props
  });

  sdk.on('destroy', function() {
    // cleanup
  });
}
```

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
    ├── content.html
    └── app.js
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
