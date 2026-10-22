---
title: cammcat add
parent: CLI Reference
layout: default
---

`$ cammcat add`

Copy a dataset (a folder or a single file) into the shared CAMM data
repository. This is a plain file-copy step and does **not** talk to SciCat —
use [`create`](create.md) afterward to register metadata.

## Usage

```bash
cammcat add (--sourceFolder PATH | --sourceFile PATH) [options]
```

`--sourceFolder` and `--sourceFile` are mutually exclusive; exactly one is
required.

- `--sourceFolder PATH` — copy the entire directory tree into the
  repository. Destination: `<camm_repo>/<key>/<folder-name>/` (the `<key>` is
  automatically generated\*).
- `--sourceFile PATH` — copy a single file into its own named directory.
  Destination: `<camm_repo>/<key>/<file-stem>/<file-name>` (the `<key>` is
  automatically generated\*).

\* Here `<key>` is a random 40-character hex string (git-style, e.g.
`ab/cdef123456789`) to prevent collisions in the case that more than one
directory/file is added with the same basename.


## Options

|  Option                   |  Description 
| ---                       | ---
|  `--camm-repository PATH` |  Destination root directory for the data. Required. 
|  `--checksums`, `-c`      |  Compute checksums (sha256) of the source files before copying. 
|  `--verify-checksums`     |  Verify checksums after copying (implies `--checksums`). 
|  `--chkAlg {sha256}`      |  Checksum algorithm (default: `sha256`). 
|  `--datasetName NAME`     |  Currently informational only; the destination directory name is derived from the source path. 
|  `--dry-run`, `-n`        |  Print what would be copied without copying anything. 


## Checksums

When `--checksums` or `--verify-checksums` is set, a `checksums.sha256`
file (in standard `sha256sum` format) is written alongside the copied
dataset directory, e.g.:

```
camm_repo/ab/cdef123456789/checksums.sha256
camm_repo/ab/cdef123456789/experiment/...
```

With `--verify-checksums`, each file is re-hashed after the copy and
compared against the original, printing `OK` / `FAILED` per file.


## Examples

Copy a whole directory, with checksums computed and verified:

```bash
cammcat add \
  --sourceFolder /data/experiment \
  --camm-repository /camm/repo \
  --verify-checksums
```

Copy a single file with checksums (but don't verify):

```bash
cammcat add \
    --sourceFile /data/sample.cif \
    --camm-repository /camm/repo \
    --checksums
```

Preview without copying:

```bash
cammcat --dry-run \
    add \
    --sourceFolder /data/experiment \
    --camm-repository /camm/repo \
```

<!-- END -->
