---
title: cammcat help
parent: CLI Reference
layout: default
---

```
$ cammcat help
```

Show information about available settings.

## Usage

```bash
cammcat help [settings|format]
```

- `settings` - resolve and print the fully merged settings currently in
  effect (CLI flags + environment variables + config file).
- `format` - print the full list of recognized setting/metadata field
  names (e.g. for use in a config file or as `CAMM_<NAME>` environment
  variables). These can be used as values for the `list
  [--field|--format]` command.

## Examples

```bash
cammcat help format
cammcat --config-file camm_config.py help settings
```

<!-- END -->
