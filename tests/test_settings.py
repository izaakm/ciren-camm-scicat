import os
import pathlib
import tempfile
import pytest

from argparse import Namespace
from datetime import datetime, timezone
from unittest.mock import patch

from cammcat.settings import (
    Settings,
    load_config,
    load_settings,
    merge_settings,
    settings_from_configfile,
    settings_from_env,
    settings_from_namespace,
    standardize_setting_names,
    utcnow,
)


# ========================================================================
# Fixtures
# ========================================================================


@pytest.fixture
def make_settings():
    '''Factory for Settings instances with sensible defaults.'''
    def _make(**overrides):
        kwargs = dict(
            base_url='http://localhost:8080',
            token='test_token',
            owner='Test Owner',
            contactEmail='test@example.com',
            creationLocation='Test Lab',
        )
        kwargs.update(overrides)
        return Settings(**kwargs)
    return _make


@pytest.fixture
def make_config_file(tmp_path):
    '''Factory for temporary Python config files.'''
    def _make(**settings):
        config_path = tmp_path / 'config.py'
        lines = [f'{k} = {repr(v)}' for k, v in settings.items()]
        config_path.write_text('\n'.join(lines))
        return str(config_path)
    return _make


# ========================================================================
# Tests: utcnow()
# ========================================================================


def test_utcnow_returns_iso_format_string():
    '''utcnow() returns ISO 8601 string.'''
    result = utcnow()
    assert isinstance(result, str)
    # Parse to verify it's valid ISO format
    dt = datetime.fromisoformat(result)
    assert dt.tzinfo is not None


def test_utcnow_has_seconds_precision():
    '''utcnow() includes seconds but not microseconds.'''
    result = utcnow()
    # ISO format with seconds precision: YYYY-MM-DDTHH:MM:SS±HH:MM
    assert result.count(':') == 3  # HH:MM:SS and timezone offset


def test_utcnow_timezone_is_utc():
    '''utcnow() returns UTC timezone.'''
    result = utcnow()
    dt = datetime.fromisoformat(result)
    assert dt.utcoffset().total_seconds() == 0


# ========================================================================
# Tests: standardize_setting_names()
# ========================================================================


def test_standardize_setting_names_exact_match():
    '''standardize_setting_names() returns exact match when available.'''
    result = standardize_setting_names(['contactEmail', 'owner'])
    assert result == ['contactEmail', 'owner']


def test_standardize_setting_names_case_insensitive():
    '''standardize_setting_names() normalizes case-folded input.'''
    result = standardize_setting_names(['CONTACTEMAIL', 'Owner', 'contactemail'])
    assert result == ['contactEmail', 'owner', 'contactEmail']


def test_standardize_setting_names_raises_on_unknown():
    '''standardize_setting_names() raises ValueError for unknown settings.'''
    with pytest.raises(ValueError, match='Cannot find setting: unknownSetting'):
        standardize_setting_names(['unknownSetting'])


def test_standardize_setting_names_coerce_mode():
    '''standardize_setting_names() with errors='coerce' appends None for unknown.'''
    result = standardize_setting_names(['contactEmail', 'unknownSetting'], errors='coerce')
    assert result == ['contactEmail', None]


# ========================================================================
# Tests: Settings class
# ========================================================================


def test_settings_instantiation_with_defaults(make_settings):
    '''Settings instantiates with provided values.'''
    s = make_settings(owner='Alice')
    assert s.owner == 'Alice'
    assert s.base_url == 'http://localhost:8080'


def test_settings_creationtime_default_factory():
    '''Settings.creationTime uses default_factory when not provided.'''
    s = Settings()
    assert s.creationTime is not None
    assert isinstance(s.creationTime, str)
    # Verify it's a valid ISO timestamp
    datetime.fromisoformat(s.creationTime)


def test_settings_creationtime_override():
    '''Settings.creationTime can be overridden.'''
    custom_time = '2024-01-01T12:00:00+00:00'
    s = Settings(creationTime=custom_time)
    assert s.creationTime == custom_time


