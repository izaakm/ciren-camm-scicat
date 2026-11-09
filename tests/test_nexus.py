import h5py
import pytest

@pytest.fixture
def make_nexus_file(tmp_path):
    '''
    Factory fixture for creating minimal NeXus HDF5 files.
    
    Returns a callable that accepts keyword overrides for each metadata field.
    All fields default to valid values; pass None to omit a field.
    '''
    def _make(
        instrument_name='SANS2D',
        instrument_date='2023-01-15',
        sample_name='test_sample',
        temperature=300.0,
        pressure=1.0,
    ):
        filepath = tmp_path / 'test.nxs'
        
        with h5py.File(filepath, 'w') as f:
            # Create the NeXus structure
            ws = f.create_group('MDHistoWorkspace')
            exp = ws.create_group('experiment0')
            
            # Instrument group
            instr = exp.create_group('instrument')
            if instrument_name is not None:
                instr.create_dataset('name', data=[instrument_name.encode()])
            
            # Instrument parameter map (for date)
            param_map = instr.create_group('instrument_parameter_map')
            if instrument_date is not None:
                param_map.create_dataset('date', data=[instrument_date.encode()])
            
            # Sample group
            sample = exp.create_group('sample')
            if sample_name is not None:
                sample.attrs['name'] = sample_name.encode()
            
            # Sample material (for temperature and pressure)
            material = sample.create_group('material')
            if temperature is not None:
                material.create_dataset('temperature', data=[temperature])
            if pressure is not None:
                material.create_dataset('pressure', data=[pressure])
        
        return filepath
    
    return _make

def test_all_fields_present(make_nexus_file):
    '''
    All metadata fields present and correctly extracted.
    '''
    from cammcat.datatypes.nexus import get_metadata_from_nexus_file
    
    filepath = make_nexus_file(
        instrument_name='  SANS2D  ',   # whitespace should be stripped
        instrument_date='2023-01-15',
        sample_name='  test_sample  ',  # whitespace should be stripped
        temperature=300.5,
        pressure=1.013,
    )
    
    metadata = get_metadata_from_nexus_file(filepath)
    
    # Check structure
    assert isinstance(metadata, dict)
    assert set(metadata.keys()) == {
        'instrument_name', 'sample_name', 'date', 'temperature', 'pressure'
    }
    
    # Check types and values
    assert metadata['instrument_name'] == 'SANS2D'   # whitespace stripped
    assert metadata['sample_name'] == 'test_sample'  # whitespace stripped
    assert metadata['date'] == '2023-01-15'
    assert metadata['temperature'] == pytest.approx(300.5)
    assert metadata['pressure'] == pytest.approx(1.013)

