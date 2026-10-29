'''
Tests for cammcat.models

Run with:
    pytest tests/test_models.py -v
'''
import os
from pathlib import Path

import pytest

from cammcat.models import (
    CaseInsensitiveEnum,
    ResearchDomain,
    Technique,
    DataOrigin,
    ScientificMetadata,
    CAMMDataset,
    ListOfDatasets,
    get_creationTime,
    get_numberOfFiles,
    get_size,
    get_data_file_from_path,
    get_data_block,
    new_dataset,
)


# # ========================================================================
# # Enums
# # ========================================================================
# class TestCaseInsensitiveEnum:
#
#     def test_exact_match(self):
#         assert ResearchDomain('Condensed Matter') == ResearchDomain.condensed_matter
#
#     def test_case_insensitive_match(self):
#         assert ResearchDomain('condensed matter') == ResearchDomain.condensed_matter
#         assert Technique('stm') == Technique.STM
#         assert DataOrigin('EXPERIMENTAL') == DataOrigin.experimental
#
#     def test_invalid_value_raises(self):
#         with pytest.raises(ValueError):
#             ResearchDomain('not a real domain')


# ========================================================================
# ScientificMetadata
# ========================================================================
class TestScientificMetadata:

    def test_defaults_are_none(self):
        meta = ScientificMetadata()
        assert meta.chemical_formula is None
        assert meta.technique is None

    def test_allows_extra_fields(self):
        meta = ScientificMetadata(some_extra_field='value')
        assert meta.some_extra_field == 'value'

    def test_model_dump_excludes_none_by_default(self):
        meta = ScientificMetadata(chemical_formula='H2O')
        dumped = meta.model_dump()
        assert dumped == {'chemical_formula': 'H2O'}

    def test_model_dump_enum_serialized_as_value(self):
        meta = ScientificMetadata(research_domain='quantum physics')
        dumped = meta.model_dump()
        assert dumped['research_domain'] == 'Quantum Physics'

    def test_model_dump_can_include_none(self):
        meta = ScientificMetadata(chemical_formula='H2O')
        dumped = meta.model_dump(exclude_none=False)
        assert 'temperature' in dumped
        assert dumped['temperature'] is None


# ========================================================================
# CAMMDataset
# ========================================================================
@pytest.fixture
def base_dataset_kwargs():
    return dict(
        contactEmail='someone@example.com',
        creationLocation='Lab A',
        creationTime='2024-01-01T00:00:00',
        datasetName='Example',
        owner='jdoe',
        sourceFolder='/data/some_folder',
        principalInvestigator='Dr. Someone',
        ownerGroup='group1',
        type='raw',
    )


class TestCAMMDataset:

    def test_get_existing_attribute(self, base_dataset_kwargs):
        ds = CAMMDataset(**base_dataset_kwargs)
        assert ds.get('owner') == 'jdoe'

    def test_get_missing_attribute_returns_default(self, base_dataset_kwargs):
        ds = CAMMDataset(**base_dataset_kwargs)
        assert ds.get('not_a_real_field', 'fallback') == 'fallback'

    def test_update_scientific_metadata_from_empty(self, base_dataset_kwargs):
        ds = CAMMDataset(**base_dataset_kwargs)
        ds._update_scientific_metadata({'chemical_formula': 'NaCl'})
        assert isinstance(ds.scientificMetadata, ScientificMetadata)
        assert ds.scientificMetadata.chemical_formula == 'NaCl'

    def test_update_scientific_metadata_merges_existing(self, base_dataset_kwargs):
        ds = CAMMDataset(
            **base_dataset_kwargs,
            scientificMetadata=ScientificMetadata(chemical_formula='NaCl'),
        )
        ds._update_scientific_metadata({'temperature': 300.0})
        assert ds.scientificMetadata.chemical_formula == 'NaCl'
        assert ds.scientificMetadata.temperature == 300.0

    def test_update_metadata_from_file_unsupported_suffix(self, base_dataset_kwargs):
        ds = CAMMDataset(**base_dataset_kwargs)
        with pytest.raises(NotImplementedError):
            ds.update_metadata_from_file(Path('file.unsupported'))

    def test_update_metadata_from_nexus_file(self, base_dataset_kwargs, monkeypatch):
        import cammcat.models as models

        monkeypatch.setattr(
            models.nexus,
            'get_metadata_from_nexus_file',
            lambda filepath: {'sample_name': 'sample1'},
        )
        ds = CAMMDataset(**base_dataset_kwargs)
        ds.update_metadata_from_file(Path('file.nxs'))
        assert ds.scientificMetadata.sample_name == 'sample1'

    def test_update_metadata_from_cif_file(self, base_dataset_kwargs, monkeypatch):
        import cammcat.models as models

        monkeypatch.setattr(
            models.cif,
            'get_metadata_from_cif_file',
            lambda filepath: {'chemical_formula': 'SiO2'},
        )
        ds = CAMMDataset(**base_dataset_kwargs)
        ds.update_metadata_from_file(Path('file.cif'))
        assert ds.scientificMetadata.chemical_formula == 'SiO2'

    def test_model_dump_mode_json(self, base_dataset_kwargs):
        ds = CAMMDataset(**base_dataset_kwargs)
        dumped = ds.model_dump()
        assert isinstance(dumped, dict)
        assert dumped['owner'] == 'jdoe'


