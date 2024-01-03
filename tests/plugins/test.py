def page_data_merged(data: dict) -> dict:
    data['plugin'] = 'ok'
    return data


def child_content_data(data: dict, args: dict) -> dict:
    if args['key'] == 'child_block':
        data['smiley'] = ':)'
    return data


def child_content_query_result(items: list, args: dict) -> list:
    if args['key'] == 'child_block':
        iterator = 0
        for position, page in items:
            items[iterator][1]['smiley'] = ':)'
            iterator += 1
    if args['key'] == 'query_block':
        iterator = 0
        for position, page in items:
            items[iterator][1]['query_plugin'] = '/ 2'
            iterator += 1
    return items


def plugin_directive(data: dict, args: dict) -> str:
    env = args['env']
    if env == 'local':
        return 'Local!'
    if env == 'prod':
        return 'Prod!'
    return 'Default!'


def inception_plugin(data: dict, args: dict) -> str:
    if 'var' in args:
        return args['var']
    return '{% block.inception %}'


def plugin_directive_custom_arg(data: dict, args: dict) -> str:
    return ' '.join([args['foo'], args['name'], args['simple'], args['feeling_1'], args['feeling_2'], args['chars']])


def specific_plugin_directive() -> str:
    return 'Specific'
