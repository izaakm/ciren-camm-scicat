---
title: create
parent: CLI Reference
layout: default
---

# `cammcat create`

Build a dataset metadata record and register it (plus its data block) in
SciCat. `--sourceFolder` should normally point at data that has already
been copied into the CAMM repository with [`add`](add.md).

## Usage

```bash
cammcat create --sourceFolder PATH --datasetName NAME [metadata options] [options]
```

## Required metadata

These can be supplied as CLI flags, environment variables (`CAMM_<FIELD>`),
or config-file entries — see [Configuration](../configuration.md).

| Flag | Description |
|---|---|
| `--sourceFolder PATH` | Directory containing the dataset's files. |
| `--datasetName NAME` | Human-readable dataset name. Pass `.` to use the basename of `--sourceFolder`. |
| `--contactEmail EMAIL` | Contact email for the dataset. |
| `--creationLocation TEXT` | Where the data was created. |
| `--owner NAME` | Dataset owner. |
| `--principalInvestigator NAME` | PI for the dataset. |
| `--ownerGroup GROUP` | Owning group (also added to `--accessGroups` automatically). |

## Common optional metadata

A large set of SciCat dataset fields is also exposed, including:
`--description`, `--keywords`, `--license`, `--classification`,
`--creationTime`, `--endTime`, `--instrumentId`, `--instrumentGroup`,
`--proposalId`, `--sampleId`, `--scientificMetadata`, `--sharedWith`,
`--techniques`, `--type`, `--version`, and more.

Run `cammcat create --help` for the complete, current list.

## Other options

| Option | Description |
|---|---|
| `--chkAlg {sha256}` | Compute checksums for files in the data block using this algorithm. |
| `--camm-repository PATH` (env `CAMM_REPO`) | Used to compute `sourceFolder` as a path relative to the repository root. |
| `--get-metadata-from-file PATH` | Extract scientific metadata automatically from a file and merge it into the dataset. Supports `.cif` and `.nxs` files (see [Supported file types](#supported-metadata-file-types)). |
| `--dry-run`, `-n` | Print the dataset and data-block JSON instead of submitting them to SciCat. |

## What it does

1. Loads/merges settings (CLI > env > config file).
2. Builds a `CAMMDataset` record from the required/optional metadata fields.
3. Builds a data block by walking `--sourceFolder` and recording every file
   (size, modified time, uid/gid, optional checksum).
4. If `--get-metadata-from-file` is given, extracts additional
   `scientificMetadata` from that file and merges it in.
5. On `--dry-run`, prints the dataset and data block as JSON and exits.
   Otherwise, logs in to SciCat, creates the dataset, verifies it was
   created, then creates the original data block, and prints the new
   dataset's PID.

## Supported metadata file types

`--get-metadata-from-file` currently supports:

- **`.cif`** — crystallographic information files (via `gemmi`). Extracts
  fields such as chemical formula, space group, cell parameters, authors,
  DOI, temperature/pressure, etc.
- **`.nxs`** — NeXus/HDF5 files (via `h5py`). Extracts instrument name,
  sample name, date, temperature, and pressure.

## Examples

Dry run to inspect the generated metadata before submitting:

```bash
cammcat create \
  --sourceFolder /camm/repo/ab/cdef.../experiment1 \
  --camm-repository /camm/repo \
  --datasetName experiment1 \
  --contactEmail me@utk.edu \
  --creationLocation "UTK" \
  --owner "Jane Scientist" \
  --principalInvestigator "Adrian del Maestro" \
  --ownerGroup CAMM \
  --dry-run
```

Create it for real, pulling extra metadata from a CIF file:

```bash
cammcat create \
  --sourceFolder /camm/repo/ab/cdef.../experiment1 \
  --camm-repository /camm/repo \
  --datasetName . \
  --get-metadata-from-file /camm/repo/ab/cdef.../experiment1/structure.cif \
  --contactEmail me@utk.edu \
  --creationLocation "UTK" \
  --owner "Jane Scientist" \
  --principalInvestigator "Adrian del Maestro" \
  --ownerGroup CAMM
```
