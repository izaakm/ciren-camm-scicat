#!/usr/bin/env python
# coding: utf-8

import argparse
import logging
import os
import pathlib
import time
import sys

from cammcat.settings import (
    _env_camm_config_file,
    _env_camm_token,
    _env_camm_username,
    _env_camm_password,
    _env_camm_base_url,
    _env_camm_repo
)


logger = logging.getLogger(__name__)

# ========================================================================
# CLI
# ========================================================================
def cli_add_dataset_to_repository(args):
    '''
    Add dataset to the CAMM repository. The default is to copy the entire
    contents of given source directory (or file).
    '''
    import os

    from cammcat.settings import load_settings
    from cammcat.models import new_dataset, get_data_block
    from cammcat.client import get_client
    from cammcat import utils
    from pyscicat.client import ScicatCommError

    settings = load_settings(args.config_file, os.environ, args)
    logger.debug(settings)

    key = utils.get_key()
    logger.debug(key)

    if args.sourceFolder:
        if args.sourceFolder.is_dir():
            # --sourceFolder /path/to/dirname
            # dest:          $CAMM_REPO/dirname
            # checksums:     $CAMM_REPO/checksums.sha256
            source = args.sourceFolder
            source_name = args.sourceFolder.name
            # For checksums
            root = args.sourceFolder.parent
            files = args.sourceFolder.rglob('*')
        else:
            sys.tracebacklimit = 0
            raise ValueError(f'--sourceFolder is not a directory or does not exist: {args.sourceFolder}')
    elif args.sourceFile:
        if args.sourceFile.is_file():
            # The final path for a *file* is differnt:
            # --sourceFile /path/to/filename.csv
            # dest:        $CAMM_REPO/filename/filename.csv
            # checksums:   $CAMM_REPO/checksums.sha256
            source = args.sourceFile
            source_name = args.sourceFile.stem
            # For checksums
            root = args.sourceFile.parent
            files = [args.sourceFile]
        else:
            sys.tracebacklimit = 0
            raise ValueError(f'--soureFile is not a file or does not exist: {args.sourceFile}')
    else:
        sys.tracebacklimit = 0
        raise ValueError(
            'You must provide either --sourceFolder or --sourceFile; you gave:\n'
            f'--sourceFolder={args.sourceFolder}\n'
            f'--sourceFile={args.sourceFile}'
        )

    if not settings.camm_repo:
        sys.tracebacklimit = 0
        raise ValueError(f'--camm-repository is required.')

    if not os.path.isdir(settings.camm_repo):
        raise FileNotFoundError(f'CAMM Repo does not exist: "{settings.camm_repo}"')

    if args.checksums or args.verify_checksums:
        # Get checksums before copying data
        checksums = utils.Checksums(root=root, algorithm=args.chkAlg)
        checksums.hash_files(files)
        # print(checksums.root)
        # print(vars(checksums))
        # checksums.write()

    # name = args.datasetName or source_name
    name = source_name
    dest = utils.get_dest_path(
        parent=settings.camm_repo,
        key=key,
        name=name
    )
    utils.copy_dataset(
        source,
        dest,
        ignore=None,
        dry_run=args.dry_run
    )

    if args.checksums or args.verify_checksums:
        # Write the checksums next to the destination directory:
        #     repo/toy
        #     repo/toy.checksums
        checksums.root = dest.parent

        if args.sourceFile:
            # Update the filename in the repo to include the additional parent directory.
            checksums.data[f'{args.sourceFile.name}']['filepath'] = pathlib.Path(f'{name}/{args.sourceFile.name}')
        # print(vars(checksums))
        checksums.write(outpath=checksums.root/'checksums.sha256')

    if args.verify_checksums:
        # Optional, also validate checksums after copying data
        checksums.verify()

    logger.info('Added %s' % dest)
    return 0

def cli_attach_datafiles_to_dataset(args):
    raise NotImplementedError('Attach command not implemented yet.')


