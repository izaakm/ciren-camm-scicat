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
def _sha256sum(filepath, chunk_size=8192):
    hash_obj = hashlib.sha256()

    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


class Checksums:
    '''
    Calculate checksums. Store them. Write them to disk to match `sha256sum` format. Verify them.

    Examples
    --------

    >>> os.chdir('srcdir')
    >>> sha256sum = Checksums()
    >>> sha256sum.hash_files(glob('srcdir/**'))
    >>> # copy files
    >>> os.chdir('dstdir')
    >>> sha256sum.verify()
    >>> sha256sum.write('dstdir.sha256')
    '''
    def __init__(self, root='.', algorithm='sha256', data=None):
        self.root = Path(root)
        self.algorithm = algorithm

        # Use dict to ensure one hash per filepath.
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = {}

        if self.algorithm == 'sha256':
            self._hash_func = _sha256sum
        else:
            raise NotImplementedError(f'Hash algorithm is not implemented: {algorithm}')

    def __repr__(self):
        return self.data.__repr__()

    def hash_files(self, files, chunk_size=8192):
        '''
        Compute hash values for the given files. Results are stored in the
        `data` attribute. Filepaths are stored relative to the path given by
        the `root` attribute.

        Parameters
        ----------
        files: list
            List of filepaths. Directories will be ignored.
        chunk_size: int

        Returns
        -------
        None
        '''
        # When storing the checksums, the path to the file should be relative
        # to self.root; this makes it easy to verify checksums after copying
        # files to a new directory.
        for filepath in files:
            # For convenience, avoid directories rather than raising an error
            # so that the user can just pass 'dirname.rglob('*')'.
            if filepath.is_dir():
                continue
            relpath = filepath.relative_to(self.root)
            # print(relpath)
            hash = self._hash_func(filepath)
            self.data[f'{relpath}'] = {
                'filepath': relpath,
                f'{self.algorithm}sum': hash,
                'message': f'{hash}  {relpath}'
            }

    def _to_string(self):
        '''
        Format output.
        '''
        return '\n'.join([item['message'] for item in self.data.values()])

    def write(self, outpath=None):
        '''
        Write checksums to file.

        Parameters
        ----------
        outpath: str,Path,None
            Path to output file. If None, write to stdout.

        Returns
        -------
        None
        '''
        if outpath is None:
            print(self._to_string())
        else:
            with open(outpath, 'w') as f:
                print(self._to_string(), file=f)

    def verify(self, root=None, chunk_size=8192):
        '''
        You want to be able to verify checksums after copying the files, so the
        "files" (paths) need to be relative, e.g.:

            cd srcdir
            checksums ....
            cp srcdir/ dstdir/
            cd dstdir
            verify

        Parameters
        ----------
        root: str|Path
            Filepaths are relative to root. By default, use `self.root="."`
        chunck_size: int

        Returns
        -------
        int
            0: success (all checksums matched)
            1: error(s) (one or more checksums did not match)
        '''
        res = 0
        root = root or self.root
        for key, item in self.data.items():
            relpath = item['filepath']
            filepath = self.root / relpath
            try:
                hash = self._hash_func(filepath)
                if hash == item[f'{self.algorithm}sum']:
                    print(f'{relpath}: OK')
                else:
                    res = 1
                    print(f'{relpath}: FAILED')
            except FileNotFoundError:
                res = 1
                print(f'{relpath}: No such file or directory')
            except IsADirectoryError:
                res = 1
                print(f'{relpath}: Is a directory')
        return res

    @classmethod
    def read(cls, filepath, algorithm='sha256'):
        '''
        Read checkusms from file.

        Returns
        -------
        Checksums
        '''
        data = {}
        with open(filepath) as f:
            for line in f.readlines():
                hash, target_path = line.strip().split(maxsplit=1)
                data[target_path] = {
                    'filepath': target_path,
                    f'{algorithm}sum': hash,
                    'message': line.strip()
                }
        return cls(root=os.path.dirname(filepath), algorithm=algorithm, data=data)


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
