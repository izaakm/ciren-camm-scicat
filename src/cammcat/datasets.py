import os
import shutil
import logging

from pathlib import Path
from cammcat.models import CAMMDataset

logger = logging.getLogger(__name__)

def get_key():
    # 20 bytes => 40 hex characters
    return os.urandom(20).hex()


def get_dest_path(parent=None, key=None, name=None):
    path = Path()
    if parent:
        path /= parent
    if key:
        path /= f'{key[:2]}/{key[2:]}'
    if name:
        path /= name
    return path.expanduser()


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
        print(f'[DRY_RUN] Would copy: "{src}" -> "{dst}"')
    else:
        if ignore:
            ignore = shutil.ignore_patterns(*ignore)

        shutil.copytree(
            src, 
            dst,
            ignore=ignore
        )

    logger.info(f"Directory copied successfully")
    return dst

