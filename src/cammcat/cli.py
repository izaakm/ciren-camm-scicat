#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import time
import sys

from cammcat.settings import (
    _env_camm_config_file,
    _env_camm_username,
    _env_camm_password,
    _env_camm_base_url
)


# ========================================================================
# CLI
# ========================================================================
def cli_add(args):
    from cammcat.settings import load_settings
    from cammcat.models import new_dataset, get_data_block
    from cammcat.client import get_client
    from pyscicat.client import ScicatCommError

    settings = load_settings(args.config_file, os.environ, args)
    dataset = new_dataset(**settings.model_dump())
    data_block = get_data_block(**settings.model_dump())
    if args.dry_run:
        print(dataset.model_dump_json(indent=2))
        print(data_block.model_dump_json(indent=2))
    else:
        client = get_client(
            username=settings.username,
            password=settings.password,
            base_url=settings.base_url
        )
        dataset_id = client.datasets_create(dataset)
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
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )
    for pid in args.dataset_id:
        dataset = client.get_dataset_by_pid(pid)
        print(json.dumps(dataset, indent=2))
        data_blocks = client.get_dataset_origdatablocks(pid)
        print(json.dumps(data_blocks, indent=2))


def cli_list(args):
    from cammcat.settings import load_settings
    from cammcat.client import get_client
    from cammcat.models import ListOfDatasets

    settings = load_settings(args.config_file, os.environ, args)
    client = get_client(
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )

    # datasets = client.get_datasets()
    datasets = ListOfDatasets(client.get_datasets())
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


def cli_update(args):
    raise NotImplementedError


def add_dataset_args(parser):
    # Add [dataset]
    # Metadata => Required
    parser.add_argument('--contactEmail', type=str)
    parser.add_argument('--creationLocation', type=str)
    parser.add_argument('--creationTime', type=str)
    parser.add_argument('--owner', type=str)
    parser.add_argument('--ownerGroup', type=str)
    parser.add_argument('--principalInvestigator', type=str)
    parser.add_argument('--sourceFolder', type=str)
    # Metadata => Optional
    # createdBy=createdBy,                        # Error: ... "should not exist"???
    # history=history,                            # Error: ... "should not exist"???
    # updatedBy=updatedBy,                         # Error: ... "should not exist"???
    parser.add_argument('--accessGroups', type=str, nargs='*')
    parser.add_argument('--classification', type=str)
    parser.add_argument('--createdAt', type=str)
    parser.add_argument('--dataFormat', type=str)
    parser.add_argument('--datasetName', type=str)
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
    parser.add_argument('--config-file', default=os.getenv(_env_camm_config_file, ''))
    parser.add_argument('--username', default=os.getenv(_env_camm_username, ''))
    parser.add_argument('--password', default=os.getenv(_env_camm_password, ''))
    parser.add_argument('--scicat-base-url', dest='base_url', default=os.getenv(_env_camm_base_url, ''))
    parser.add_argument('--dry-run', '-n', action='store_true', default=False)

    subparsers = parser.add_subparsers()

    parse_help = subparsers.add_parser('help')
    parse_help.set_defaults(func=cli_help)

    parse_add = subparsers.add_parser('add')
    parse_add.set_defaults(func=cli_add)

    parse_config = subparsers.add_parser('config')
    parse_config.set_defaults(func=cli_config)

    parse_show = subparsers.add_parser('show')
    parse_show.set_defaults(func=cli_show)

    parse_list = subparsers.add_parser('list')
    parse_list.set_defaults(func=cli_list)

    parse_list_files = subparsers.add_parser('list-files')
    parse_list_files.set_defaults(func=cli_list_files)

    parse_update = subparsers.add_parser('update')
    parse_update.set_defaults(func=cli_update)

    # Add [dataset]
    parse_add = add_dataset_args(parse_add)
    # Others
    parse_add.add_argument('--chkAlg', type=str)

    parse_config_subparsers = parse_config.add_subparsers()
    parse_config_list = parse_config_subparsers.add_parser('list')
    parse_config_list.set_defaults(func=cli_config_list)

    parse_help.add_argument(
        'topic',
        nargs='?',
        choices=['format', 'settings']
    )

    parse_list.add_argument(
        '--fields', '--format', '-f',
        help='Comma separated list of fields (not case sensitive).',
        type=str,
        default='pid,datasetName'
    )
    parse_list.add_argument('--sep', type=str, default='\t')
    parse_list.add_argument('--parsable', '-p', dest='sep', action='store_const', const='|')

    parse_list_files.add_argument(
        'dataset_id',
        help='List the files associated with the dataset PID(s). If no PID is given, list all files for all datasets.',
        type=str,
        nargs='*'
    )

    parse_show.add_argument('dataset_id', type=str, nargs='*')
    parse_show.add_argument('--data-blocks', help='Also show the files for the dataset.', action='store_true')

    parse_update = add_dataset_args(parse_update)

    args = parser.parse_args()
    # print(args)

    res = args.func(args)

    return res


if __name__ == '__main__':
    sys.exit(cli())


# END
