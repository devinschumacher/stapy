"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
requirement = []
try:
    import markdown
except ModuleNotFoundError:
    requirement.append('markdown module is required [pip install markdown]')


def file_content_opened(content: str or bytes, args: dict) -> str or bytes:
    """
    For the md extension, we convert the content from Markdown to HTML with Python markdown module
    The Markdown files in the "assets" directory are ignored
    """
    if not args['path'].endswith('.md'):
        return content
    if args.get('_stapy').get('file_system').get_source_dir('assets') in args['path']:
        return content
    if requirement:
        return ', '.join(requirement)
    is_bytes = isinstance(content, bytes)
    if is_bytes:
        content = content.decode()
    content = _useless_line_break(
        markdown.markdown(content, tab_length=2, extensions=_get_md_extensions())
    )
    return content.encode() if is_bytes else content


def _useless_line_break(content: str) -> str:
    """
    Remove the useless br element added by "nl2br" extension
    """
    content = content.replace('<br /></li>', '</li>')
    content = content.replace('<br /></p>', '</p>')
    return content


def _get_md_extensions() -> list:
    """
    Markdown extensions to enable

    - fenced_code: https://python-markdown.github.io/extensions/fenced_code_blocks/
    - tables:      https://python-markdown.github.io/extensions/tables/
    - attr_list:   https://python-markdown.github.io/extensions/attr_list/
    - md_in_html:  https://python-markdown.github.io/extensions/md_in_html/
    - nl2br:       https://python-markdown.github.io/extensions/nl2br/
    """
    return ['fenced_code', 'tables', 'attr_list', 'md_in_html', 'nl2br']
