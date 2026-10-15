import h5py
import json

# from pathlib import Path


def _get_instrument_name(file):
    # print(f['MDHistoWorkspace']['experiment0']['instrument']['name'])
    try:
        value = file['MDHistoWorkspace/experiment0/instrument/name']
        return value.asstr()[0].strip()
    except KeyError as e:
        return None


def _get_instrument_date(file):
    # print('date:', f['MDHistoWorkspace']['experiment0']['instrument']['instrument_parameter_map']['date'])
    try:
        value = file['MDHistoWorkspace/experiment0/instrument/instrument_parameter_map/date']
        return value.asstr()[0].strip()
    except KeyError as e:
        return None


def _get_sample_name(file):
    # f['MDHistoWorkspace']['experiment0']['sample'].attrs['name'].decode()
    try:
        value = file['MDHistoWorkspace']['experiment0']['sample']
        return value.attrs['name'].decode().strip()
    except KeyError as e:
        return None

def _get_sample_material_temperature(file):
    # print('temp:', f['MDHistoWorkspace']['experiment0']['sample']['material']['temperature'])
    try:
        value = file['MDHistoWorkspace/experiment0/sample/material/temperature']
        return value[0]
    except KeyError as e:
        return None


def _get_sample_material_pressure(file):
    try:
        value = file['MDHistoWorkspace/experiment0/sample/material/pressure']
        return value[0]
    except KeyError as e:
        return None


def get_metadata_from_nexus_file(filepath):
    with h5py.File(filepath) as file:
        metadata = {
            'instrument_name': _get_instrument_name(file),
            'sample_name': _get_sample_name(file),
            'date': _get_instrument_date(file),
            'temperature': _get_sample_material_temperature(file),
            'pressure': _get_sample_material_pressure(file)
        }
    return metadata

