# Validation Eval Fixtures

Intentionally broken widgets used by the validate-extension behavior evals.

| Fixture | Issues |
|---------|--------|
| `broken_widget` | Missing `description`, `category`, and `source`/`content` in widget.json |
| `insecure_widget` | Hardcoded API key in connectors.json, `document.querySelector` instead of `sdk.$()` |
| `invalid_html` | Full HTML document (`<html>`, `<head>`, `<body>`) instead of HTML fragment |

These fixtures are copied into the eval workspace before running behavior evals.
