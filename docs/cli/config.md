---
title: cammcat config
parent: CLI Reference
layout: default
---

`$ cammcat config`

Inspect settings defined in a config file.

## Usage

```bash
cammcat --config-file PATH config list
```

`--config-file` is a global flag (see [Configuration](../configuration.md)); it
must be provided (or set via `CAMM_CONFIG_FILE`) for `config list` to have
anything to show.

## Subcommands

`$ cammcat config list`

Prints every non-empty setting from the config file, one per line, as
`key=value`.

## Example

```bash
cammcat --config-file camm_config.py config list
```

<!-- END -->
