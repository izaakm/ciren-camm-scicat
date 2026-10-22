---
title: CLI Reference
layout: default
nav_order: 4
has_children: true
---

# CLI Command Reference

`cammcat` is organized as a single entry point with subcommands:

```bash
cammcat [global options] <command> [command options]
```

Run `cammcat <command> --help` at any time to see the full, authoritative
list of options for that command.

## Commands

- [`add`](add.md) — copy a dataset into the CAMM repository
- [`create`](create.md) — register dataset metadata in SciCat
- [`list`](list.md) — list datasets in SciCat
- [`list-files`](list-files.md) — list files attached to datasets
- [`show`](show.md) — print full metadata for datasets
- [`login`](login.md) — test authentication
- [`model`](model.md) — inspect the dataset data model
- [`config`](config.md) — inspect a config file
- [`help`](help.md) — list settings and their resolved values

## Not yet implemented

- `attach` — intended to attach data files to an existing dataset.
- `update` — intended to update an existing dataset's metadata.

Both currently raise `NotImplementedError` if run.
