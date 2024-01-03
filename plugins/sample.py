"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""


def custom_plugin_method(data: dict, args: dict) -> str:
    """
    A freely named method to be called anywhere in the template and content files with {: xxx :}
    Ex: {: my_custom_plugin_event :}
    Should always return a string with HTML content to display

    - data:           the page Json data
    - args['path']:   the full page path, e.g. /index.html
    - args['env']:    the environment name, e.g. prod
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return '<strong>Hello!</strong>'


def file_content_opened(content: str or bytes, args: dict) -> str or bytes:
    """
    Update the file content when opened
    For example, convert markdown to HTML when the file has md extension

    - content:        the file content
    - args['path']:   the full page path, e.g. /index.html
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return content


def page_data_merged(data: dict, args: dict) -> dict:
    """
    Update the page json data if needed
    Add or update data with conditions

    - data:           the page Json data
    - args['path']:   the full page path, e.g. /index.html
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return data


def before_content_parsed(content: str, args: dict) -> str:
    """
    Update the template content before parsing

    - content:        the template file content
    - args['data']:   the page json data
    - args['env']:    the environment name, e.g. prod
    - args['path']:   the full page path, e.g. /index.html
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return content


def after_content_parsed(content: str, args: dict) -> str:
    """
    Update the template content after parsing

    - content:        the final parsed content
    - args['data']:   the page json data
    - args['env']:    the environment name, e.g. prod
    - args['path']:   the full page path, e.g. /index.html
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return content


def child_content_data(child: dict, args: dict) -> dict:
    """
    Update child data before parsing content

    - child:          the child json data
    - args['key']:    the block name
    - args['env']:    the environment name, e.g. prod
    - args['path']:   the full page path, e.g. /index.html
    - args['data']:   the current page data
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return child


def child_content_query_result(items: list, args: dict) -> list:
    """
    Update the query result before parsing content

    - items:          children's json data
    - args['key']:    the block name
    - args['env']:    the environment name, e.g. prod
    - args['path']:   the full page path, e.g. /index.html
    - args['data']:   the current page data
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    return items


def custom_http_response(response: tuple or None, args: dict) -> tuple or None:
    """
    Send custom response on a request

    - response:        the current response content
    - args['path']:    the requested page path, e.g. /
    - args['request']: URL query string (GET) + application/x-www-form-urlencoded (POST)
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
    if args['path'] == '/_stapy_example':
        return '{"success": true}', 'application/json'
    return response


def http_request_initialized(path: str, args: dict) -> None:
    """
    Execute a custom action when HTTP request is initialized

    - path: the current page page, e.g. /
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """


def http_request_sent(path: str, args: dict) -> None:
    """
    Execute a custom action when HTTP request was sent

    - path: the current page page, e.g. /
    - args['_stapy']: {
        file_system: StapyFileSystem, json_query: StapyJsonQuery, parser: StapyParser, generator: StapyGenerator
    }
    """
