# Gainsight Hub Extensions Plugin

A Claude Code plugin for building widgets, stylesheets, scripts, and connectors for the Gainsight Customer Hub (Insided) Extensions framework.

## Installation

In Claude Code, add the marketplace and install the plugin:

```
/plugin marketplace add gainsight-hub/gainsight-hub-extensions-plugin
/plugin install gainsight-hub-extensions@gainsight-hub-extensions-dev
```

## Skills

This plugin provides three skills:

- **build-extension** - Scaffold and build Gainsight Hub extensions from a conversational prompt
- **hub-reference** - Look up Gainsight Hub Extensions framework documentation and patterns
- **validate-extension** - Validate extension structure, HTML, connectors, and widget.json configuration

## Usage

Once installed, the skills are available in Claude Code. Invoke them with:

```
/build-extension
/hub-reference
/validate-extension
```

## License

MIT
