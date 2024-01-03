"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
import os
from datetime import datetime

token = datetime.now().strftime('%Y%d%m%H%M%S%f')


def get_token() -> str:
    """
    Returns a token generated when loading the plugin.
    Useful for getting a unique token for all pages when building.
    """
    return token


def get_asset_token(data: dict, args: dict) -> str:
    """
    Returns a token for an asset file, based on the last update date.
    Used to force client to reload the asset file when the token is used as a query param.
    """
    file = args.get('file', False)
    if not file:
        raise ValueError('[get_asset_token] File argument is required')
    path = args.get('_stapy').get('file_system').get_source_dir('assets') + os.sep + args.get('file').lstrip('/')
    if not os.path.exists(path):
        raise FileNotFoundError('[get_asset_token] File does not exist: ' + path)
    return str(os.path.getmtime(path)).replace('.', '')
