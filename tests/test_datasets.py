import os


from pathlib import Path
from cammcat import datasets
from unittest.mock import patch


def test_get_key():
    with patch('os.urandom', return_value=b'\x00' * 20):
        result = datasets.get_key()
        assert result == '00' * 20
        assert len(result) == 40


def test_get_dest_path():
    dst = datasets.get_dest_path()
    assert str(dst) == '.'

    dst = datasets.get_dest_path(parent='data/camm')
    assert str(dst) == 'data/camm'


def test_get_dest_path_with_key():
    with patch('os.urandom', return_value=b'\x00' * 20):
        key = datasets.get_key()

        dst = datasets.get_dest_path(key=key)
        assert str(dst) == '00/00000000000000000000000000000000000000'

        dst = datasets.get_dest_path(parent='data/camm', key=key)
        assert str(dst) == 'data/camm/00/00000000000000000000000000000000000000'


def test_get_dest_path_expanduser(monkeypatch):
    monkeypatch.setattr(
        'pathlib.Path.expanduser',
        lambda self: str(self).replace('~', '/home/test')
    )
    monkeypatch.setattr(
        'os.urandom',
        lambda self: b'\x00' * 20
    )

    dst = datasets.get_dest_path(parent='~/data/camm')
    assert str(dst) == '/home/test/data/camm', f'"{str(dst)}" should be "/home/test/data/camm"'

    key = datasets.get_key()
    dst = datasets.get_dest_path(parent='~/data/camm', key=key)
    assert str(dst) == '/home/test/data/camm/00/00000000000000000000000000000000000000'

