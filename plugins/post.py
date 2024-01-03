"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
from html import escape


def more_posts(data: dict, args: dict) -> str:
    """
    Display the previous and next post
    """
    query = args.get('_stapy').get('json_query')
    posts = query.fetch('SELECT ITEMS WHERE "post" in tags ORDER BY date desc')
    iterator = 0
    post_previous = post_next = ''
    for _key, page in posts:
        if page.get('_full_path') == data.get('_full_path'):
            try:
                if iterator:
                    post_previous = '{% block.article + ' + posts[iterator - 1][1].get('_full_path') + ' %}'
                post_next = '{% block.article + ' + posts[iterator + 1][1].get('_full_path') + ' %}'
            except IndexError:
                pass
            break
        iterator = iterator + 1
    return f'<div class="post previous">{post_previous}</div><div class="post next">{post_next}</div>'


def picture(data: dict, args: dict) -> str:
    """
    Return an image element if src is not empty
    """
    if args.get('src', ''):
        return f'<img src="{{{{ url }}}}{escape(args.get("src"))}" alt="{escape(args.get("alt", ""))}" />'
    return ''
