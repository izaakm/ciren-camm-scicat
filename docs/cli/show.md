---
title: show
parent: CLI Reference
layout: default
---

# `cammcat show`

Print the full metadata record (and its original data block) for one or
more datasets, as JSON.

## Usage

```bash
cammcat show [dataset_id ...] [--data-blocks]
```

- `dataset_id` — zero or more dataset PIDs to display.
- `--data-blocks` — also print the associated file list (data blocks) for
  each dataset.

## Output

For each PID given, prints two pretty-printed JSON documents: the dataset
record, followed by its original data blocks.

## Example

```bash
cammcat show 20.500.12345/abc-123
```
