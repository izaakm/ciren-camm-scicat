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
- [Configuration](configuration.md) - config file, environment variables, CLI flags
- [CLI command reference](cli/index.md)

## Primary commands

- [`cammcat add`](./cli/add.md) — copy a dataset into the CAMM repository
- [`cammcat create`](./cli/create.md) — register dataset metadata in SciCat
- [`cammcat list`](./cli/list.md) — list datasets in SciCat
- [`cammcat show`](./cli/show.md) — print full metadata for datasets


## Quick Start

Once installed, a typical workflow looks like this:

```bash
# 1. Copy data files into the CAMM repository (does not require credentials)
cammcat add \
    --sourceFolder /data/experiment \
    --camm-repository /camm/repo \
    --verify-checksums
# Copies/data/experiment -> /camm/repo/experiment
# Returns path to new directory

# 2. Register the dataset's metadata in SciCat
# 2a. Export your credentials. Put these in a .env file and source it instead
#     of typing this into the prompt so that it's not tracked in your bash history
export CAMM_BASE_URL="https://scicat-ciren.cn.isaac.utk.edu/api/v3"
export CAMM_USERNAME="<Your UTK NetID>"
export CAMM_PASSWORD="<Your UTK Password>"
# 2b. Create the dataset record in SciCat's database
cammcat create \
  --sourceFolder /camm/repo/<key>/experiment \
  --datasetName "Name of experiment" \
  --contactEmail netid@utk.edu \
  --creationLocation "University of Tennessee, Knoxville" \
  --owner "Your Name" \
  --principalInvestigator "PI's Name" \
  --ownerGroup CAMM
# Returns PID of the new dataset

# 3. Confirm
cammcat list
cammcat show <pid>
```

See [Configuration](configuration.md) for how to avoid typing the
`--camm-repository`, credentials, and base URL every time.


<!-- END -->
