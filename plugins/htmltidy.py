"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
import re


def after_content_parsed(content: str, args: dict) -> str:
    """
    For a file with the html extension, we remove useless white spaces at the beginning of each line,
    except for pre and textarea
    """
    if not args['path'].endswith('.html'):
        return content
    cleaned = ''
    is_preformatted = False
    for line in content.split('\n'):
        if not is_preformatted and (
                re.search(r'<(pre|textarea)(.*)>', line, flags=re.IGNORECASE) or re.search(r'<!--', line)):
            is_preformatted = True
        if re.search(r'</(pre|textarea)>', line, flags=re.IGNORECASE) or re.search(r'-->', line):
            is_preformatted = False
        if not is_preformatted and not line.strip():
            continue
        cleaned += (line if is_preformatted else line.strip()) + '\n'
    return cleaned