# ========================================================================
# ListOfDatasets
# ========================================================================
class TestListOfDatasets:

    def test_list_default_fields(self, base_dataset_kwargs, monkeypatch):
        import cammcat.models as models

        # standardize_setting_names just passes field names through unchanged
        monkeypatch.setattr(
            models, 'standardize_setting_names', lambda fields, errors='raise': fields
        )
        kwargs = base_dataset_kwargs
        kwargs.pop('datasetName')
        ds1 = CAMMDataset(**base_dataset_kwargs, pid='pid-1', datasetName='Dataset 1')
        ds2 = CAMMDataset(**base_dataset_kwargs, pid='pid-2', datasetName='Dataset 2')
        datasets = ListOfDatasets([ds1, ds2])

        fields, lines = datasets.list()

        assert fields == ['pid', 'datasetName']
        assert lines == [['pid-1', 'Dataset 1'], ['pid-2', 'Dataset 2']]

    def test_list_missing_field_uses_default(self, base_dataset_kwargs, monkeypatch):
        import cammcat.models as models
        monkeypatch.setattr(
            models, 'standardize_setting_names', lambda fields, errors='raise': fields
        )
        ds = CAMMDataset(**base_dataset_kwargs)
        datasets = ListOfDatasets([ds])
        fields, lines = datasets.list(fields=['not_a_real_field'], default='N/A')
        assert lines == [['N/A']]


# ========================================================================
# Filesystem helper functions
# ========================================================================
@pytest.fixture
def tmp_dataset(tmp_path):
    '''
    tmp_path
        gives each test a fresh, unique temporary directory, automatically
        cleaned up after the test

    pytest sees tmp_dataset is a fixture (because of @pytest.fixture), then
    sees tmp_path and recongizes it as a built-in fixture, and injects it.
    '''
    sub = tmp_path / 'sub'
    sub.mkdir()

    (tmp_path / 'a.txt').write_bytes(b'hello')
    (tmp_path / 'b.txt').write_bytes(b'world!')
    (sub / 'c.txt').write_bytes(b'123')

    return tmp_path


