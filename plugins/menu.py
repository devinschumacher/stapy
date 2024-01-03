"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""


def child_content_query_result(items: list, args: dict) -> list:
    """
    For the block.menu.link query (template/block/menu.html), we add a param "menu_item.class" to the menu page data.
    If current page path matches menu link path, we add "active" to the class.
    Finally, we can use the param in the menu link template (template/block/menu/link.html).
    """
    key = args['key']
    path = args['path']
    page_data = args['data']

    if key != 'block.menu.link':
        return items
    iterator = 0
    for key, data in items:
        class_name = 'menu-item'

        if iterator == 0:
            class_name += ' first'

        if iterator == len(items) - 1:
            class_name += ' last'

        if data.get('_full_path') in [path.lstrip('/'), page_data.get('menu.active', '')]:
            class_name += ' active'

        items[iterator][1]['menu_item.class'] = class_name

        iterator += 1
    return items
