## Turn 1

**User:** Build a widget that shows our current app version, keep it really small and unobtrusive

**Agent:**

Got the docs. Here's what I'm thinking:

**Widget: `app-version`** — a tiny pill/badge that just shows something like "v2.4.1" in muted text. Think of it like the version labels you see tucked in a footer corner — small font, low contrast, doesn't compete for attention.

```
widgets/app-version/
├── widget.json
└── dist/
    └── content.html
```

The version string would come from a **text configuration property** — an admin sets it in the No-Code Builder (e.g., "2.4.1"). Simple, no API needed.

Two quick questions before I build:

1. **Version source** — Is a config property fine, or does the version need to come from an API/connector?
2. **Prefix style** — Do you want a "v" prefix (like `v2.4.1`) or a label (like `Version 2.4.1`), or just the raw number?


---

## Turn 2

**User:** Yeah a pill or badge sounds right. Just make it a configurable text property, go ahead and build it.

**Agent:**

Widget is built. Here's what was created:

```
workspace/
├── widget_registry.json
└── widgets/app-version/
    ├── widget.json
    └── dist/
        └── content.html
```

**What it does:**
- Renders a tiny pill badge showing **v1.0.0** (or whatever version the admin sets)
- 11px font, rounded-pill shape, muted colors — stays out of the way
- Starts at 75% opacity, full opacity on hover
- Uses community design tokens (`--config--main-color-*`) so it adapts to any theme
- Version text is selectable (`user-select: all`) for easy copy
- Single config property: **Version** (text, max 20 chars)
