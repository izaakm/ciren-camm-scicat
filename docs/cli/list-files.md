---
title: list-files
parent: CLI Reference
layout: default
---

# `cammcat list-files`

List the files recorded in the original data block(s) for one or more
datasets.

## Usage

```bash
cammcat list-files [dataset_id ...]
```

- `dataset_id` — zero or more dataset PIDs. If none are given, no PIDs will
  be queried (pass the PIDs you want explicitly).

## Output

Prints a fixed-width table with columns:

```
PID   UID   GID   Size   mTime   Filepath
```

## Example

```bash
cammcat list-files 20.500.12345/abc-123 20.500.12345/def-456
```
