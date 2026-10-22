---
title: Configuration
layout: default
nav_order: 3
---

# Configuration

Settings can come from three places, merged with this priority (highest
wins):

```
CLI flags  >  environment variables  >  config file
```

## Config file

Pass a path with `--config-file`, or set the `CAMM_CONFIG_FILE` environment
variable. The file is a plain Python file; any variable you define becomes
a setting. For example:

```python
# camm_config.py
base_url = "https://scicat.example.org/api/v3"
username = "myuser"
camm_repo = "/camm/repo"
contactEmail = "me@utk.edu"
ownerGroup = "CAMM"
```

Inspect what a config file resolves to:

```bash
cammcat --config-file camm_config.py config list
```

## Environment variables

| Variable | Maps to |
|---|---|
| `CAMM_CONFIG_FILE` | `--config-file` |
| `CAMM_BASE_URL` | SciCat `base_url` |
| `CAMM_TOKEN` | SciCat API token |
| `CAMM_USERNAME` | SciCat username |
| `CAMM_PASSWORD` | SciCat password |
| `CAMM_REPO` | `--camm-repository` |
| `CAMM_<SETTING>` | Any dataset metadata field, e.g. `CAMM_OWNERGROUP`, `CAMM_CONTACTEMAIL` (see full list below) |

Any dataset metadata attribute (the fields used when creating a dataset,
e.g. `contactEmail`, `ownerGroup`, `datasetName`, `keywords`, ...) can be set
via an environment variable of the form `CAMM_<FIELDNAME>` (case-insensitive
on the field name portion, but conventionally upper case).

## Authentication

Provide **either** a token or a username/password pair:

- `CAMM_TOKEN` / nothing else — uses the token directly.
- `CAMM_USERNAME` + `CAMM_PASSWORD` — the client logs in automatically
  (via LDAP by default) and exchanges credentials for a token.

Test your credentials and connection with:

```bash
cammcat login
```

## Inspecting resolved settings

```bash
cammcat help settings     # show the fully merged settings currently in effect
cammcat help format       # list every recognized setting/field name
```

## Global flags

These apply no matter which subcommand you run:

| Flag | Description |
|---|---|
| `--log-level {debug,info,warning,error,critical}` | Logging verbosity (default: `warning`). |
| `--config-file PATH` | Path to a config file (default: `$CAMM_CONFIG_FILE`). |
| `--scicat-base-url URL` | SciCat base URL (default: `$CAMM_BASE_URL`). |
| `--dry-run`, `-n` | Don't make changes; print what would happen. (Supported by `add` and `create`.) |
