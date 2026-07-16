#!/usr/bin/env python
# coding: utf-8

'''
Docker container:

    username: admin
    password: 2jf70TPNZsS


'''

import argparse
import os
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
    from cammcat.models import new_dataset
    from cammcat.client import get_client

    settings = load_settings(args.config_file, os.environ, args)
    dataset = new_dataset(**settings.model_dump())
    if args.dry_run:
        print(vars(dataset))
    else:
        client = get_client(
            username=settings.username,
            password=settings.password,
            base_url=settings.base_url
        )
        dataset_id = client.datasets_create(dataset)
        print(f'{dataset_id}')
    return 0


def cli_config(args):
    # Placeholder.
    return 0


def cli_config_list(args):
    from cammcat.settings import load_config

    config = load_config(args.config_file)
    print(config.list())
    return 0


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


def cli_list(args):
    from cammcat.settings import load_settings
    from cammcat.client import get_client

    settings = load_settings(args.config_file, os.environ, args)
    client = get_client(
        username=settings.username,
        password=settings.password,
        base_url=settings.base_url
    )

    datasets = client.get_datasets()
    if not datasets:
        print('No datasets found.')
        return 0

    for dataset in datasets:
        # print(dataset)
        pid = dataset.get('pid')
        name = dataset.get('datasetName')
        print(f'{pid}  {name}')

    return 0


def cli():
    res = 0

    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', default=os.getenv(_env_camm_config_file, ''))
    parser.add_argument('--username', default=os.getenv(_env_camm_username, ''))
    parser.add_argument('--password', default=os.getenv(_env_camm_password, ''))
    parser.add_argument('--scicat-base-url', dest='base_url', default=os.getenv(_env_camm_base_url, ''))
    parser.add_argument('--dry-run', '-n', action='store_true', default=False)

    subparsers = parser.add_subparsers()

    parse_add = subparsers.add_parser('add')
    parse_add.set_defaults(func=cli_add)

    parse_config = subparsers.add_parser('config')
    parse_config.set_defaults(func=cli_config)

    parse_show = subparsers.add_parser('show')
    parse_show.set_defaults(func=cli_show)

    parse_list = subparsers.add_parser('list')
    parse_list.set_defaults(func=cli_list)

    # Add [dataset]
    # Metadata => Required
    parse_add.add_argument('--contactEmail', type=str)
    parse_add.add_argument('--creationLocation', type=str)
    parse_add.add_argument('--creationTime', type=str)
    parse_add.add_argument('--owner', type=str)
    parse_add.add_argument('--ownerGroup', type=str)
    parse_add.add_argument('--principalInvestigator', type=str)
    parse_add.add_argument('--sourceFolder', type=str)
    # Metadata => Optional
    # createdBy=createdBy,                        # Error: ... "should not exist"???
    # history=history,                            # Error: ... "should not exist"???
    # updatedBy=updatedBy,                         # Error: ... "should not exist"???
    parse_add.add_argument('--accessGroups', type=str, nargs='*')
    parse_add.add_argument('--classification', type=str)
    parse_add.add_argument('--createdAt', type=str)
    parse_add.add_argument('--dataFormat', type=str)
    parse_add.add_argument('--datasetName', type=str)
    parse_add.add_argument('--description', type=str)
    parse_add.add_argument('--endTime', type=str)
    parse_add.add_argument('--instrumentGroup', type=str)
    parse_add.add_argument('--instrumentId', type=str)
    parse_add.add_argument('--isPublished', action='store_true', default=False)
    parse_add.add_argument('--keywords', type=str, nargs='*')
    parse_add.add_argument('--license', type=str)
    parse_add.add_argument('--numberOfFiles', type=int)
    parse_add.add_argument('--numberOfFilesArchived', type=int)
    parse_add.add_argument('--orcidOfOwner', type=str)
    parse_add.add_argument('--ownerEmail', type=str)
    parse_add.add_argument('--packedSize', type=str)
    parse_add.add_argument('--pid', type=str)
    parse_add.add_argument('--proposalId', type=str)
    parse_add.add_argument('--sampleId', type=str)
    parse_add.add_argument('--scientificMetadata', type=str, help='Dictionary')
    parse_add.add_argument('--sharedWith', type=str, nargs='*')
    parse_add.add_argument('--size', type=int)
    parse_add.add_argument('--sourceFolderHost', type=str)
    parse_add.add_argument('--techniques', type=str, nargs='*', help='List of dictionaries')
    parse_add.add_argument('--type', dest='type_', type=str)
    parse_add.add_argument('--updatedAt', type=str)
    parse_add.add_argument('--validationStatus', type=str)
    parse_add.add_argument('--version', type=str)

    parse_config_subparsers = parse_config.add_subparsers()
    parse_config_list = parse_config_subparsers.add_parser('list')
    parse_config_list.set_defaults(func=cli_config_list)

    parse_show.add_argument('dataset_id', type=str, nargs='*')

    args = parser.parse_args()
    # print(args)

    res = args.func(args)

    return res


if __name__ == '__main__':
    sys.exit(cli())


# END
