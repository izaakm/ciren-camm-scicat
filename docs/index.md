---
title: Home
layout: default
nav_order: 1
---

# cammcat Documentation

`cammcat` is a Python package for managing CAMM datasets: copying raw data
into a shared CAMM data repository, building and registering dataset
metadata in a [SciCat](https://scicatproject.github.io/) instance, and
querying datasets that already exist there.

This site documents the **command-line interface (CLI)**, which is the
primary way most users will interact with the package.

## Quick links

- [Installation](installation.md)
- [Configuration](configuration.md) — config file, environment variables, CLI flags
- [CLI command reference](cli/index.md)

## What can the CLI do?

| Command | Purpose |
|---|---|
| [`cammcat add`](cli/add.md) | Copy a dataset (file or folder) into the CAMM data repository, optionally computing/verifying checksums. |
| [`cammcat create`](cli/create.md) | Build dataset metadata and register a new dataset (and its data block) in SciCat. |
| [`cammcat list`](cli/list.md) | List datasets already registered in SciCat. |
| [`cammcat list-files`](cli/list-files.md) | List the files attached to one or more datasets. |
| [`cammcat show`](cli/show.md) | Print the full metadata record for one or more datasets. |
| [`cammcat login`](cli/login.md) | Authenticate against SciCat and verify credentials work. |
| [`cammcat model`](cli/model.md) | Inspect the dataset's underlying data model (e.g. dump its JSON schema). |
| [`cammcat config`](cli/config.md) | Inspect configuration loaded from a config file. |
| [`cammcat help`](cli/help.md) | Show available settings and their current resolved values. |

> **Note:** `attach` and `update` are present in the CLI but not yet
> implemented — they will raise `NotImplementedError` if invoked. They'll be
> documented here once implemented.

## Basic workflow

A typical workflow looks like this:

```bash
# 1. Copy data into the shared CAMM repository
cammcat add --sourceFolder /data/experiment1 --camm-repository /camm/repo --checksums

# 2. Register the dataset's metadata in SciCat
cammcat create \
  --sourceFolder /camm/repo/<key>/experiment1 \
  --datasetName experiment1 \
  --contactEmail me@utk.edu \
  --creationLocation "University of Tennessee, Knoxville" \
  --owner "Jane Scientist" \
  --principalInvestigator "Adrian del Maestro" \
  --ownerGroup CAMM

# 3. Confirm it is there
cammcat list
cammcat show <pid>
```

See [Configuration](configuration.md) for how to avoid typing the
`--camm-repository`, credentials, and base URL every time.
