import os

from collections import UserList
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from pyscicat.model import (
    Attachment,
    CreateDatasetOrigDatablockDto,
    DataFile,
    DatasetType,
    DerivedDataset,
    Ownable,
    RawDataset,
)

from cammcat.datatypes import cif, nexus
from cammcat.settings import standardize_setting_names
from cammcat import utils

# ========================================================================
# Dataset
# ========================================================================
class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class ResearchDomain(CaseInsensitiveEnum):
    condensed_matter = 'Condensed Matter'
    quantum_physics = 'Quantum Physics'
    materials_science = 'Materials Science'
    neutron_scattering = 'Neutron Scattering'


class Technique(CaseInsensitiveEnum):
    STM = 'STM'
    STS = 'STS'
    DFT = 'DFT'
    PIMC = 'PIMC'
    INS = 'INS'
    persistent_homology = 'Persistent Homology'
    machine_learning_potential = 'Machine Learning Potential'


class DataOrigin(CaseInsensitiveEnum):
    experimental = 'Experimental'
    computational = 'Computational'
    hybrid = 'Hybrid'


# class ScientificMetadata(BaseModel, extra='allow'):
#     pass

class ScientificMetadata(BaseModel, extra='allow'):
    chemical_formula: Optional[str] = None
    data_origin: Optional[DataOrigin] = None
    date: Optional[str] = None
    experiment_type: Optional[str] = None
    instrument_name: Optional[str] = None
    pressure: Optional[float] = None
    research_domain: Optional[ResearchDomain] = None
    sample_name: Optional[str] = None
    technique: Optional[list[Technique]] = None
    temperature: Optional[float] = None

    def model_dump(self, *args, **kwargs):
        # At the time of writing, there is no way to set `mode="json"` as the default.
        # See: https://github.com/pydantic/pydantic/issues/11647
        # WARNING: This doesn't work in ipython with `%autoreload`:
        #   ----> 1 m.model_dump()
        #   File <string>:3, in model_dump(self, *args, **kwargs)
        #         1 'Could not get source, probably due dynamically evaluated source code.'
        #   RuntimeError: super(): __class__ cell not found
        kwargs.setdefault('exclude_none',True)
        kwargs.setdefault('mode', 'json')
        return super().model_dump(*args, **kwargs)

# Base classes, for reference
# ---------------------------
# class RawDataset(DatasetCommon):
#     """
#     Raw datasets from which derived datasets are... derived.
#     """
#     creationLocation: str  # Required for a raw dataset
#     dataFormat: Optional[str] = None
#     endTime: Optional[str] = None  # datetime
#     inputDatasets: Optional[List[str]] = None                  * also in DerivedDataset
#     owner: str                                                 * also in DerivedDataset
#     principalInvestigator: str  # Required for a raw dataset
#     proposalId: Optional[str] = None                           * also in DerivedDataset
#     sampleId: Optional[str] = None
#     type: DatasetType = DatasetType.raw                        * also in DerivedDataset
#     usedSoftware: Optional[List[str]] = None                   * also in DerivedDataset
#
# class DerivedDataset(DatasetCommon):
#     """
#     Derived datasets which have been generated based on one or more raw datasets
#     """
#     inputDatasets: List[str] = []
#     owner: str
#     proposalId: Optional[str] = None
#     type: DatasetType = DatasetType.derived
#     usedSoftware: List[str] = []

class CAMMDataset(RawDataset):
    '''
    This is the primary class for handling CAMM datasets.
    '''
    # scientificMetadata: Optional[dict[str,Any]] = None
    scientificMetadata: Optional[ScientificMetadata] = Field(
        default=None,
        title='Scientific Metadata',
        description='Metadata for experimental and simulation values.',
    )

    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def _update_scientific_metadata(self, new):
        if self.scientificMetadata is None:
            metadata = {}
        else:
            metadata = self.scientificMetadata.model_dump()
        metadata.update(new)
        self.scientificMetadata = ScientificMetadata(**metadata)

    def update_metadata_from_file(self, filepath:Path):
        if filepath.suffix == '.nxs':
            metadata = nexus.get_metadata_from_nexus_file(filepath)
        elif filepath.suffix == '.cif':
            metadata = cif.get_metadata_from_cif_file(filepath)
        else:
            raise NotImplementedError(f'Cannot extract metadata file type "{filepath.suffix}": {filepath}')
        self._update_scientific_metadata(metadata)

    def model_dump(self, *args, **kwargs):
        # At the time of writing, there is no way to set `mode="json"` as the default.
        # See: https://github.com/pydantic/pydantic/issues/11647
        # WARNING: This doesn't work in ipython with `%autoreload`:
        #   ----> 1 m.model_dump()
        #   File <string>:3, in model_dump(self, *args, **kwargs)
        #         1 'Could not get source, probably due dynamically evaluated source code.'
        #   RuntimeError: super(): __class__ cell not found
        kwargs.setdefault('mode', 'json')
        return super().model_dump(*args, **kwargs)

    def to_json(self):
        pass

    def to_yaml(self):
        pass

    def to_text(self):
        pass


