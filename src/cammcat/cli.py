#!/usr/bin/env python
# coding: utf-8

'''
Docker container:

    username: admin
    password: 2jf70TPNZsS


Init signature:
RawDataset(
    *,
    # [sorted]
    accessGroups          : List[str] | None            = None,
    classification        : str | None                  = None,
    contactEmail          : str,                                # Required
    createdAt             : str | None                  = None,
    createdBy             : str | None                  = None,
    creationLocation      : str,                                # Required
    creationTime          : str,                                # Required
    dataFormat            : str | None                  = None,
    datasetName           : str | None                  = None,
    description           : str | None                  = None,
    endTime               : str | None                  = None,
    history               : List[dict] | None           = None,
    instrumentGroup       : str | None                  = None,
    instrumentId          : str | None                  = None,
    isPublished           : bool | None                 = False,
    keywords              : List[str] | None            = None,
    license               : str | None                  = None,
    numberOfFiles         : int | None                  = None,
    numberOfFilesArchived : int | None                  = None,
    orcidOfOwner          : str | None                  = None,
    owner                 : str,                                # Required
    ownerEmail            : str | None                  = None,
    ownerGroup            : str,                                # Required
    packedSize            : int | None                  = None,
    pid                   : str | None                  = None,
    principalInvestigator : str,                                # Required
    proposalId            : str | None                  = None,
    sampleId              : str | None                  = None,
    scientificMetadata    : Dict | None                 = None,
    sharedWith            : List[str] | None            = None,
    size                  : int | None                  = None,
    sourceFolder          : str,                                # Required
    sourceFolderHost      : str | None                  = None,
    techniques            : List[dict] | None           = None,
    type                  : pyscicat.model.DatasetType  = <DatasetType.raw:'raw'>,
    updatedAt             : str | None                  = None,
    updatedBy             : str | None                  = None,
    validationStatus      : str | None                  = None,
    version               : str | None                  = None,
) -> None
'''


import json
import argparse
import os
import pathlib
import tomllib  # Can't write ... deal with writing configs via CLI later
import sys
import runpy
import importlib.util

from pathlib import Path
from collections import UserDict
from datetime import datetime
from typing import Any, Dict, List, Literal

from pyscicat import model
from pyscicat.client import ScicatClient
from pyscicat.model import DataFile, CreateDatasetOrigDatablockDto
from pyscicat.model import DatasetType
from pyscicat.model import Ownable, RawDataset

from pydantic import BaseModel, ConfigDict


# Some names of environment variables.
_env_camm_config_file = 'CAMM_CONFIG_FILE'
_env_camm_username = 'CAMM_USERNAME'
_env_camm_password = 'CAMM_PASSWORD'
_env_camm_base_url = 'CAMM_BASE_URL'


# owner vs contact ??? ~> PI? ~> createdBy?
example_config: dict[str, Any] = {
    'contactEmail': 'izaak@utk.edu',  # Required
    'creationLocation': 'University of Tennessee, Knoxville',  # Required
    'creationTime': None,  # Required
    'owner': 'Izaak Miller',  # Required
    'sourceFolder': None,  # Required
    'principalInvestigator': 'Adrian del Maestro',  # Required
    'ownerGroup': 'CAMM',  # Required
    'accessGroups': [],
    'classification': None,
    'createdAt': None,
    'createdBy': None,
    'dataFormat': None,
    'datasetName': None,
    'description': None,
    'endTime': None,
    'history': [],
    'instrumentGroup': None,
    'instrumentId': None,
    'isPublished': False,
    'keywords': [],
    'license': None,
    'numberOfFiles': None,
    'numberOfFilesArchived': -1,
    'orcidOfOwner': '0000-0000-0000-0000',
    'ownerEmail': 'izaak@utk.edu',
    'packedSize': -1,
    'pid': None,  # ????
    'proposalId': None,
    'sampleId': None,
    'scientificMetadata': {},
    'sharedWith': [],
    'size': None,
    'sourceFolderHost': None,
    'techniques': [],
    'type': 'raw',
    'updatedAt': None,
    'updatedBy': None,
    'validationStatus': None,
    'version': None,
}

