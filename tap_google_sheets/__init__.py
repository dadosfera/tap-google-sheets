#!/usr/bin/env python3

import sys
import json
import argparse
import singer
from singer import metadata, utils
from tap_google_sheets.client import GoogleClient
from tap_google_sheets.discover import discover
from tap_google_sheets.sync import sync

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS_OAUTH = [
    'client_id',
    'client_secret',
    'refresh_token',
    'spreadsheet_id',
    'start_date',
    'user_agent'
]

REQUIRED_CONFIG_KEYS_SERVICE_ACCOUNT = [
    'spreadsheet_id',
    'start_date',
    'user_agent'
]

def _build_client(config):
    credentials_type = config.get('credentials_type', 'oauth')
    request_timeout = config.get('request_timeout')
    user_agent = config['user_agent']

    if credentials_type == 'service_account':
        return GoogleClient.from_service_account(
            service_account_info=config['client_secrets'],
            request_timeout=request_timeout,
            user_agent=user_agent,
        )

    return GoogleClient.from_oauth(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        refresh_token=config['refresh_token'],
        request_timeout=request_timeout,
        user_agent=user_agent,
    )

def do_discover(client, spreadsheet_id):

    LOGGER.info('Starting discover')
    catalog = discover(client, spreadsheet_id)
    json.dump(catalog.to_dict(), sys.stdout, indent=2)
    LOGGER.info('Finished discover')


@singer.utils.handle_top_exception(LOGGER)
def main():

    config = singer.utils.parse_args([]).config
    credentials_type = config.get('credentials_type', 'oauth')

    if credentials_type == 'service_account':
        required_keys = REQUIRED_CONFIG_KEYS_SERVICE_ACCOUNT + ['client_secrets']
    else:
        required_keys = REQUIRED_CONFIG_KEYS_OAUTH

    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise Exception('Config is missing required keys: {}'.format(missing_keys))

    parsed_args = singer.utils.parse_args([])

    with _build_client(config) as client:

        state = {}
        if parsed_args.state:
            state = parsed_args.state

        config = parsed_args.config
        spreadsheet_id = config.get('spreadsheet_id')

        if parsed_args.discover:
            do_discover(client, spreadsheet_id)
        elif parsed_args.catalog:
            sync(client=client,
                 config=config,
                 catalog=parsed_args.catalog,
                 state=state)

if __name__ == '__main__':
    main()