class ListOfDatasets(UserList):

    def list(self, fields=None, default=''):
        fields = fields or ['pid', 'datasetName']
        fields = standardize_setting_names(fields, errors='raise')
        lines = []
        for dataset in self.data:
            line = []
            for field in fields:
                line.append(dataset.get(field, default))
            lines.append(line)
        return fields, lines


# Attributes of RawDataset, for reference
# =======================================
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
        size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    return size


def get_data_file_from_path(filepath, chkAlg=None, relative_to=None, **kwargs):
    '''
    class DataFile(MongoQueryable):
        """
        A reference to a file in SciCat. Path is relative
        to the Dataset's sourceFolder parameter
        """
        path: str
        size: int
        time: Optional[str] = None
        chk: Optional[str] = None
        uid: Optional[str] = None
        gid: Optional[str] = None
        perm: Optional[str] = None
    '''
    if relative_to:
        path = os.path.relpath(filepath, start=relative_to)
    else:
        path = filepath

    stats = os.stat(filepath)
    # os.stat_result(st_mode=33188, st_ino=7876932, st_dev=234881026,
    # st_nlink=1, st_uid=501, st_gid=501, st_size=264, st_atime=1297230295,
    # st_mtime=1297230027, st_ctime=1297230027)

    if chkAlg is None:
        chk = None
    elif chkAlg.casefold().startswith('sha256'):
        chk = utils.sha256sum(filepath)
    else:
        raise NotImplementedError(f'Checksum algorithm not implemented: {chkAlg}')

    return DataFile(
        path=path,
        size=stats.st_size,
        time=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(), # schema requires str|None
        chk=chk,                            # Checksum?
        uid=str(stats.st_uid),
        gid=str(stats.st_gid),
        perm=None,                          # How to get permissions?
        createdAt=kwargs.get('createdAt'),  # From MongoQueryable
        createdBy=kwargs.get('createdBy'),  # From MongoQueryable
        updatedAt=kwargs.get('updatedAt'),  # From MongoQueryable
        updatedBy=kwargs.get('updatedBy'),  # From MongoQueryable
    )


def get_data_block(sourceFolder, chkAlg=None, relative_to=None, **kwargs):
    '''
    Return a list of DataFiles

        class CreateDatasetOrigDatablockDto(BaseModel):
            """
            DTO for creating a new dataset with an original datablock
            """
            size: int
            dataFileList: List[DataFile]
            chkAlg: Optional[str] = None

    '''
    if not os.path.isdir(sourceFolder):
        raise FileNotFoundError(f'sourceFolder not found or not a directory: {sourceFolder}')
    dataFileList = []
    for root, dirs, files in os.walk(sourceFolder):
        for filename in files:
            filepath = os.path.join(root, filename)
            dataFileList.append(
                get_data_file_from_path(
                    filepath,
                    chkAlg=chkAlg,
                    relative_to=relative_to,
                    **kwargs
                )
            )
    size = sum([f.size for f in dataFileList])
    # print(size)
    # print(dataFileList)
    # print(chkAlg)
    # Hack because pydantic seems to think chkAlg is supposed to be an int, not a str.
    # if chkAlg == 'sha256' or chkAlg == 'sha256sum':
    #     chkAlg = 256
    return CreateDatasetOrigDatablockDto(
        size=size,
        dataFileList=dataFileList,
        chkAlg=chkAlg
    )


# [TODO] Handle "DerivedDataset" class????
def new_dataset(
        # Required for pyscicat *Dataset* classes
        contactEmail: str | None = None,
        creationLocation: str | None = None,
        creationTime: str | None = None,
        owner: str | None = None,
        sourceFolder: str | None = None,
        principalInvestigator: str | None = None,
        ownerGroup: str | None = None,
        datasetName: str | None = None,

        # Optional
        accessGroups: List[str] | None = None,
        classification: str | None = None,
        createdAt: str | None = None,
        createdBy: str | None = None,
        dataFormat: str | None = None,
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
        type_: str|None = 'raw',
        updatedAt: str | None = None,
        updatedBy: str | None = None,
        validationStatus: str | None = None,
        version: str | None = None,

        # Others
        relative_to=None,
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

    if relative_to:
        path = os.path.relpath(sourceFolder, start=relative_to)
    else:
        path = sourceFolder

    datasetName = datasetName or os.path.basename(path)

    # if type_ == 'raw':
    #     type_ = DatasetType.raw
    # else:
    #     type_ = DatasetType.derived

    return CAMMDataset(
        # Required
        contactEmail=contactEmail,
        creationLocation=creationLocation,
        creationTime=creationTime,
        owner=owner,
        sourceFolder=path,
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
        updatedAt=updatedAt,
        # updatedBy=updatedBy,                         # Error: ... "should not exist"???
        validationStatus=validationStatus,
        version=version
    )

