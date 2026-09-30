# CAMM SciCat

Connect to the scicat frontend in your browser at:

<https://scicat-ciren.isaac.utk.edu>

Note that the base url for connecting the CLI is different:

`https://scicat-ciren.cn.isaac.utk.edu`

## Installation

```sh
conda env create -f environment.yml
conda activate camm-scicat
pip install .
```


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