# Use the keys from the example config, e.g.:
# { 'CAMM_OWNEREMAIL': 'ownerEmail', ... }
env2config = {f'CAMM_{k.upper()}': k for k in sorted(example_config.keys()) } 


# ========================================================================
# Client
# ========================================================================
# I'm not sure if the "client" should be a subclass of ScicatClient or just a fxn.
class CAMMClient:
    pass


def get_client(username=None, password=None, base_url=''):
    return ScicatClient(base_url=base_url, username=username, password=password)


# ========================================================================
# Config
# ========================================================================
# def load_config(path: str):
#     '''
#     Load the config file as a `config` module.
#
#     A simpler alternative to this is `runpy.run_path(path)`, but the object it produces is messy.
#     '''
#     if not path:
#         sys.tracebacklimit = 0
#         raise ValueError(f'You must provide a path for the config file or set "{_env_camm_config_file}".')
#     path = Path(path).expanduser().resolve()
#     spec = importlib.util.spec_from_file_location("configfile", path)
#     module = importlib.util.module_from_spec(spec)
#
#     # Register in sys.modules so it behaves like a normal `import <module>`
#     sys.modules['configfile'] = module
#
#     spec.loader.exec_module(module)
#     return module

class Settings(BaseModel):
    # Client settings
    base_url: str|None = None
    username: str|None = None
    password: str|None = None

    # Dataset settings
    # owner vs contact ??? ~> PI? ~> createdBy?
    contactEmail: str|None = None
    creationLocation: str|None = None
    creationTime: str|None = None
    owner: str|None = None
    sourceFolder: str|None = None
    principalInvestigator: str|None = None
    ownerGroup: str|None = None
    accessGroups: List[str]|None = None
    classification: str|None = None
    createdAt: str|None = None
    createdBy: str|None = None
    dataFormat: str|None = None
    datasetName: str|None = None
    description: str|None = None
    endTime: str|None = None
    history: List[str]|None = None
    instrumentGroup: str|None = None
    instrumentId: str|None = None
    isPublished: bool|None = None
    keywords: List[str]|None = None
    license: str|None = None
    numberOfFiles: str|None = None
    numberOfFilesArchived: int|None = None
    orcidOfOwner: str|None = None
    ownerEmail: str|None = None
    packedSize: int|None = None
    pid: str|None = None
    proposalId: str|None = None
    sampleId: str|None = None
    scientificMetadata: dict[str,Any]|None = None
    sharedWith: List[str]|None = None
    size: str|None = None
    sourceFolderHost: str|None = None
    techniques: List[str]|None = None
    type: str|None = None
    updatedAt: str|None = None
    updatedBy: str|None = None
    validationStatus: str|None = None
    version: str|None = None

    # model_config = ConfigDict(extra='allow')  # This is the default.
    model_config = ConfigDict(extra='ignore')

    def list(self):
        lines = []
        for key, val in self.model_dump(exclude_none=True).items():
            lines.append(f'{key}={val}')
        return '\n'.join(lines)


def load_config(filepath: str):
    data = runpy.run_path(filepath)
    return Settings(**data)


# def find_global_config_file(path=None):
#     if path:
#         return path
#     elif 'CAMM_GLOBAL_CONFIG' in os.environ:
#         return os.environ['CAMM_GLOBAL_CONFIG']
#     else:
#         # [TODO] Find the file.
#         pass


# def find_local_config_file(path=None):
#     if path:
#         return path
#     elif 'CAMM_LOCAL_CONFIG' in os.environ:
#         return os.environ['CAMM_LOCAL_CONFIG']
#     else:
#         # [TODO] Find the file.
#         pass


def settings_from_configfile(config_file):
    '''
    Simple wrapper to produce a dict from a *module* (the config file).
    '''
    return vars(load_config(config_file))


# See `env_keys` above
def settings_from_env(environ=None, keys=env2config):
    environ = environ or os.environ
    data = {}
    for env_key, config_key in env2config.items():
        if env_key in environ:
            data[config_key] = environ[env_key]
    return data


