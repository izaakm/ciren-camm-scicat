import pytest
import gemmi
from pathlib import Path
from cammcat.datatypes.cif import get_metadata_from_cif_file


@pytest.fixture
def make_cif_file(tmp_path):
    '''
    Factory fixture to create minimal CIF files for testing.
    '''
    def _make(data_block_name="test_block", tags_and_values=None, **overrides):
        '''
        Create a CIF file with specified tags and values.

        Args:
            data_block_name: Name of the data block
            tags_and_values: Dict of {tag: value} pairs to add to the block
            **overrides: Additional tags to override/add
        '''
        if tags_and_values is None:
            tags_and_values = {}
        tags_and_values.update(overrides)

        # Build CIF content as a string
        cif_content = f"data_{data_block_name}\n"
        for tag, value in tags_and_values.items():
            # Quote values that contain spaces or special characters
            if ' ' in value or '\\' in value:
                quoted_value = f"'{value}'"
            else:
                quoted_value = value
            cif_content += f"{tag} {quoted_value}\n"

        filepath = tmp_path / f"{data_block_name}.cif"
        filepath.write_text(cif_content)
        return filepath

    return _make


def test_get_metadata_from_cif_file_valid(make_cif_file):
    '''
    Test that valid CIF file is read and metadata dict has expected structure.
    '''
    filepath = make_cif_file(
        data_block_name="my_structure",
        tags_and_values={
            '_database_code_depnum_ccdc_archive': '12345',
            '_chemical_name_common': 'Test Compound',
            '_chemical_formula_sum': 'C6 H12 O6',
            '_chemical_formula_weight': '180.156',
            '_journal_paper_doi': '10.1234/test',
            '_publ_author_name': 'Smith, J.',
            '_publ_section_title': 'A Test Structure',
            '_journal_name_full': 'Test Journal',
            '_journal_year': '2023',
            '_diffrn_ambient_temperature': '298',
            '_diffrn_ambient_pressure': '101325',
            '_space_group_name_H-M_alt': 'P 1',
            '_space_group_IT_number': '1',
            '_cell_length_a': '10.0',
            '_cell_length_b': '11.0',
            '_cell_length_c': '12.0',
            '_cell_angle_alpha': '90.0',
            '_cell_angle_beta': '90.0',
            '_cell_angle_gamma': '90.0',
            '_cell_volume': '1320.0',
            '_cell_formula_units_Z': '4',
            '_diffrn_radiation_type': 'MoK\\a',
            '_diffrn_radiation_wavelength': '0.71073',
            '_refine_ls_R_factor_gt': '0.045',
        }
    )

    metadata = get_metadata_from_cif_file(filepath)

    # Check structure: dict with expected keys
    assert isinstance(metadata, dict)
    assert 'file_name' in metadata
    assert 'data_block' in metadata
    assert metadata['file_name'] == 'my_structure.cif'
    assert metadata['data_block'] == 'my_structure'

    # Check that populated fields are present and non-empty
    assert metadata['database_code'] == '12345'
    assert metadata['chemical_name'] == 'Test Compound'
    assert metadata['formula_sum'] == 'C6 H12 O6'
    assert metadata['formula_weight'] == '180.156'
    assert metadata['doi'] == '10.1234/test'
    assert metadata['authors'] == ['Smith, J.']
    assert metadata['publication_title'] == 'A Test Structure'
    assert metadata['journal'] == 'Test Journal'
    assert metadata['publication_year'] == '2023'
    assert metadata['temperature_K'] == '298'
    assert metadata['pressure_kPa'] == '101325'
    assert metadata['space_group'] == 'P 1'
    assert metadata['space_group_number'] == '1'
    assert metadata['cell_length_a'] == '10.0'
    assert metadata['cell_length_b'] == '11.0'
    assert metadata['cell_length_c'] == '12.0'
    assert metadata['cell_angle_alpha'] == '90.0'
    assert metadata['cell_angle_beta'] == '90.0'
    assert metadata['cell_angle_gamma'] == '90.0'
    assert metadata['cell_volume'] == '1320.0'
    assert metadata['z_value'] == '4'
    assert metadata['radiation_type'] == 'MoK\\a'
    assert metadata['wavelength'] == '0.71073'
    assert metadata['r_factor'] == '0.045'


def test_get_metadata_from_cif_file_missing_fields(make_cif_file):
    '''
    Test that missing metadata fields are returned as None or empty list.
    '''
    filepath = make_cif_file(
        data_block_name="sparse_block",
        tags_and_values={
            '_cell_length_a': '10.0',
        }
    )

    metadata = get_metadata_from_cif_file(filepath)

    # Check required keys are present
    assert 'file_name' in metadata
    assert 'data_block' in metadata
    assert metadata['file_name'] == 'sparse_block.cif'
    assert metadata['data_block'] == 'sparse_block'

    # Check that present field has value
    assert metadata['cell_length_a'] == '10.0'

    # Check that missing scalar fields are None
    assert metadata['database_code'] is None
    assert metadata['chemical_name'] is None
    assert metadata['formula_sum'] is None
    assert metadata['doi'] is None
    assert metadata['temperature_K'] is None

    # Check that missing list field (authors) is empty list
    assert metadata['authors'] == []


def test_get_metadata_from_cif_file_empty_cif(tmp_path):
    '''
    Test that empty CIF (no data blocks) raises ValueError.
    '''
    # Create an empty CIF document with no blocks
    doc = gemmi.cif.Document()
    filepath = tmp_path / "empty.cif"
    doc.write_file(str(filepath))

    with pytest.raises(ValueError, match="No data blocks found"):
        get_metadata_from_cif_file(filepath)