def test_settings_extra_fields_ignored():
    '''Settings ignores extra fields due to extra='ignore' config.'''
    s = Settings(owner='Test', extra_field='should_be_ignored')
    assert not hasattr(s, 'extra_field')
    assert s.owner == 'Test'


def test_settings_none_fields_allowed():
    '''Settings allows None for optional fields.'''
    s = Settings(owner=None, contactEmail=None)
    assert s.owner is None
    assert s.contactEmail is None


def test_settings_list_method(make_settings):
    '''Settings.list() returns sorted non-None fields as key=value lines.'''
    s = make_settings(owner='Alice', contactEmail='alice@example.com')
    s.principalInvestigator = None  # Explicitly set to None
    result = s.list()
    lines = result.split('\n')
    
    # Check that it's sorted
    assert lines == sorted(lines)
    # Check that None values are excluded
    assert not any('principalInvestigator' in line for line in lines)
    # Check that non-None values are included
    assert any('owner=Alice' in line for line in lines)
    assert any('contactEmail=alice@example.com' in line for line in lines)


def test_settings_list_attributes_method(make_settings):
    '''Settings.list_attributes() returns sorted all field names.'''
    s = make_settings()
    result = s.list_attributes()
    lines = result.split('\n')
    
    # Check that it's sorted
    assert lines == sorted(lines)
    # Check that all fields are present (even None ones)
    assert 'owner' in lines
    assert 'contactEmail' in lines
    assert 'base_url' in lines


def test_settings_pathlib_path_field():
    '''Settings accepts pathlib.Path for camm_repo field.'''
    path = pathlib.Path('/tmp/test')
    s = Settings(camm_repo=path)
    assert s.camm_repo == path


def test_settings_list_fields():
    '''Settings accepts list fields like keywords, accessGroups.'''
    s = Settings(
        keywords=['keyword1', 'keyword2'],
        accessGroups=['group1', 'group2']
    )
    assert s.keywords == ['keyword1', 'keyword2']
    assert s.accessGroups == ['group1', 'group2']


def test_settings_dict_field():
    '''Settings accepts dict for scientificMetadata.'''
    metadata = {'key1': 'value1', 'key2': 42}
    s = Settings(scientificMetadata=metadata)
    assert s.scientificMetadata == metadata


def test_settings_bool_field():
    '''Settings accepts bool for isPublished.'''
    s = Settings(isPublished=True)
    assert s.isPublished is True


def test_settings_int_fields():
    '''Settings accepts int for numeric fields.'''
    s = Settings(numberOfFilesArchived=10, packedSize=1024)
    assert s.numberOfFilesArchived == 10
    assert s.packedSize == 1024


# ========================================================================
# Tests: load_config()
# ========================================================================


def test_load_config_returns_settings_instance(make_config_file):
    '''load_config() executes file and returns Settings instance.'''
    config_path = make_config_file(owner='TestOwner', contactEmail='test@example.com')
    result = load_config(config_path)
    assert isinstance(result, Settings)
    assert result.owner == 'TestOwner'
    assert result.contactEmail == 'test@example.com'


def test_load_config_with_complex_data(make_config_file):
    '''load_config() handles lists and dicts from config file.'''
    config_path = make_config_file(
        keywords=['kw1', 'kw2'],
        scientificMetadata={'meta_key': 'meta_value'}
    )
    result = load_config(config_path)
    assert result.keywords == ['kw1', 'kw2']
    assert result.scientificMetadata == {'meta_key': 'meta_value'}


def test_load_config_validation_error(make_config_file, tmp_path):
    '''load_config() propagates validation errors.'''
    # Create a config with invalid data that would fail validation
    config_path = tmp_path / 'bad_config.py'
    config_path.write_text('numberOfFilesArchived = "not_an_int"')
    
    with pytest.raises(Exception):  # Pydantic ValidationError wrapped
        load_config(str(config_path))


# ========================================================================
# Tests: settings_from_configfile()
# ========================================================================


def test_settings_from_configfile_returns_dict(make_config_file):
    '''settings_from_configfile() returns dict from config module.'''
    config_path = make_config_file(owner='Alice', contactEmail='alice@example.com')
    result = settings_from_configfile(config_path)
    assert isinstance(result, dict)
    assert result['owner'] == 'Alice'
    assert result['contactEmail'] == 'alice@example.com'


