"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
from datetime import datetime


def page_data_merged(data: dict) -> dict:
    """
    We add date formats to page data
    """
    if 'date' not in data:
        return data
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        data['date_full'] = date.strftime('%B %d, %Y')
        data['date_rfc_3339'] = date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4] + 'Z'
        data['date_rfc_822'] = date.strftime('%a, %d %b %Y %H:%M:%S GMT')
    except ValueError:
        data['date_full'] = data['date']
    return data


def now(data: dict, args: dict) -> str:
    """
    Retrieve current date in specified format
    """
    if 'format' not in args:
        args['format'] = '%B %d, %Y at %H:%M'
    return datetime.now().strftime(args['format'])
