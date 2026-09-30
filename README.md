# CAMM SciCat

Connect to the scicat frontend in your browser at:

<https://scicat-ciren.isaac.utk.edu>

> [!IMPORTANT]
> The web GUI is **only** accessible from the UTK VPN to members of the
> `ciren-scicat` AD group.
> 
> - [Click here] to learn how to set up and log in to the VPN.
> - Let your CIREN facilitator know (by email) if you need to be added to the
>   `ciren-scicat` AD group.

[vpn]: https://utk.teamdynamix.com/TDClient/2277/OIT-Portal/KB/Article/130338/Virtual-Private-Network-VPN-User-Guide

> [!WARNING]
> We are currenlty using a self-signed cert for TLS/HTTPS; you will see a
> warning from your browser when navigating to the URL.

Note that the base url for connecting the CLI is different:

`https://scicat-ciren.cn.isaac.utk.edu`

## Installation

```sh
conda env create -f environment.yml
conda activate camm-scicat
pip install .
```

> [!TIP]
> The `cammcat` CLI is installed in a conda environment on the ISAAC-NG
> cluster:
>
> ```sh
> module load miniconda
> conda activate --prefix /lustre/isaac24/proj/UTK0487/conda/envs/camm-scicat
> ```

## Usage

    usage: cammcat [-h] [--log-level LOG_LEVEL] [--config-file CONFIG_FILE]
                   [--scicat-base-url BASE_URL] [--dry-run]
                   {help,add,config,show,list,list-files,update} ...

    positional arguments:
      {help,add,config,show,list,list-files,update}

    options:
      -h, --help            show this help message and exit
      --log-level LOG_LEVEL
      --config-file CONFIG_FILE
      --scicat-base-url BASE_URL
      --dry-run, -n


## Setup

> [!IMPORTANT]
> The `cammcat` and `pyscicat` packages use python requests to communicate with
> the SciCat REST API. We have included a copy of the public cert, which you
> must provide via the `CURL_CA_BUNDLE` env variable in order for python
> requests to connect:
>
> ```sh
> export CURL_CA_BUNDLE="${PWD}/certs/scicat.crt"
> ```

```sh
tee /path/to/config.py << EOF
# ========================================================================
# Specify the path to this file:
#
#   cammcat --config-file /path/to/config.py
#
# Or set the env variable:
#
#   export CAMM_CONFIG_FILE="/path/to/config.py"
#
# ========================================================================
# Client settings
# ========================================================================
# base_url = 'https://scicat-ciren.cn.isaac.utk.edu'
# username = '<NetID>'
# password = '<Password>'

# ========================================================================
# Dataset settings
# ========================================================================
# owner vs contact ??? ~> PI? ~> createdBy?
contactEmail = '<NetID>@utk.edu'                          # Required
creationLocation = 'University of Tennessee, Knoxville'   # Required
creationTime = None                                       # Required
owner = '<Your Name>'                                     # Required
principalInvestigator = '<Name of PI>'                    # Required
ownerGroup = 'CAMM'                                       # Required
# sourceFolder = None                                     # Required, use cammcat add --sourceFolder /path/to/dataset
# accessGroups = []
# classification = None
# createdAt = None
# createdBy = None
# dataFormat = None
# datasetName = None
# description = None
# endTime = None
# history = []
# instrumentGroup = None
# instrumentId = None
# isPublished = False
# keywords = []
# license = None
# numberOfFiles = None
# numberOfFilesArchived = -1
# orcidOfOwner = '0000-0000-0000-0000'
# ownerEmail = '<NetID>@utk.edu'
# packedSize = -1
# pid = None
# proposalId = None
# sampleId = None
# scientificMetadata = {}
# sharedWith = []
# size = None
# sourceFolderHost = None
# techniques = []
# type = 'raw'     # <= Don't use this one
# type_ = 'raw'    # Munge the key
# updatedAt = None
# updatedBy = None
# validationStatus = None
EOF
```

```sh
tee -a.env << EOF
# Environment variables override config.py
export CAMM_BASE_URL="https://scicat-ciren.cn.isaac.utk.edu"
export CAMM_USERNAME="<NetID>"
export CAMM_PASSWORD="<Password>"
# export CAMM_TOKEN="<token from web GUI>"
# export CAMM_CONFIG_FILE="/path/to/config.py"
EOF
```

Then

```sh
source .env
```


## Examples


List all datasets

```sh
cammcat list
```

Show a specific dataset

```sh
cammcat show <PID>
```

Create a new dataset

```sh
cammcat add --sourceFolder </path/to/dataset-directory>
```



<!-- END -->
