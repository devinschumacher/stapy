"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
import re


def file_content_opened(content: str or bytes, args: dict) -> str or bytes:
    """
    If the file is a css, we minify it by removing all unnecessary characters
    """
    if args['path'].endswith('.css'):
        return _minify(content)
    return content


def _minify(content: str or bytes) -> bytes:
    """
    Minify a CSS file by removing unnecessary characters
    """
    rules = ((r'\/\*.*?\*\/', ''), (r'\n', ''), (r'[\t ]+', ' '), (r'\s?([;:{},+>])\s?', r'\1'), (r';}', '}'))
    is_bytes = isinstance(content, bytes)
    if is_bytes:
        content = content.decode()
    content = content.replace('\r\n', '\n')
    for rule in rules:
        content = re.compile(rule[0], re.MULTILINE | re.UNICODE | re.DOTALL).sub(rule[1], content)
    return content.encode() if is_bytes else content