class TestFileHelpers:

    def test_get_creationTime_returns_iso_string(self):
        result = get_creationTime()
        assert isinstance(result, str)
        # Should be parseable as an ISO format datetime string.
        from datetime import datetime
        datetime.fromisoformat(result)

    def test_get_numberOfFiles(self, tmp_dataset):
        assert get_numberOfFiles(tmp_dataset) == 3

    def test_get_size(self, tmp_dataset):
        expected = len(b'hello') + len(b'world!') + len(b'123')
        assert get_size(tmp_dataset) == expected

    def test_get_data_file_from_path_no_checksum(self, tmp_dataset):
        filepath = tmp_dataset / 'a.txt'
        data_file = get_data_file_from_path(str(filepath))
        assert data_file.path == str(filepath)
        assert data_file.size == len(b'hello')
        assert data_file.chk is None

    def test_get_data_file_from_path_relative(self, tmp_dataset):
        filepath = tmp_dataset / 'a.txt'
        data_file = get_data_file_from_path(str(filepath), relative_to=str(tmp_dataset))
        assert data_file.path == 'a.txt'

    def test_get_data_file_from_path_with_checksum(self, tmp_dataset, monkeypatch):
        import cammcat.models as models

        monkeypatch.setattr(models.utils, 'sha256sum', lambda filepath: 'fakehash')
        filepath = tmp_dataset / 'a.txt'
        data_file = get_data_file_from_path(str(filepath), chkAlg='sha256')
        assert data_file.chk == 'fakehash'

    def test_get_data_file_from_path_unsupported_checksum(self, tmp_dataset):
        filepath = tmp_dataset / 'a.txt'
        with pytest.raises(NotImplementedError):
            get_data_file_from_path(str(filepath), chkAlg='md5')

    def test_get_data_block(self, tmp_dataset):
        block = get_data_block(str(tmp_dataset))
        assert len(block.dataFileList) == 3
        assert block.size == len(b'hello') + len(b'world!') + len(b'123')

    def test_get_data_block_missing_folder_raises(self, tmp_path):
        missing = tmp_path / 'does_not_exist'
        with pytest.raises(FileNotFoundError):
            get_data_block(str(missing))


# ========================================================================
# new_dataset
# ========================================================================
class TestNewDataset:

    def test_missing_required_fields_raise(self, tmp_dataset):
        with pytest.raises(ValueError):
            new_dataset(
                sourceFolder=str(tmp_dataset),
            )

    def test_creates_dataset_with_defaults(self, tmp_dataset):
        ds = new_dataset(
            contactEmail='someone@example.com',
            creationLocation='Lab A',
            owner='jdoe',
            sourceFolder=str(tmp_dataset),
            principalInvestigator='Dr. Someone',
            ownerGroup='group1',
        )
        assert isinstance(ds, CAMMDataset)
        assert ds.numberOfFiles == 3
        assert ds.size == len(b'hello') + len(b'world!') + len(b'123')
        assert ds.accessGroups == ['group1']

    def test_ownerGroup_added_to_access_groups(self, tmp_dataset):
        ds = new_dataset(
            contactEmail='someone@example.com',
            creationLocation='Lab A',
            owner='jdoe',
            sourceFolder=str(tmp_dataset),
            principalInvestigator='Dr. Someone',
            ownerGroup='group1',
            accessGroups=['group2'],
        )
        assert ds.accessGroups == ['group2', 'group1']

    def test_relative_to_sets_relative_source_folder(self, tmp_dataset):
        parent = tmp_dataset.parent
        ds = new_dataset(
            contactEmail='someone@example.com',
            creationLocation='Lab A',
            owner='jdoe',
            sourceFolder=str(tmp_dataset),
            principalInvestigator='Dr. Someone',
            ownerGroup='group1',
            relative_to=str(parent),
        )
        assert ds.sourceFolder == tmp_dataset.name

    def test_override_numberOfFiles(self, tmp_dataset):
        ds = new_dataset(
            contactEmail='someone@example.com',
            creationLocation='Lab A',
            owner='jdoe',
            sourceFolder=str(tmp_dataset),
            principalInvestigator='Dr. Someone',
            ownerGroup='group1',
            numberOfFiles=99,
            size=12345,
        )
        assert ds.numberOfFiles == 99, f'numberOfFiles is {ds.numberOfFiles}, should be 99'

    def test_override_size(self, tmp_dataset):
        ds = new_dataset(
            contactEmail='someone@example.com',
            creationLocation='Lab A',
            owner='jdoe',
            sourceFolder=str(tmp_dataset),
            principalInvestigator='Dr. Someone',
            ownerGroup='group1',
            numberOfFiles=99,
            size=12345,
        )
        assert ds.size == 12345
