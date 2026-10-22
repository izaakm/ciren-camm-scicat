---
title: model
parent: CLI Reference
layout: default
---

# `cammcat model`

Inspect the underlying `CAMMDataset` data model (a `pydantic` model built
on top of SciCat's `RawDataset`).

## Usage

```bash
cammcat model --dump-schema
```

## Options

| Option | Description |
|---|---|
| `--dump-schema` | Print the JSON Schema for `CAMMDataset` to stdout. |

This is primarily useful for integrating with other tools (e.g. generating
forms or validating metadata files) or for understanding exactly which
fields and types are expected.