def settings_from_namespace(namespace):
    # [TODO] Explicitely get values by name instead of getting everything from args.
    return vars(namespace)


def merge_settings(*settings, dropna=True):
    data = {}
    for d in settings:
        if dropna:
            data.update({k:v for k,v in d.items() if v})
        else:
            data.update(d)
    return Settings(**data)


def load_settings(config_file, env_config, cli_config, dropna=True):
    # Check the configs.
    # Priority (high to low): CLI > ENV > config file
    configs = []
    if os.path.exists(config_file):
        # Lowest priority in first, will be overwritten by configs below.
        d = settings_from_configfile(config_file)
        configs.append(d)
    if env_config:
        d = settings_from_env(env_config)
        configs.append(d)
    if cli_config:
        # Highest priority is last, will overwrite configs above.
        d = settings_from_namespace(cli_config)
        configs.append(d)

    settings = merge_settings(*configs, dropna=dropna)
    return settings


# ========================================================================
# Dataset
# ========================================================================
# createdBy: str | None = None,
# updatedBy: str | None = None,
# updatedAt: str | None = None,
# createdAt: str | None = None,
# ownerGroup: str,
# accessGroups: List[str] | None = None,
# instrumentGroup: str | None = None,
# pid: str | None = None,
# classification: str | None = None,
# contactEmail: str,

# creationTime: str,
def get_creationTime():
    return datetime.now().isoformat()

# datasetName: str | None = None,
# description: str | None = None,
# history: List[dict] | None = None,
# instrumentId: str | None = None,
# isPublished: bool | None = False,
# keywords: List[str] | None = None,
# license: str | None = None,

# numberOfFiles: int | None = None,
def get_numberOfFiles(sourceFolder):
    n_files = 0
    for root, dirs, files in os.walk(sourceFolder):
        n_files += len(files)
    return n_files

# numberOfFilesArchived: int | None = None,
# orcidOfOwner: str | None = None,
# owner: str,
# ownerEmail: str | None = None,
# packedSize: int | None = None,
# sharedWith: List[str] | None = None,

# size: int | None = None,
import os
from os.path import join, getsize
def get_size(sourceFolder):
    '''
    Based on example from `os.walk` example in Python docs.
    
    Returns
    -------
    size
        In bytes.
    '''
    size = 0
    for root, dirs, files in os.walk(sourceFolder):
        size += sum(getsize(join(root, name)) for name in files)
    return size