def cli_create(args):
    '''
    Create a new metadata record for a dataset.
    '''
    from cammcat.settings import load_settings
    from cammcat.models import new_dataset, get_data_block
    from cammcat.client import get_client
    from pyscicat.client import ScicatCommError

    settings = load_settings(args.config_file, os.environ, args)

    # [TODO] Each 'kind' of dataset could have it's own 'new_dataset' function
    # to automatically extract metadata.
    kwargs = { **settings.model_dump() }
    if kwargs.get('camm_repo'):
        kwargs['relative_to'] = kwargs['camm_repo']
    if args.datasetName == '.':
        kwargs['datasetName'] = os.path.basename(settings.sourceFolder)
    dataset = new_dataset(**kwargs)

    kwargs = { **settings.model_dump() }
    if kwargs.get('camm_repo'):
        kwargs['relative_to'] = kwargs['camm_repo']
    data_block = get_data_block(**kwargs)

    if args.metadata_file:
        dataset.update_metadata_from_file(
            args.metadata_file
        )

    if args.dry_run:
        print(dataset.model_dump_json(indent=2))
        print(data_block.model_dump_json(indent=2))
    else:
        logger.debug('Creating client...')
        client = get_client(
            token=settings.token,
            username=settings.username,
            password=settings.password,
            base_url=settings.base_url
        )

        logger.debug('Adding dataset...')
        # # Old, official pyscicat API
        # dataset_id = client.datasets_create(dataset)
        # New client API, return the dataset, not just the pid
        dataset = client.datasets_create(dataset)
        dataset_id = dataset['pid']

        logger.debug('Verifiying...')
        success = False
        for i in range(3):
            try:
                res = client.get_dataset_by_pid(dataset_id)
                success = True
                break
            except ScicatCommError:
                time.sleep(i**2)
                continue
        if not success:
            raise ScicatCommError('Error, cannot confirm dataset created.')
        # Adding the `data_block` (below) wasn't working for awhile. Does it
        # need to sleep (added above)? I was initially calling it without
        # capturing the output ... add `res =` and it started working ...
        # doesn't seem like that would make a difference, what else did I
        # change?
        logger.debug('Adding data blocks...')
        res = client.datasets_origdatablock_create(
            dataset_id,
            data_block
        )
        print(f'{dataset_id}')
        # print(res)
    return 0


def cli_config(args):
    # Placeholder.
    return 0


def cli_config_list(args):
    from cammcat.settings import load_config

    if not args.config_file:
        print('Config file is not set.')
        return 1
    config = load_config(args.config_file)
    print(config.list())
    return 0


def cli_help(args):
    from cammcat.settings import list_of_settings, load_settings
    if args.topic == 'settings':
        settings = load_settings(args.config_file, os.environ, args)
        print(settings)
    elif args.topic == 'format':
        print(*list_of_settings, sep='\n')


def cli_show(args):
    '''
    What do they want to do with the data when they get an object out of the CLI?
    '''
    import json
    from cammcat.settings import load_settings
    from cammcat.client import get_client

    settings = load_settings(args.config_file, os.environ, args)
    client = get_client(
        token=settings.token,
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )
    for pid in args.dataset_id:
        dataset = client.get_dataset_by_pid(pid)
        print(json.dumps(dataset, indent=2))
        data_blocks = client.get_dataset_origdatablocks(pid)
        print(json.dumps(data_blocks, indent=2))


def cli_login(args):
    from cammcat.settings import load_settings
    from cammcat.client import get_client
    from cammcat.models import ListOfDatasets

    settings = load_settings(args.config_file, os.environ, args)
    logger.debug(settings)

    client = get_client(
        token=settings.token,
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )
    client.login()


def cli_list(args):
    from cammcat.settings import load_settings
    from cammcat.client import get_client
    from cammcat.models import ListOfDatasets

    settings = load_settings(args.config_file, os.environ, args)
    logger.debug(settings)

    client = get_client(
        token=settings.token,
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )

    datasets = ListOfDatasets(client.get_datasets())
    logger.debug(f'type(datasets) => {type(datasets)}')
    logger.debug(datasets)
    if not datasets:
        print('No datasets found.')
        return 0

    fields = args.fields.split(',')
    fields, lines = datasets.list(fields=fields)
    print(*fields, sep=args.sep)
    for line in lines:
        print(*line, sep=args.sep)

    return 0


def cli_list_files(args):
    import json
    from cammcat.settings import load_settings
    from cammcat.client import get_client

    settings = load_settings(args.config_file, os.environ, args)
    client = get_client(
        token=settings.token,
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )
    linefmt = '{pid:<16} {uid:>4} {gid:>4} {size:>12} {mtime:<24} {filepath}'
    headerfmt = linefmt.replace('>', '<')
    print(headerfmt.format(pid='PID', uid='UID', gid='GID', size='Size', mtime='mTime', filepath='Filepath'))
    for pid in args.dataset_id:
        # dataset = client.get_dataset_by_pid(pid)
        # print(json.dumps(dataset, indent=2))
        data_blocks = client.get_dataset_origdatablocks(pid)
        # print(json.dumps(data_blocks, indent=2))
        for block in data_blocks:
            for item in block['dataFileList']:
                uid = item['uid']
                gid = item['gid']
                size = item['size']
                mtime = item['time']
                filepath = item['path']
                # print(pid, uid, gid, size, mtime, filepath)
                print(linefmt.format(pid=pid, uid=uid, gid=gid, size=size, mtime=mtime, filepath=filepath))


