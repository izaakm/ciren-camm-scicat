import gemmi

from pathlib import Path
from typing import Any


# Mapping: output field -> possible CIF tag names, in preference order.
_METADATA_TAGS = {
    'database_code': (
        '_database_code_depnum_ccdc_archive',
        '_database_code_CSD',
        '_database_code_ICSD',
        '_entry.id',
    ),
    'chemical_name': (
        '_chemical_name_common',
        '_chemical_name_systematic',
        '_chemical.name_common',
        '_chemical.name_systematic',
    ),
    'formula_sum': (
        '_chemical_formula_sum',
        '_chemical_formula.structural'
    ),
    'formula_weight': (
        '_chemical_formula_weight',
        '_chemical_formula.weight'
    ),
    'doi': (
        '_journal_paper_doi',
        '_citation.doi'
    ),
    'authors': (
        '_publ_author_name',
        '_citation_author.name'
    ),
    'publication_title': (
        '_publ_section_title',
        '_citation.title'
    ),
    'journal': (
        '_journal_name_full',
        '_citation.journal_full'
    ),
    'publication_year': (
        '_journal_year',
        '_citation.year'
    ),
    'temperature_K': (
        '_diffrn_ambient_temperature',
        '_cell_measurement_temperature'
    ),
    'pressure_kPa': (
        '_diffrn_ambient_pressure',
    ),
    'crystal_system': (
        '_space_group_crystal_system',
        '_symmetry_cell_setting'
    ),
    'space_group': (
        '_space_group_name_H-M_alt',
        '_symmetry_space_group_name_H-M',
        '_space_group.name_H-M_alt',
    ),
    'space_group_number': (
        '_space_group_IT_number',
        '_symmetry_Int_Tables_number'
    ),
    'cell_length_a': (
        '_cell_length_a',
        '_cell.length_a'
    ),
    'cell_length_b': (
        '_cell_length_b',
        '_cell.length_b'
    ),
    'cell_length_c': (
        '_cell_length_c',
        '_cell.length_c'
    ),
    'cell_angle_alpha': (
        '_cell_angle_alpha',
        '_cell.angle_alpha'
    ),
    'cell_angle_beta': (
        '_cell_angle_beta',
        '_cell.angle_beta'
    ),
    'cell_angle_gamma': (
        '_cell_angle_gamma',
        '_cell.angle_gamma'
    ),
    'cell_volume': (
        '_cell_volume',
        '_cell.volume'
    ),
    'z_value': (
        '_cell_formula_units_Z',
        '_cell.Z_PDB'
    ),
    'radiation_type': (
        '_diffrn_radiation_type',
        '_diffrn_radiation.type'
    ),
    'wavelength': (
        '_diffrn_radiation_wavelength',
        '_diffrn_radiation_wavelength.wavelength'
    ),
    'r_factor': (
        '_refine_ls_R_factor_gt',
        '_refine_ls_R_factor_all'
    ),
}


def _clean_cif_value(
        value: str | None
    ) -> str | None:
    '''
    Convert a raw Gemmi CIF value to a plain string or None.
    '''
    if value is None or value in {'?', '.'}:
        return None
    try:
        return gemmi.cif.as_string(value).strip()
    except (ValueError, TypeError):
        return value.strip().strip("'\"")


def _first_value(
        block: gemmi.cif.Block,
        tags: tuple[str, ...]
    ) -> str | None:
    '''
    Return the first present scalar value among synonymous CIF tags.
    '''
    for tag in tags:
        value = _clean_cif_value(block.find_value(tag))
        if value:
            return value
    return None


def _all_values(
        block: gemmi.cif.Block,
        tags: tuple[str, ...]
    ) -> list[str]:
    '''
    Return values from the first matching scalar or looped CIF tag.
    '''
    for tag in tags:
        values = [_clean_cif_value(v) for v in block.find_values(tag)]
        cleaned = [v for v in values if v]
        if cleaned:
            return cleaned
    return []


def get_metadata_from_cif_file(filepath):
    '''
    Extract commonly used metadata from the first data block of a CIF.

    Values are returned as strings so crystallographic uncertainty notation,
    such as ``12.345(6)``, is preserved. Missing values are returned as None.
    '''
    path = Path(filepath)
    document = gemmi.cif.read_file(str(path))
    if len(document) == 0:
        raise ValueError(f'No data blocks found in CIF: {path}')

    block = document[0]
    metadata = {
        'file_name': path.name,
        'data_block': block.name,
    }

    for field, tags in _METADATA_TAGS.items():
        if field == 'authors':
            metadata[field] = _all_values(block, tags)
        else:
            metadata[field] = _first_value(block, tags)
    return metadata