# ========================================================================
# Tests: settings_from_env()
# ========================================================================


def test_settings_from_env_extracts_mapped_vars():
    '''settings_from_env() extracts environment variables by mapping.'''
    env = {
        'CAMM_OWNER': 'EnvOwner',
        'CAMM_CONTACTEMAIL': 'env@example.com',
        'CAMM_TOKEN': 'env_token',
    }
    result = settings_from_env(environ=env)
    assert result['owner'] == 'EnvOwner'
    assert result['contactEmail'] == 'env@example.com'
    assert result['token'] == 'env_token'


def test_settings_from_env_ignores_unmapped_vars():
    '''settings_from_env() ignores environment variables not in mapping.'''
    env = {
        'CAMM_OWNER': 'Owner',
        'RANDOM_VAR': 'should_be_ignored',
        'OTHER_VAR': 'also_ignored',
    }
    result = settings_from_env(environ=env)
    assert 'RANDOM_VAR' not in result
    assert result['owner'] == 'Owner'


def test_settings_from_env_empty_environ():
    with patch('os.environ', return_value={}):
        result = settings_from_env(environ={})
        assert result == {}


def test_settings_from_env_uses_os_environ_by_default(monkeypatch):
    '''settings_from_env() uses os.environ when environ=None.'''
    monkeypatch.setenv('CAMM_OWNER', 'OSEnvOwner')
    result = settings_from_env(environ=None)
    assert result['owner'] == 'OSEnvOwner'


# ========================================================================
# Tests: settings_from_namespace()
# ========================================================================


def test_settings_from_namespace_converts_argparse_namespace():
    '''settings_from_namespace() converts Namespace to dict.'''
    ns = Namespace(owner='CliOwner', contactEmail='cli@example.com', verbose=True)
    result = settings_from_namespace(ns)
    assert isinstance(result, dict)
    assert result['owner'] == 'CliOwner'
    assert result['contactEmail'] == 'cli@example.com'
    assert result['verbose'] is True


# ========================================================================
# Tests: merge_settings()
# ========================================================================


def test_merge_settings_single_dict(make_settings):
    '''merge_settings() with single dict returns Settings instance.'''
    data = {'owner': 'Alice', 'contactEmail': 'alice@example.com'}
    result = merge_settings(data)
    assert isinstance(result, Settings)
    assert result.owner == 'Alice'


def test_merge_settings_multiple_dicts_later_overwrites():
    '''merge_settings() later dicts overwrite earlier ones.'''
    dict1 = {'owner': 'Alice', 'contactEmail': 'alice@example.com'}
    dict2 = {'owner': 'Bob'}
    result = merge_settings(dict1, dict2)
    assert result.owner == 'Bob'
    assert result.contactEmail == 'alice@example.com'


def test_merge_settings_dropna_true():
    '''merge_settings(dropna=True) excludes None values.'''
    dict1 = {'owner': 'Alice', 'contactEmail': None}
    dict2 = {'contactEmail': 'alice@example.com', 'principalInvestigator': None}
    result = merge_settings(dict1, dict2, dropna=True)
    assert result.owner == 'Alice'
    assert result.contactEmail == 'alice@example.com'


def test_merge_settings_dropna_false():
    '''merge_settings(dropna=False) includes None values.'''
    dict1 = {'owner': 'Alice'}
    dict2 = {'contactEmail': None}
    result = merge_settings(dict1, dict2, dropna=False)
    assert result.contactEmail is None


def test_merge_settings_validation_error_includes_data():
    '''merge_settings() wraps validation errors with data context.'''
    invalid_data = {'numberOfFilesArchived': 'not_an_int'}
    with pytest.raises(Exception, match='data='):
        merge_settings(invalid_data)


# ========================================================================
# Tests: load_settings()
# ========================================================================


def test_load_settings_config_file_only(make_config_file):
    '''load_settings() loads from config file when only file provided.'''
    config_path = make_config_file(owner='FileOwner', contactEmail='file@example.com')
    result = load_settings(config_file=config_path)
    assert result.owner == 'FileOwner'
    assert result.contactEmail == 'file@example.com'