def cli_model(args):
    import json
    from cammcat.models import CAMMDataset

    if args.dump_schema:
        schema = CAMMDataset.model_json_schema(union_format="primitive_type_array")
        print(json.dumps(schema, indent=2))


def cli_update(args):
    raise NotImplementedError


def parse_log_level(value, default=logging.WARNING):
    if value.casefold().startswith('d'):
        return logging.DEBUG
    elif value.casefold().startswith('i'):
        return logging.INFO
    elif value.casefold().startswith('w'):
        return logging.WARNING
    elif value.casefold().startswith('e'):
        return logging.ERROR
    elif value.casefold().startswith('c'):
        return logging.CRITICAL
    else:
        return default


def _add_dataset_args(parser):
    # Add [dataset]
    # Metadata => Required
    parser.add_argument('--contactEmail', type=str)
    parser.add_argument('--creationLocation', type=str)
    parser.add_argument('--creationTime', type=str)
    parser.add_argument('--owner', type=str)
    parser.add_argument('--ownerGroup', type=str)
    parser.add_argument('--principalInvestigator', type=str)
    parser.add_argument(
        '--sourceFolder',
        type=str,
        required=True
    )
    # Metadata => Optional
    # createdBy=createdBy,                        # Error: ... "should not exist"???
    # history=history,                            # Error: ... "should not exist"???
    # updatedBy=updatedBy,                         # Error: ... "should not exist"???
    parser.add_argument('--accessGroups', type=str, nargs='*')
    parser.add_argument('--classification', type=str)
    parser.add_argument('--createdAt', type=str)
    parser.add_argument('--dataFormat', type=str)
    parser.add_argument(
        '--datasetName',
        help='Name of dataset as it appears in the metadata (human readable). If ".", use the basename of the --sourceFolder.',
        type=str,
        required=True
    )
    parser.add_argument('--description', type=str)
    parser.add_argument('--endTime', type=str)
    parser.add_argument('--instrumentGroup', type=str)
    parser.add_argument('--instrumentId', type=str)
    parser.add_argument('--isPublished', action='store_true', default=False)
    parser.add_argument('--keywords', type=str, nargs='*')
    parser.add_argument('--license', type=str)
    parser.add_argument('--numberOfFiles', type=int)
    parser.add_argument('--numberOfFilesArchived', type=int)
    parser.add_argument('--orcidOfOwner', type=str)
    parser.add_argument('--ownerEmail', type=str)
    parser.add_argument('--packedSize', type=str)
    parser.add_argument('--pid', type=str)
    parser.add_argument('--proposalId', type=str)
    parser.add_argument('--sampleId', type=str)
    parser.add_argument('--scientificMetadata', type=str, help='Dictionary')
    parser.add_argument('--sharedWith', type=str, nargs='*')
    parser.add_argument('--size', type=int)
    parser.add_argument('--sourceFolderHost', type=str)
    parser.add_argument('--techniques', type=str, nargs='*', help='List of dictionaries')
    parser.add_argument('--type', dest='type_', type=str)
    parser.add_argument('--updatedAt', type=str)
    parser.add_argument('--validationStatus', type=str)
    parser.add_argument('--version', type=str)
    return parser