def new_dataset(
    # Required for RawDataset
    contactEmail: str | None = None,
    creationLocation: str | None = None,
    creationTime: str | None = None,
    owner: str | None = None,
    sourceFolder: str | None = None,
    principalInvestigator: str | None = None,
    ownerGroup: str | None = None,

    # Optional
    accessGroups: List[str] | None = None,
    classification: str | None = None,
    createdAt: str | None = None,
    createdBy: str | None = None,
    dataFormat: str | None = None,
    datasetName: str | None = None,
    description: str | None = None,
    endTime: str | None = None,
    history: List[dict] | None = None,
    instrumentGroup: str | None = None,
    instrumentId: str | None = None,
    isPublished: bool | None = False,
    keywords: List[str] | None = None,
    license: str | None = None,
    numberOfFiles: int | None = None,
    numberOfFilesArchived: int | None = None,
    orcidOfOwner: str | None = None,
    ownerEmail: str | None = None,
    packedSize: int | None = None,
    pid: str | None = None,
    proposalId: str | None = None,
    sampleId: str | None = None,
    scientificMetadata: Dict | None = None,
    sharedWith: List[str] | None = None,
    size: int | None = None,
    sourceFolderHost: str | None = None,
    techniques: List[dict] | None = None,
    type_: str | DatasetType = 'raw',
    updatedAt: str | None = None,
    updatedBy: str | None = None,
    validationStatus: str | None = None,
    version: str | None = None,
    **kwargs                                    # Catch all
):
    '''
    Questions:
    - "owner" vs "creator" vs "PI" ???
    - "pid" ? Seems to be assigned automatically on call to `client.datasets_create`s
    - "{created,updated}At" ... location? time?
    - "version" for datasets? date? version process/pipeline that created it?
    - "...Archived" ?
    - "packedSize"?

    Issue:
        ScicatCommError: Error in operation datasets_create: 
            {'status': 400, 'message': 
                '[
                    {"property":"createdBy","constraints":{"whitelistValidation":"property createdBy should not exist"}},
                    {"property":"updatedBy","constraints":{"whitelistValidation":"property updatedBy should not exist"}},
                    {"property":"history","constraints":{"whitelistValidation":"property history should not exist"}}]'}
    '''
    # All of the args to this function are optional.
    # Enforce required args explicitely after checking config.
    if not contactEmail:
        raise ValueError('contactEmail is required')

    if not creationLocation:
        raise ValueError('creationLocation is required')

    creationTime = creationTime or get_creationTime()
    if not creationTime:
        raise ValueError('creationTime is required')

    if not owner:
        raise ValueError('owner is required')

    if not sourceFolder:
        raise ValueError('sourceFolder is required')

    if not principalInvestigator:
        raise ValueError('principalInvestigator is required')

    if not ownerGroup:
        raise ValueError('ownerGroup is required')

    # Optional args.
    if ownerGroup:
        if accessGroups is None:
            accessGroups = [ownerGroup]
        elif ownerGroup not in accessGroups:
            # Assume accessGroups is a list
            accessGroups.append(ownerGroup)

    numberOfFiles = numberOfFiles or get_numberOfFiles(sourceFolder)

    size = size or get_size(sourceFolder)

    return RawDataset(
        # Required
        contactEmail=contactEmail,
        creationLocation=creationLocation,
        creationTime=creationTime,
        owner=owner,
        sourceFolder=sourceFolder,
        principalInvestigator=principalInvestigator,
        ownerGroup=ownerGroup,
        # Optional
        accessGroups=accessGroups,
        classification=classification,
        createdAt=createdAt,
        # createdBy=createdBy,                        # Error: ... "should not exist"???
        dataFormat=dataFormat,
        datasetName=datasetName,
        description=description,
        endTime=endTime,
        # history=history,                            # Error: ... "should not exist"???
        instrumentGroup=instrumentGroup,
        instrumentId=instrumentId,
        isPublished=isPublished,
        keywords=keywords,
        license=license,
        numberOfFiles=numberOfFiles,
        numberOfFilesArchived=numberOfFilesArchived,
        orcidOfOwner=orcidOfOwner,
        ownerEmail=ownerEmail,
        packedSize=packedSize,
        pid=pid,
        proposalId=proposalId,
        sampleId=sampleId,
        scientificMetadata=scientificMetadata,
        sharedWith=sharedWith,
        size=size,
        sourceFolderHost=sourceFolderHost,
        techniques=techniques,
        type=type_,
        updatedAt=updatedAt,
        # updatedBy=updatedBy,                         # Error: ... "should not exist"???
        validationStatus=validationStatus,
        version=version
    )

# ========================================================================
# CLI
# ========================================================================
def cli_add(args):
    # client = get_client(
    #     base_url=args.base_url,
    #     username=args.username,
    #     password=args.password
    # )
    settings = load_settings(args.config_file, os.environ, args)
    dataset = new_dataset(**settings.model_dump())
    if args.dry_run:
        print(vars(dataset))
    else:
        client = get_client(
            username=settings.username,
            password=settings.password,
            base_url=settings.base_url
        )
        dataset_id = client.datasets_create(dataset)
        print(f'{dataset_id}')
    return 0


def cli_config(args):
    # Placeholder.
    return 0


def cli_config_list(args):
    config = load_config(args.config_file)
    print(config.list())
    return 0


def cli_show(args):
    '''
    What do they want to do with the data when they get an object out of the CLI?
    '''
    settings = load_settings(args.config_file, os.environ, args)
    client = get_client(
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )
    for pid in args.dataset_id:
        dataset = client.get_dataset_by_pid(pid)
        print(json.dumps(dataset, indent=2))


