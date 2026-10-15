import hashlib
import logging
import os
import shutil
import sys

from pathlib import Path
from typing import Union, List

# from cammcat.models import CAMMDataset


logger = logging.getLogger(__name__)


def get_key():
    # 20 bytes => 40 hex characters
    return os.urandom(20).hex()


def get_dest_path(parent='.', key=None, name=None):
    '''
    Parameters
    ----------
    parent: pathlib.Path|str
        Default: current working directory.
    key: str
    name: str

    Returns
    -------
    pathlib.Path
        Returns a git-like path for the directory `name`:
        '{parent}/{key[:2]}/{key[2:]}/{name}'
    '''
    path = Path(parent)
    if key:
        path /= f'{key[:2]}/{key[2:]}'
    if name:
        path /= name
    return path.expanduser()


def _copy(src, dst, ignore=None):
    if os.path.exists(dst) and not os.path.isdir(dst):
        raise NotADirectoryError(f'The destination is not a directory: {dst}')

    if os.path.isdir(src):
        # Copy directory and its contents.
        # copytree: "All intermediate directories needed to contain dst will also be created by default."
        if ignore:
            ignore = shutil.ignore_patterns(*ignore)
        shutil.copytree(
            src,
            dst,
            ignore=ignore
        )
    else:
        # Copy file.
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(
            src,
            dst
        )

    logger.info(f"Directory copied successfully")

    return None


def _copy_dry_run(src, dst, *args, **kwargs):
    print(f'[DRY_RUN] Would copy: "{src}" -> "{dst}"')
    return None


def copy_dataset(src, dst, ignore=None, dry_run=False):
    '''
    Copy src directory to dst

    Parameters
    ----------
    src: pathlib.Path
    dst: pathlib.Path
    ignore: list
        Patterns to ignore. See https://docs.python.org/3/library/shutil.html#shutil.ignore_patterns

    Returns
    -------
    pathlib.Path
        Returns destination path on success
    '''
    if dry_run:
        _copy_dry_run(src, dst)
    else:
        _copy(src, dst, ignore=ignore)

    return dst


# [TODO] Switch checksums to a class.
class Checksums:
    '''
    Calculate checksums. Store them. Write them to disk to match `sha256sum` format. Verify them.

    Examples
    --------

    >>> os.chdir('srcdir')
    >>> sha256sum = Checksums()
    >>> sha256sum.calc(glob('srcdir/**'))
    >>> # copy files
    >>> os.chdir('dstdir')
    >>> sha256sum.verify()
    >>> sha256sum.write('dstdir.sha256')
    '''
    def __init__(self, algorithm='sha256'):
        self.algorithm = algorithm
        self.data = {}

    def calc(self, files, chunk_size=8192):
        pass

    def write(self, outpath):
        pass

    def verify(self, chunk_size=8192):
        '''
        You want to be able to verify checksums after copying the files, so the
        "files" (paths) need to be relative, e.g.:

            cd srcdir
            checksums ....
            cp srcdir/ dstdir/
            cd dstdir
            verify
        '''
        pass


def sha256sum(files, chunk_size=8192):
    '''
    Mimic the sha256sum command.
    
    Parameters
    ----------
    files: str|list[str]
        Single file path (str/Path) or list of file paths
    chunk_size: int
        Bytes to read at a time (default 8192)
    
    Returns
    -------
    list[dict[str,[str|path]]]
        Each item is

            {
                'filepath': str|Path,
                'sha256sum': str,
                'message': str,
                'error': bool
            }

        where `str` matches what `sha256sum` would print. Note that errors are
        coerced to informative statements and returned as the `str` in the
        tuple.

    Examples
    --------

    >>> sha256sum('file.txt')
    >>> sha256sum(['file1.txt', 'file2.txt'])
    '''
    if isinstance(files, (str, Path)):
        files = [files]
    
    data = []
    for filepath in files:
        try:
            hash_obj = hashlib.sha256()
            
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_obj.update(chunk)
            
            data.append(
                {
                    'filepath': filepath,
                    'sha256sum': hash_obj.hexdigest(),
                    'message': f'{hash_obj.hexdigest()}  {filepath}'
                }
            )
        
        except FileNotFoundError:
            data.append(
                {
                    'filepath': filepath,
                    'message': f'sha256sum: {filepath}: No such file or directory',
                    'error': True
                }
            )
        except IsADirectoryError:
            data.append(
                {
                    'filepath': filepath,
                    'message': f'sha256sum: {filepath}: Is a directory',
                    'error': True
                }
            )
        except Exception as e:
            data.append(
                {
                    'filepath': filepath,
                    'message': f'sha256sum: {filepath}: {e}',
                    'error': True
                }
            )

    return data

