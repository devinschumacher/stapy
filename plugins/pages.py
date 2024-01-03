"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""


def page_navigation(data: dict, args: dict) -> str:
    """
    When we receive "page.previous" or "page.next" in args, we return the page navigation HTML content
    """
    pages = '<div class="pages">'
    pages += _previous(args.get('page.previous'))
    pages += _next(args.get('page.next'))
    pages += '</div>'
    return pages


def _previous(previous_page: str or None) -> str:
    """
    Retrieve the previous page link
    """
    if previous_page is None:
        return ''

    return f'<a href="{{{{ url }}}}{previous_page}" class="previous">Previous</a>'


def _next(next_page: str or None) -> str:
    """
    Retrieve the next page link
    """
    if next_page is None:
        return ''

    return f'<a href="{{{{ url }}}}{next_page}" class="next">Next</a>'
