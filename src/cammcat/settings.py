import os
import runpy

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, ConfigDict, Field

# Some names of environment variables.
_env_camm_config_file = 'CAMM_CONFIG_FILE'
_env_camm_username = 'CAMM_USERNAME'
_env_camm_password = 'CAMM_PASSWORD'
_env_camm_base_url = 'CAMM_BASE_URL'


# # owner vs contact ??? ~> PI? ~> createdBy?
# example_config: dict[str, Any] = {
#     'contactEmail': 'izaak@utk.edu',  # Required
#     'creationLocation': 'University of Tennessee, Knoxville',  # Required
#     'creationTime': None,  # Required
#     'owner': 'Izaak Miller',  # Required
#     'sourceFolder': None,  # Required
#     'principalInvestigator': 'Adrian del Maestro',  # Required
#     'ownerGroup': 'CAMM',  # Required
#     'accessGroups': [],
#     'classification': None,
#     'createdAt': None,
#     'createdBy': None,
#     'dataFormat': None,
#     'datasetName': None,
#     'description': None,
#     'endTime': None,
#     'history': [],
#     'instrumentGroup': None,
#     'instrumentId': None,
#     'isPublished': False,
#     'keywords': [],
#     'license': None,
#     'numberOfFiles': None,
#     'numberOfFilesArchived': -1,
#     'orcidOfOwner': '0000-0000-0000-0000',
#     'ownerEmail': 'izaak@utk.edu',
#     'packedSize': -1,
#     'pid': None,  # ????
#     'proposalId': None,
#     'sampleId': None,
#     'scientificMetadata': {},
#     'sharedWith': [],
#     'size': None,
#     'sourceFolderHost': None,
#     'techniques': [],
#     'type': 'raw',
#     'updatedAt': None,
#     'updatedBy': None,
#     'validationStatus': None,
#     'version': None,
# }

# owner vs contact ??? ~> PI? ~> createdBy?
# This is actually a list of "metadata" attributes for a dataset, not
# "settings" that control the behavior of this library.
# [TODO] Split "settings" from the "metadata" attributes for a dataset.
list_of_settings: List[str] = [
    'contactEmail',
    'creationLocation',
    'creationTime',
    'owner',
    'sourceFolder',
    'principalInvestigator',
    'ownerGroup',
    'accessGroups',
    'classification',
    'createdAt',
    'createdBy',
    'dataFormat',
    'datasetName',
    'description',
    'endTime',
    'history',
    'instrumentGroup',
    'instrumentId',
    'isPublished',
    'keywords',
    'license',
    'numberOfFiles',
    'numberOfFilesArchived',
    'orcidOfOwner',
    'ownerEmail',
    'packedSize',
    'pid',
    'proposalId',
    'sampleId',
    'scientificMetadata',
    'sharedWith',
    'size',
    'sourceFolderHost',
    'techniques',
    'type',
    'updatedAt',
    'updatedBy',
    'validationStatus',
    'version',
]

# Use the keys from the example config, e.g.:
# { 'CAMM_OWNEREMAIL': 'ownerEmail', ... }
env2setting = {f'CAMM_{setting.upper()}': setting for setting in list_of_settings} 
env2setting[_env_camm_config_file] = 'config_file'
env2setting[_env_camm_username] = 'username'
env2setting[_env_camm_password] = 'password'
env2setting[_env_camm_base_url] = 'base_url'

# Helper: contactemail => contactEmail
casefold_settings = {setting.casefold():setting for setting in list_of_settings}

def standardize_setting_names(settings, errors='raise'):
    '''
    Given a list of "settings", get the standard name of that setting, e.g.:

        given    : contactemail
        standard : contactEmail
    '''
    found = []
    for given in settings:
        standard = casefold_settings.get(given.casefold())
        if not standard and errors != 'coerce':
            raise ValueError(f'Cannot find setting: {given}')
        found.append(standard)
    return found


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


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

class Settings(BaseModel):
    # Client settings
    base_url: str|None = None
    username: str|None = None
    password: str|None = None

    # Dataset settings
    # owner vs contact ??? ~> PI? ~> createdBy?
    contactEmail: str|None = None
    creationLocation: str|None = None
    creationTime: str|None = Field(default_factory=utcnow)
    owner: str|None = None
    sourceFolder: str|None = None
    principalInvestigator: str|None = None
    ownerGroup: str|None = None
    accessGroups: List[str]|None = None
    classification: str|None = None
    # createdAt: str|None = Field(default_factory=utcnow)
    # ^pyscicat.client.ScicatCommError: Error in operation datasets_create: {'status': 400, 'message': '[{...},{"property":"createdAt","constraints":{"whitelistValidation":"property createdAt should not exist"}}]'}
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
    # updatedAt: str|None = Field(default_factory=utcnow)
    # ^pyscicat.client.ScicatCommError: Error in operation datasets_create: {'status': 400, 'message': '[{"property":"updatedAt","constraints":{"whitelistValidation":"property updatedAt should not exist"}},{...}]'}
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
def settings_from_env(environ=None, keys=env2setting):
    environ = environ or os.environ
    data = {}
    for env_key, config_key in env2setting.items():
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


def load_settings(config_file, env_config, cli_config, dropna=True, errors='raise'):
    '''
    Load and merge settings. Priority (high to low):

        CLI > ENV > config file
    '''
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

    # This probably needs to be implemented separately for each cli command.
    # if errors != 'ignore':
    #     if settings.sourceFolder is None:
    #         raise ValueError('sourceFolder cannot be None')
    #     elif not os.path.isdir(settings.sourceFolder):
    #         raise FileNotFoundError(f'sourceFolder does not exist or is not a directory: {settings.sourceFolder}')

    return settings


