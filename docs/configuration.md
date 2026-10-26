---
title: Configuration
layout: default
nav_order: 3
---

# Configuration

Options can be passed to the `cammcat` CLI three ways, in order of priority:

1. CLI flags (take priority over other settings)
2. Environment variables
3. Config file (lowest priority)

## Authentication

> **IMPORTANT** You must provide your username and password via environment variables.

Provide **either** a token or a username/password pair:

- `CAMM_TOKEN` (you can get this from the web frontend)
- `CAMM_USERNAME` + `CAMM_PASSWORD` (this is your UT NetID and password)

Export the env variables, and then test your connection:

```bash
cammcat login
```

## CLI Flags

```
cammcat \
    --config-file CONFIG_FILE \
    --scicat-base-url BASE_URL \
    [...]
```

**Global options** can be used with any subcommand and precede the subcommand
on the command line (`cammcat [global options] subcommand [options]`):

|  Flag                                                |  Description 
| ---                                                  | ---
|  `--log-level {debug,info,warning,error,critical}`   |  Logging verbosity (default: `warning`). 
|  `--config-file PATH`                                |  Path to a config file (default: `$CAMM_CONFIG_FILE`). 
|  `--scicat-base-url URL`                             |  SciCat base URL (default: `$CAMM_BASE_URL`). 
|  `--dry-run`, `-n`                                   |  Don't make changes; print what would happen. (Supported by `add` and `create`.) 


## Environment variables

|  Variable             |  CLI                 | Description
| ---                   | ---                  | ---
|  `CAMM_CONFIG_FILE`   |  `--config-file`     | Path to config file.
|  `CAMM_BASE_URL`      |  `--scicat-base-url` | Base URL of the SciCat REST API
|  `CAMM_TOKEN`         |  -                   | SciCat API token 
|  `CAMM_USERNAME`      |  -                   | UTK NetID
|  `CAMM_PASSWORD`      |  -                   | UTK Password
|  `CAMM_REPO`          |  `--camm-repository` | Directory for storing datasets
|  `CAMM_<SETTING>`     |  -                   | Any dataset metadata attribute, e.g. `CAMM_OWNERGROUP`, `CAMM_CONTACTEMAIL` \*

\* Any dataset metadata attribute (the fields used when creating a dataset,
e.g. `contactEmail`, `ownerGroup`, `datasetName`, `keywords`, ...) can be set
via an environment variable of the form `CAMM_<FIELDNAME>` (all uppercase).


## Config file

The path can be set with `CAMM_CONFIG_FILE` or `--config-file` (overrides the
env variable). The file is a plain Python file; any variable you define becomes
a setting. For example:

```python
# camm_config.py
base_url = "https://scicat.example.org/api/v3"
camm_repo = "/camm/repo"
contactEmail = "me@utk.edu"
ownerGroup = "CAMM"
principalInvestigator = "PI's Name"
```

Inspect what a config file resolves to:

```bash
cammcat --config-file camm_config.py config list
```


## Inspecting resolved settings

```bash
cammcat help settings     # show the fully merged settings currently in effect
cammcat help format       # list every recognized setting/field name
```


<!-- END -->
