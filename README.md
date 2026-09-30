# CAMM SciCat

Connect to the scicat frontend in your browser at:

<https://scicat-ciren.isaac.utk.edu>

> [!IMPORTANT]
> The web GUI is **only** accessible from the UTK VPN to members of the
> `ciren-scicat` AD group.
> 
> - [Click here][vpn] to learn how to set up and log in to the VPN.
> - Let your CIREN facilitator know (by email) if you need to be added to the
>   `ciren-scicat` AD group.

[vpn]: https://utk.teamdynamix.com/TDClient/2277/OIT-Portal/KB/Article/130338/Virtual-Private-Network-VPN-User-Guide

> [!WARNING]
> We are currenlty using a self-signed cert for TLS/HTTPS; you will see a
> warning from your browser when navigating to the URL.

> [!NOTE]
> Note that the base url for connecting the CLI is different:
>
> ```
> https://scicat-ciren.cn.isaac.utk.edu/api/v3
>                      ^^              ^^^^^^^
> ```


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
> conda activate /lustre/isaac24/proj/UTK0487/conda/envs/camm-scicat
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
> The **cammcat** and **pyscicat** packages use python **requests** to
> communicate with the SciCat REST API. Since we are still using a self-signed
> cert, you will have to provide this to **requests** or it will not connect.
> We have included a copy of the public cert, which you must provide via the
> `CURL_CA_BUNDLE` env variable in order for **requests** to connect:
>
> ```sh
> export CURL_CA_BUNDLE="${PWD}/certs/scicat.crt"
> ```

> [!IMPORTANT]
> Your **username** and **password** **must** be specific in either the
> config.py file or as env variables. If you provide both, the env variables
> take precedence over the config file.

Optional config file:

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
# ========================================================================

# ========================================================================
# Client settings
# ========================================================================
# base_url = 'https://scicat-ciren.cn.isaac.utk.edu/api/v3'
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
# type_ = 'raw'                                           # aka 'type'
# updatedAt = None
# updatedBy = None
# validationStatus = None
EOF
```

Optional environment variables:

```sh
tee -a .env << EOF
# Environment variables override config.py
export CAMM_BASE_URL="https://scicat-ciren.cn.isaac.utk.edu/api/v3"
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


**List all datasets:**

```sh
cammcat list
```

Output:

```
pid	                                                    datasetName
PID.SAMPLE.PREFIX/4db51a19-2a6d-493a-a84e-22990848ecf8	example/dataset
```

**Show a specific dataset**

```sh
cammcat show <PID>
```

Output:

```json
{
  "ownerGroup": "CAMM",
  "accessGroups": [
    "CAMM"
  ],
...
}
```

**Create a new dataset**

```sh
cammcat add --sourceFolder </path/to/dataset-directory>
```

Output (PID of dataset):

```
PID.SAMPLE.PREFIX/6a8afda8-4a15-4935-885a-5a426757a141
```


<!-- END -->
