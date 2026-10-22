---
title: Installation
layout: default
nav_order: 2
---

# Installation

`cammcat` is a standard Python package (`src/` layout) with the following
dependencies:

- [pyscicat](https://github.com/SciCatProject/pyscicat)
- [pydantic](https://docs.pydantic.dev/)
- [gemmi](https://gemmi.readthedocs.io/) (for CIF files)
- [h5py](https://www.h5py.org/) (for NeXus/HDF5 files).

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


Next: [Configuration](configuration.md) to set up your SciCat connection and
CAMM repository location.


<!-- END -->