def cli_list(args):
    settings = load_settings(args.config_file, os.environ, args)
    client = get_client(
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )
    for dataset in client.get_datasets():
        # print(dataset)
        pid = dataset.get('pid')
        name = dataset.get('datasetName')
        print(f'{pid}  {name}')
    return 0


def cli():
    res = 0

    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', default=os.getenv(_env_camm_config_file, ''))
    parser.add_argument('--username', default=os.getenv(_env_camm_username, ''))
    parser.add_argument('--password', default=os.getenv(_env_camm_password, ''))
    parser.add_argument('--scicat-base-url', dest='base_url', default=os.getenv(_env_camm_base_url, ''))
    parser.add_argument('--dry-run', '-n', action='store_true', default=False)

    subparsers = parser.add_subparsers()

    parse_add = subparsers.add_parser('add')
    parse_add.set_defaults(func=cli_add)

    parse_config = subparsers.add_parser('config')
    parse_config.set_defaults(func=cli_config)

    parse_show = subparsers.add_parser('show')
    parse_show.set_defaults(func=cli_show)

    parse_list = subparsers.add_parser('list')
    parse_list.set_defaults(func=cli_list)

    # Add [dataset]
    # Metadata => Required
    parse_add.add_argument('--contactEmail', type=str)
    parse_add.add_argument('--creationLocation', type=str)
    parse_add.add_argument('--creationTime', type=str)
    parse_add.add_argument('--owner', type=str)
    parse_add.add_argument('--ownerGroup', type=str)
    parse_add.add_argument('--principalInvestigator', type=str)
    parse_add.add_argument('--sourceFolder', type=str)
    # Metadata => Optional
    # createdBy=createdBy,                        # Error: ... "should not exist"???
    # history=history,                            # Error: ... "should not exist"???
    # updatedBy=updatedBy,                         # Error: ... "should not exist"???
    parse_add.add_argument('--accessGroups', type=str, nargs='*')
    parse_add.add_argument('--classification', type=str)
    parse_add.add_argument('--createdAt', type=str)
    parse_add.add_argument('--dataFormat', type=str)
    parse_add.add_argument('--datasetName', type=str)
    parse_add.add_argument('--description', type=str)
    parse_add.add_argument('--endTime', type=str)
    parse_add.add_argument('--instrumentGroup', type=str)
    parse_add.add_argument('--instrumentId', type=str)
    parse_add.add_argument('--isPublished', action='store_true', default=False)
    parse_add.add_argument('--keywords', type=str, nargs='*')
    parse_add.add_argument('--license', type=str)
    parse_add.add_argument('--numberOfFiles', type=int)
    parse_add.add_argument('--numberOfFilesArchived', type=int)
    parse_add.add_argument('--orcidOfOwner', type=str)
    parse_add.add_argument('--ownerEmail', type=str)
    parse_add.add_argument('--packedSize', type=str)
    parse_add.add_argument('--pid', type=str)
    parse_add.add_argument('--proposalId', type=str)
    parse_add.add_argument('--sampleId', type=str)
    parse_add.add_argument('--scientificMetadata', type=str, help='Dictionary')
    parse_add.add_argument('--sharedWith', type=str, nargs='*')
    parse_add.add_argument('--size', type=int)
    parse_add.add_argument('--sourceFolderHost', type=str)
    parse_add.add_argument('--techniques', type=str, nargs='*', help='List of dictionaries')
    parse_add.add_argument('--type', dest='type_', type=str)
    parse_add.add_argument('--updatedAt', type=str)
    parse_add.add_argument('--validationStatus', type=str)
    parse_add.add_argument('--version', type=str)

    parse_config_subparsers = parse_config.add_subparsers()
    parse_config_list = parse_config_subparsers.add_parser('list')
    parse_config_list.set_defaults(func=cli_config_list)

    parse_show.add_argument('dataset_id', type=str, nargs='*')

    args = parser.parse_args()
    # print(args)

    res = args.func(args)

    return res


if __name__ == '__main__':
    sys.exit(cli())


# END
