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
