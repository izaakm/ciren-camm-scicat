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
- [h5py](https://www.h5py.org/) (for NeXus/HDF5 files)


<!-- [TODO] fix: h5py install fails -->
<!-- ## Standard install with pip -->
<!---->
<!-- ```bash -->
<!-- git clone https://github.com/izaakm/ciren-camm-scicat.git cammcat -->
<!-- cd cammcat -->
<!-- pip install . -->
<!-- ``` -->
<!---->
<!-- For development (editable install): -->
<!---->
<!-- ```bash -->
<!-- pip install -e . -->
<!-- ``` -->

## Conda install

```bash
git clone https://github.com/izaakm/ciren-camm-scicat.git cammcat
cd cammcat
conda env create -f environment.yml --prefix /path/to/conda/envs/camm-scicat
conda activate camm-scicat
pip install -e .
```

## A note about usage on ISAAC-NG

The `cammcat` package is already installed on ISAAC-NG:

```bash
module load miniconda
conda activate --prefix /lustre/isaac24/proj/UTK0487/conda/envs/camm-scicat
```

## Verify the install

```bash
cammcat --help
```

Next: [Configuration](configuration.md) to set up your SciCat connection and
CAMM repository location.


<!-- END -->