def test_load_settings_priority_cli_over_env_over_file(make_config_file):
    '''load_settings() applies priority: CLI > ENV > file.'''
    config_path = make_config_file(owner='FileOwner', contactEmail='file@example.com')
    env_config = {'CAMM_OWNER': 'EnvOwner'}
    cli_config = Namespace(owner='CliOwner')
    
    result = load_settings(
        config_file=config_path,
        env_config=env_config,
        cli_config=cli_config
    )
    assert result.owner == 'CliOwner'  # CLI wins
    assert result.contactEmail == 'file@example.com'  # From file


def test_load_settings_env_over_file(make_config_file):
    '''load_settings() ENV overrides file.'''
    config_path = make_config_file(owner='FileOwner', contactEmail='file@example.com')
    env_config = {'CAMM_OWNER': 'EnvOwner'}
    
    result = load_settings(config_file=config_path, env_config=env_config)
    assert result.owner == 'EnvOwner'
    assert result.contactEmail == 'file@example.com'


def test_load_settings_missing_config_file():
    '''load_settings() handles missing config file gracefully.'''
    result = load_settings(config_file='/nonexistent/path.py')
    assert isinstance(result, Settings)


def test_load_settings_errors_raise_on_bad_config_file(tmp_path):
    '''load_settings(errors='raise') raises on invalid config file.'''
    bad_config = tmp_path / 'bad.py'
    bad_config.write_text('numberOfFilesArchived = "not_an_int"')
    
    with pytest.raises(Exception):
        load_settings(config_file=str(bad_config), errors='raise')


def test_load_settings_errors_warn_on_bad_config_file(tmp_path):
    '''load_settings(errors='warn') warns instead of raising.'''
    bad_config = tmp_path / 'bad.py'
    bad_config.write_text('numberOfFilesArchived = "not_an_int"')
    
    with pytest.warns(UserWarning):
        result = load_settings(config_file=str(bad_config), errors='warn')
    assert isinstance(result, Settings)


def test_load_settings_dropna_parameter(make_config_file):
    '''load_settings(dropna=False) preserves None values.'''
    config_path = make_config_file(owner='Owner')
    result = load_settings(config_file=config_path, dropna=False)
    # All fields should exist, many as None
    assert hasattr(result, 'contactEmail')


def test_load_settings_all_sources_none(tmp_path):
    '''load_settings() with no sources returns empty Settings.'''
    result = load_settings(config_file='/nonexistent/path.py')
    assert isinstance(result, Settings)


def test_load_settings_cli_config_as_namespace(make_config_file):
    '''load_settings() accepts argparse Namespace for cli_config.'''
    config_path = make_config_file(owner='FileOwner')
    cli_config = Namespace(owner='CliOwner', contactEmail='cli@example.com')
    
    result = load_settings(config_file=config_path, cli_config=cli_config)
    assert result.owner == 'CliOwner'
    assert result.contactEmail == 'cli@example.com'


def test_load_settings_env_config_as_dict(make_config_file):
    '''load_settings() accepts dict for env_config.'''
    config_path = make_config_file(owner='FileOwner')
    env_config = {'CAMM_OWNER': 'EnvOwner'}
    
    result = load_settings(config_file=config_path, env_config=env_config)
    assert result.owner == 'EnvOwner'


def test_load_settings_merges_all_three_sources(make_config_file):
    '''load_settings() merges file, env, and cli with correct priority.'''
    config_path = make_config_file(
        owner='FileOwner',
        contactEmail='file@example.com',
        principalInvestigator='FilePi'
    )
    env_config = {'CAMM_OWNER': 'EnvOwner', 'CAMM_CONTACTEMAIL': 'env@example.com'}
    cli_config = Namespace(owner='CliOwner')
    
    result = load_settings(
        config_file=config_path,
        env_config=env_config,
        cli_config=cli_config
    )
    assert result.owner == 'CliOwner'  # CLI highest priority
    assert result.contactEmail == 'env@example.com'  # ENV over file
    assert result.principalInvestigator == 'FilePi'  # From file only
