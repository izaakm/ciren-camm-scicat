import hashlib
import logging
import os
import os
import shutil
import shutil
import stat
import sys

from pathlib import Path

logger = logging.getLogger(__name__)


def get_key():
    '''
    Generate a random base16 string.
    '''
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


def _set_permissions(
        target,
        owner = None,
        group = None,
    ):
    '''
    Recursively make the target read-only, keep execute, and make directories sticky.
    '''
    paths = [target]
    if target.is_dir():
        paths.extend(target.rglob('*'))

    # Process children before directories so traversal remains possible.
    for item in reversed(paths):
        # # > Changing owner generally requires root or CAP_CHOWN. Changing
        # # > group is normally allowed only to one of the caller's
        # # > supplementary groups.
        # if owner is not None or group is not None:
        #     shutil.chown(item, user=owner, group=group)

        if item.is_dir():
            # sticky+read+execute
            mode = 0o1555
        else:
            old_mode = item.stat().st_mode
            if old_mode & 0o111:  # Is any execute bit set?
                # read+execute
                mode = 0o555
            else:
                # read only
                mode = 0o444

        item.chmod(mode)


def _copy(
        src,
        dst,
        ignore = None,
        owner = None,
        group = None,
    ):
    '''
    Copy src into a new destination directory, then make it read-only.

    Parameters
    ----------
    src: str|Path
    dst: str|Path
        The path to the new directory. If src is a directory, its contents will
        be copied into dst. If src is a file, it's copied to dst/src.name.
    ignore: list[str]
        List of glob patterns to ignore.
    owner: str
        Not implemented.
    group: str
        Not implemented.
    '''
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(src)

    if dst.exists():
        raise FileExistsError(f'Destination already exists: {dst}')

    try:
        if src.is_dir():
            ignore_pat = shutil.ignore_patterns(*ignore) if ignore else None
            # symlinks=False: This is the default; the contents and metadata of the linked files are copied to the new tree.
            # ignore_dangling_symlinks=True: No error if target doesn't exist.
            shutil.copytree(
                src,
                dst,
                ignore=ignore_pat,
                symlinks=False,
                ignore_dangling_symlinks=True
            )
        else:
            # exist_ok=False protects against a concurrent creator
            dst.mkdir(parents=True, exist_ok=False)
            shutil.copy2(
                src,
                dst / src.name,
                follow_symlinks=True
            )

        _set_permissions(dst, owner=owner, group=group)
    except Exception:
        # Avoid leaving partial data behind. Temporarily restore owner-write
        # permission in case metadata application got partway.
        if dst.exists():
            for item in [dst, *dst.rglob('*')]:
                if not item.is_symlink():
                    try:
                        item.chmod(item.stat().st_mode | stat.S_IWUSR)
                    except OSError:
                        pass
            shutil.rmtree(dst, ignore_errors=True)
        raise


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



def sha256sum(filepath, chunk_size=8192):
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
            self._hash_func = sha256sum
        else:
            raise NotImplementedError(f'Hash algorithm is not implemented: {algorithm}')

    def __repr__(self):
        return self.data.__repr__()

    @property
    def _hash_name(self):
        return f'{self.algorithm}sum'

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
                f'{self._hash_name}': hash
            }

    def _to_string(self):
        '''
        Format output.
        '''
        lines = []
        for key, item in self.data.items():
            lines.append(f'{item[self._hash_name]}  {item["filepath"]}')
        return '\n'.join(lines)

    def write(self, outpath=None, set_permissions=True):
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
            if set_permissions:
                _set_permissions(outpath)

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
        hash_name = f'{algorithm}sum'
        data = {}
        with open(filepath) as f:
            for line in f.readlines():
                hash, target_path = line.strip().split(maxsplit=1)
                data[target_path] = {
                    'filepath': target_path,
                    f'{hash_name}': hash
                }
        return cls(root=os.path.dirname(filepath), algorithm=algorithm, data=data)

# END