def cli():
    res = 0

    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', default=logging.WARNING, type=parse_log_level)
    parser.add_argument('--config-file', default=os.getenv(_env_camm_config_file, ''))
    parser.add_argument('--scicat-base-url', dest='base_url', default=os.getenv(_env_camm_base_url, ''))
    parser.add_argument('--dry-run', '-n', action='store_true', default=False)

    # ========================================================================
    # Init Subparsers
    # ========================================================================
    subparsers = parser.add_subparsers()

    parse_help = subparsers.add_parser('help')
    parse_help.set_defaults(func=cli_help)

    parse_add = subparsers.add_parser(
        'add',
        help='Add (copy) dataset to CAMM data repository.',
        description=cli_add_dataset_to_repository.__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_add.set_defaults(func=cli_add_dataset_to_repository)

    parse_attach_datafiles = subparsers.add_parser(
        'attach',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_attach_datafiles.set_defaults(func=cli_attach_datafiles_to_dataset)

    parse_create = subparsers.add_parser('create')
    parse_create.set_defaults(func=cli_create)

    parse_config = subparsers.add_parser('config')
    parse_config.set_defaults(func=cli_config)

    parse_model = subparsers.add_parser('model')
    parse_model.set_defaults(func=cli_model)

    parse_show = subparsers.add_parser('show')
    parse_show.set_defaults(func=cli_show)

    parse_login = subparsers.add_parser('login')
    parse_login.set_defaults(func=cli_login)

    parse_list = subparsers.add_parser('list')
    parse_list.set_defaults(func=cli_list)

    parse_list_files = subparsers.add_parser('list-files')
    parse_list_files.set_defaults(func=cli_list_files)

    parse_update = subparsers.add_parser('update')
    parse_update.set_defaults(func=cli_update)

    # ========================================================================
    # Create a new dataset in the SciCat metadata database.
    # ========================================================================
    parse_create = _add_dataset_args(parse_create)
    parse_create.add_argument(
        '--chkAlg',
        help='Calculate checksums using given algorithm.',
        choices=['sha256']
    )
    parse_create.add_argument(
        '--camm-repository',
        dest='camm_repo',
        help="Destination directory for the data.",
        type=pathlib.Path,
        default=os.getenv(_env_camm_repo)
    )
    parse_create.add_argument(
        '--get-metadata-from-file',
        dest='metadata_file',
        help='Path to file. Extract metadata from this file and add it to the dataset.',
        type=pathlib.Path
    )

    # ========================================================================
    # Config
    # ========================================================================
    parse_config_subparsers = parse_config.add_subparsers()
    parse_config_list = parse_config_subparsers.add_parser('list')
    parse_config_list.set_defaults(func=cli_config_list)

    # ========================================================================
    # Help
    # ========================================================================
    parse_help.add_argument(
        'topic',
        nargs='?',
        help='format: for use with "list [--fields|--format]; settings: show settings and their values.',
        choices=['format', 'settings']
    )

    # ========================================================================
    # Add dataset to respository
    # [TODO] Optional: Instead of copying the 'sourceFolder', tar everything up
    # so the repository has only tar files. Or possibly hdf5 files???
    # ========================================================================
    parse_add_source_file_or_folder = parse_add.add_mutually_exclusive_group(required=True)
    parse_add_source_file_or_folder.add_argument(
        '--sourceFolder',
        help='Path to directory. Copy the directory and all of its contents into the data repository.',
        type=pathlib.Path
    )
    parse_add_source_file_or_folder.add_argument(
        '--sourceFile',
        help='Path to file. Copy the given file into the data repository.',
        type=pathlib.Path,
    )
    parse_add.add_argument(
        '--camm-repository',
        dest='camm_repo',
        help="Destination directory for the data.",
        type=pathlib.Path,
        default=os.getenv(_env_camm_repo)
    )
    parse_add.add_argument(
        '--chkAlg',
        help='Use this checksum algorithm.',
        choices=['sha256'],
        default='sha256'
    )
    parse_add.add_argument(
        '--checksums', '-c',
        help='Calculate checksums from original data files using given algorithm.',
        action='store_true',
    )
    parse_add.add_argument(
        '--verify-checksums',
        help='Verify checksums after the data is copied. This also sets "--checksums".',
        action='store_true'
    )
    parse_add.add_argument(
        '--datasetName',
        help='Name of dataset. Used as the name of the destination directory',
        type=str
    )

    # ========================================================================
    # List datasets
    # ========================================================================
    parse_list.add_argument(
        '--fields', '--format', '-f',
        help='Comma separated list of fields (not case sensitive).',
        type=str,
        default='pid,datasetName'
    )
    parse_list.add_argument('--sep', type=str, default='\t')
    parse_list.add_argument('--parsable', '-p', dest='sep', action='store_const', const='|')

    # ========================================================================
    # List files
    # ========================================================================
    parse_list_files.add_argument(
        'dataset_id',
        help='List the files associated with the dataset PID(s). If no PID is given, list all files for all datasets.',
        type=str,
        nargs='*'
    )


    # ========================================================================
    # Model
    # ========================================================================
    parse_model.add_argument('--dump-schema', action='store_true')

    # ========================================================================
    # Show dataset
    # ========================================================================
    parse_show.add_argument('dataset_id', type=str, nargs='*')
    parse_show.add_argument('--data-blocks', help='Also show the files for the dataset.', action='store_true')

    # ========================================================================
    # Update dataset
    # ========================================================================
    parse_update = _add_dataset_args(parse_update)

    # ========================================================================
    # Parse args
    # ========================================================================
    args = parser.parse_args()
    # print(args)

    logging.basicConfig(level=args.log_level)

    res = args.func(args)

    return res


if __name__ == '__main__':
    sys.exit(cli())


# END
