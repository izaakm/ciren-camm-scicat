---
title: Installation
layout: default
nav_order: 2
---

# Installation

`cammcat` is a standard Python package (`src/` layout) built on
[pyscicat](https://github.com/SciCatProject/pyscicat), [pydantic](https://docs.pydantic.dev/),
[gemmi](https://gemmi.readthedocs.io/) (for CIF files), and [h5py](https://www.h5py.org/)
(for NeXus/HDF5 files).

## From source

```bash
git clone <this-repo-url>
cd <this-repo>
pip install .
```

For development (editable install):

```bash
pip install -e .
```

## Verify the install

```bash
cammcat --help
```

If the `cammcat` console script isn't available, you can always invoke the
CLI module directly:

```bash
python -m cammcat.cli --help
```

Next: [Configuration](configuration.md) to set up your SciCat connection and
CAMM repository location.
