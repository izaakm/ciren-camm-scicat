---
title: cammcat login
parent: CLI Reference
layout: default
---

```
$ cammcat login
```

Authenticate against the SciCat client using the currently configured
credentials and confirm that login succeeds. Useful for validating a config
file or environment variables before running `create`.


## Usage

```bash
cammcat login
```

Uses `--scicat-base-url` / `CAMM_BASE_URL`, plus one of:

- `CAMM_TOKEN`
- `CAMM_USERNAME` + `CAMM_PASSWORD`

See [Configuration](../configuration.md) for details. On failure, an
authentication error is raised with details from the SciCat server.


<!-- END -->
