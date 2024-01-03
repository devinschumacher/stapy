"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""


def http_request_initialized(path: str, args: dict) -> None:
    """
    We automatically clear the page cache data on page load.
    This allows to see changes in JSON query blocks when page data is updated.
    For a site with several hundred pages, this could be optional.
    For manually clear the cache, restart the server or go to http://127.0.0.1:1985/_cache/clear
    """
    args.get('_stapy').get('file_system').reset_pages_data()
