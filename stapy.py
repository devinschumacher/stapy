"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
from email import message_from_bytes
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs, unquote
from typing import Any
import hashlib
import html
import importlib
import json
import os
import mimetypes
import re
import shutil
import socket
import sys
import time
import traceback

VERSION = '1.17.12'


class StapyPluginsInterface:
    def dispatch(self, method: str, value: Any, same_type: bool, args: dict) -> Any:
        return value

    def reload(self) -> None:
        pass


class StapyPluginsAdapter:
    def __init__(self) -> None:
        self._adapter = None

    def set(self, adapter: StapyPluginsInterface) -> None:
        self._adapter = adapter

    def dispatch(self, method: str, value: Any, same_type: bool, **kwargs) -> Any:
        if self._adapter:
            return self._adapter.dispatch(method, value, same_type, kwargs)
        return value

    def reload(self) -> None:
        if self._adapter:
            self._adapter.reload()


class StapyFileSystem:
    _environments = {}

    def __init__(self, plugins) -> None:
        self._sp = plugins
        self._pages = {}

    @staticmethod
    def get_version() -> str:
        return VERSION

    @staticmethod
    def get_root_dir() -> str:
        return os.path.dirname(os.path.abspath(__file__)) + os.sep

    def get_plugins_dir(self) -> str:
        return self.get_root_dir() + 'plugins'

    def get_build_dir(self) -> str:
        return self.get_root_dir() + 'web'

    def get_source_dir(self, directory: str = '') -> str:
        return self.get_root_dir() + 'source' + (os.sep + os.path.normpath(directory) if directory else '')

    @staticmethod
    def get_encoding() -> str:
        return 'utf-8'

    @staticmethod
    def get_local_environment() -> str:
        return 'local'

    def get_environments(self) -> dict:
        if not self._environments:
            if os.path.isdir(self.get_build_dir()):
                for env in os.listdir(self.get_build_dir()):
                    path = os.path.join(self.get_build_dir(), env)
                    if os.path.isdir(path):
                        self._environments[env] = path
            self._environments[self.get_local_environment()] = False
        return self._environments

    def get_file_content(self, path: str, mode: str = 'r', encoding: str = None) -> str or bytes:
        if encoding is None and 'b' not in mode:
            encoding = self.get_encoding()
        with open(os.path.normpath(path), mode, encoding=encoding) as file:
            content = file.read()
        return self._sp.dispatch('file_content_opened', content, True, path=path, mode=mode)

    @staticmethod
    def get_file_extension(file: str) -> str:
        extension = os.path.splitext(file)[1]
        if not extension:
            extension = ''
        return extension.replace('.', '')

    @staticmethod
    def get_file_type(file: str) -> str:
        mime, encoding = mimetypes.guess_type(file)
        if not mime:
            return 'application/octet-stream'
        if encoding:
            return f'{mime}; charset={encoding}'
        return mime

    def get_layout_config(self, path: str) -> str:
        return os.path.normpath(self.get_source_dir('layout') + '/' + path.lstrip('/') + '.json')

    def get_page_config(self, path: str) -> str:
        return os.path.normpath(self.get_source_dir('pages') + '/' + path.lstrip('/') + '.json')

    def get_page_data(self, path: str = '', merge: bool = True) -> dict:
        extension = self.get_file_extension(path)
        files = []
        if merge:
            files = [self.get_layout_config('common'), self.get_layout_config(extension)]
            directories = []
            directory = os.path.dirname(path.strip('/'))
            while directory:
                directories.append(self.get_layout_config(directory + '/' + extension))
                directories.append(self.get_layout_config(directory + '/' + 'common'))
                directory = os.path.dirname(directory.strip('/'))
            files.extend(reversed(directories))
        if path:
            files.append(self.get_page_config(path))
        data = self.merge_json(files)
        data['_full_path'] = path.lstrip('/')
        data['_path'] = path.lstrip('/').replace('index.html', '')
        return self._sp.dispatch('page_data_merged', data, True, path=path)

    def get_pages_data(self, with_disabled: bool = True) -> dict:
        if not self._pages:
            files = self.get_files(self.get_source_dir('pages'))
            for file in files:
                key = re.sub(r'^' + re.escape(self.get_source_dir('pages')), '', file).replace('\\', '/')
                key = re.sub(r'\.json$', '', key)
                data = self.get_page_data(key)
                if not with_disabled and not self.is_enabled(data):
                    continue
                self._pages[key] = data
        return self._pages

    def reset_pages_data(self) -> int:
        total = len(self._pages)
        self._pages = {}
        return total

    @staticmethod
    def is_enabled(data: dict) -> bool:
        return 'enabled' not in data or data['enabled'] in ('1', 1, True)

    @staticmethod
    def create_directory(path: str) -> None:
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        Path(os.path.normpath(path)).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def rm_directory_content(src: str, except_file: list = None) -> None:
        if except_file is None:
            except_file = ['.git', '.gitignore', '.gitkeep']
        src = os.path.normpath(src)
        for item in os.listdir(src):
            if item in except_file:
                continue
            path = os.path.join(src, item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)

    def create_file(self, path: str, content: str = '', mode: str = 'w', encoding: str = None) -> None:
        if encoding is None and 'b' not in mode:
            encoding = self.get_encoding()
        path = os.path.normpath(path)
        self.create_directory(path)
        with open(path, mode, encoding=encoding) as file:
            file.write(content)

    def copy_tree(self, src: str, dst: str, env: str = None) -> None:
        src = os.path.normpath(src)
        dst = os.path.normpath(dst)
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            source = os.path.join(src, item)
            destination = os.path.join(dst, item)
            if os.path.isdir(source):
                self.copy_tree(source, destination, env)
            else:
                if not os.path.exists(destination) or os.stat(source).st_mtime - os.stat(destination).st_mtime > 1:
                    content = self.get_file_content(source, 'rb')
                    if content:
                        self.create_file(destination, content, 'wb')

    def get_files(self, src: str, files: list = None, sub_dir: bool = True) -> list:
        if files is None:
            files = []
        src = os.path.normpath(src)
        if not os.path.isdir(src):
            return files
        for item in os.listdir(src):
            path = os.path.join(src, item)
            if os.path.isdir(path):
                if sub_dir:
                    self.get_files(path, files)
            else:
                files.append(path)
        files.sort()
        return files

    def merge_json(self, files: list) -> dict:
        merged = json.loads('{}')
        for file in files:
            if os.path.exists(file):
                with open(file, encoding=self.get_encoding()) as content:
                    try:
                        data = json.load(content)
                        for (key, value) in data.items():
                            merged[key] = value
                    except Exception as exception:
                        raise Exception(file + ':\n' + str(exception)) from exception
        return merged

    def get_flag(self, flag: str) -> bool:
        return os.path.isfile(self.get_root_dir() + flag)

    def is_secure(self) -> bool:
        return self.get_flag('secure')

    @staticmethod
    def get_page_path(path: str) -> str:
        if not path.endswith('/') and '.' not in path:
            path += '/'
        if path.endswith('/'):
            path = path + 'index.html'
        return path


class StapyJsonQuery:
    def __init__(self, file_system, encoder) -> None:
        self._fs = file_system
        self._se = encoder

    def fetch(self, query: str, with_disabled: bool = False) -> list:
        (where, order, limit) = self.build(query)
        search = {}
        i = 0
        for data in self._fs.get_pages_data(with_disabled).values():
            try:
                if where and not eval(where):
                    continue
            except TypeError as type_error:
                raise TypeError(str(type_error) + '\n\n' + query + '\n\nEval: ' + where) from type_error
            search[str(data[order[0]]) + str(i) if order[0] and order[0] in data else '!' + str(i)] = data.copy()
            i += 1
        return sorted(search.items(), reverse=order[1] == 'desc')[limit[0]:limit[1]]

    def build(self, query: str) -> tuple:
        where = order = limit = None
        build_where = 0
        keys = self._extract_keywords(self._format_keywords(self._se.encode_exp(query)))
        for _i, keyword in enumerate(keys):
            if keyword == 'SELECT-ITEMS':
                limit = self._build_limit(keys, _i)
                build_where = 0
            elif keyword == 'ORDER-BY':
                order = self._build_sort_order(keys, _i)
                build_where = 0
            elif build_where > 2 and keyword.upper() in ['OR', 'AND']:
                where += f'{keyword.lower()} '
                build_where = 1
                continue
            elif build_where and keyword in ['(', ')']:
                where += f'{keyword} '
                continue
            elif build_where:
                if build_where == 1:
                    try:
                        where += f'{self._build_where_part_1(keys, keyword, _i)} '
                    except IndexError:
                        build_where = 0
                        continue
                elif build_where == 2:
                    where += f'{self._build_where_part_2(keys, keyword, _i)} '
                elif build_where == 3:
                    where += f'{self._build_where_part_3(keys, keyword, _i)} '
                build_where += 1
            elif keyword.upper() == 'WHERE':
                where = ''
                build_where = 1
        return where, self._format_order(order), self._format_limit(limit)

    def _build_limit(self, _keys: list, _i: int) -> tuple or None:
        _limit = None
        try:
            if re.search(r'^([0-9]+)-([0-9]+)$', _keys[_i + 1]):
                _limit = self._string_to_tuple(_keys[_i + 1].replace('-', ':'))
            if re.search(r'^([0-9]+)$', _keys[_i + 1]):
                _limit = self._string_to_tuple(_keys[_i + 1])
        except IndexError:
            pass
        return _limit

    def _build_sort_order(self, _keys: list, _i: int) -> tuple or None:
        try:
            _order = _keys[_i + 1] + ':'
        except IndexError:
            return None
        try:
            if _keys[_i + 2].lower() in ('asc', 'desc'):
                _order += _keys[_i + 2].lower()
            else:
                _order += 'asc'
        except IndexError:
            _order += 'asc'
        return self._string_to_tuple(_order)

    def _build_where_part_1(self, _keys: list, _keyword: str, _i: int) -> str:
        if _keys[_i + 1].lower() in ['in', 'not-in']:
            return f'("{self._format_data_key(_keys[_i + 2])}" in data and ' + self._format_data_value(_keyword)
        return f'("{self._format_data_key(_keyword)}" in data and data["{self._format_data_key(_keyword)}"]'

    @staticmethod
    def _build_where_part_2(_keys: list, _keyword: str, _i: int) -> str:
        if _keyword.lower() in ['=', '>', '<', '!=', '>=', '<=', 'in', 'not-in']:
            if _keyword == "not-in":
                return 'not in'
            if _keyword.lower() != "=":
                return _keyword.lower()
        return '=='

    def _build_where_part_3(self, _keys: list, _keyword: str, _i: int) -> str:
        if _keys[_i - 1].lower() in ['in', 'not-in']:
            return f'data["{self._format_data_key(_keyword)}"])'
        return self._format_data_value(_keyword) + ')'

    def _string_to_tuple(self, string: str) -> tuple:
        return tuple(self._se.decode_exp(item) for item in string.split(':'))

    @staticmethod
    def _format_order(order: tuple = None) -> tuple:
        if order is None:
            order = ('', 'asc')
        if len(order) == 1:
            order = (order[0], 'asc')
        return order

    @staticmethod
    def _format_limit(limit: tuple = None) -> tuple:
        if limit is None:
            limit = (1, 10000)
        if len(limit) == 1:
            limit = (limit[0], limit[0])
        return int(limit[0]) - 1 if int(limit[0]) > 0 else 0, int(limit[1])

    @staticmethod
    def _extract_keywords(_query: str) -> list:
        conditions = [')', '(', '=', '>', '<', '! =', '>  =', '<  =']
        for condition in conditions:
            _query = _query.replace(condition, f' {condition.replace(" ", "")} ')
        return re.sub(' +', ' ', _query).split(' ')

    def _format_data_key(self, _keyword: str, escape: bool = True) -> str:
        _keyword = self._se.decode_exp(_keyword.replace('"', '').replace("'", ''))
        if escape:
            _keyword = _keyword.replace('"', '\\"')
        return _keyword

    def _format_data_value(self, _keyword: str) -> str:
        is_str = False
        for enclosed in ['"', "'"]:
            if _keyword.startswith(enclosed) and _keyword.endswith(enclosed):
                is_str = True
        _keyword = self._format_data_key(_keyword)
        if _keyword.lower() in ['true', 'false']:
            return _keyword.capitalize()
        if is_str:
            return f'"{_keyword}"'
        return _keyword

    @staticmethod
    def _format_keywords(_query: str) -> str:
        _keywords = {'SELECT ITEMS': 'SELECT-ITEMS', 'ORDER BY': 'ORDER-BY', 'not in': 'not-in'}
        for _from, _to in _keywords.items():
            _query = re.compile(re.escape(_from), re.IGNORECASE).sub(_to, _query)
        return _query


class StapyParser:
    def __init__(self, plugins, file_system, json_query, encoder) -> None:
        self._sp = plugins
        self._fs = file_system
        self._jq = json_query
        self._se = encoder
        self._env = ''
        self._path = ''

    def process(self, data: dict, content: str, env: str, path: str = '') -> str:
        self._env = env
        self._path = path
        data['_env'] = env
        content = self._sp.dispatch('before_content_parsed', content, True, data=data, env=env, path=path)
        content = self._parse(data, content)
        content = self.clean(content)
        content = self._sp.dispatch('after_content_parsed', content, True, data=data, env=env, path=path)
        return content

    def clean(self, content: str):
        tags = self._find_expressions(('{{', '}}'), content) + \
               self._find_expressions(('{:', ':}'), content) + \
               self._find_expressions(('{%', '%}'), content)
        for tag in tags:
            content = content.replace(tag[0], '')
        return content.replace(self._se.hash('{'), '{').replace(self._se.hash('}'), '}')

    def _parse(self, data: dict, content: str) -> str:
        content = content.replace('\\{', self._se.hash('{')).replace('\\}', self._se.hash('}'))
        content = self._plugin_tags(data, content)
        content = self._template_tags(data, content)
        content = self._content_tags(data, content)
        return content

    @staticmethod
    def _find_expressions(bounds: tuple, content: str) -> list:
        expressions = re.findall(r'' + bounds[0] + '(?!' + bounds[0] + ')(.*?)' + bounds[1], content, flags=re.DOTALL)
        result = []
        if expressions is not None:
            for expression in expressions:
                cleaned = expression.replace('\n', ' ').replace('\t', ' ').strip(' ')
                if cleaned:
                    result.append((bounds[0] + expression + bounds[1], cleaned))
        return result

    def _content_tags(self, data: dict, content: str, escape: bool = False) -> str:
        tags = self._find_expressions(('{{', '}}'), content)
        for tag in tags:
            keys = [tag[1], tag[1] + '.' + self._env]
            value = None
            for key in keys:
                value = data[key] if key in data else value
            if value is not None:
                if escape:
                    value = value.replace('"', '\\"').replace("'", "\\'")
                content = content.replace(tag[0], str(value))
        return content

    def _plugin_tags(self, data: dict, content: str) -> str:
        tags = self._find_expressions(('{:', ':}'), content)
        for tag in tags:
            parts = tag[1].split(' ')
            method = parts[0]
            args = {}
            cleaned = self._clean_tag(tag[1], data)
            self._add_args_to_data(args, cleaned)
            args['env'] = self._env
            args['path'] = self._path
            result = self._sp.dispatch(method, data, False, **args)
            if result != data:
                content = content.replace(tag[0], self._parse(data, str(result)))
        return content

    def _template_tags(self, data: dict, content: str) -> str:
        tags = self._find_expressions(('{%', '%}'), content)
        tags = list(set(tags))
        for tag in tags:
            parts = tag[1].split(' ')
            block = parts[0]
            keys = [block, block + '.' + self._env]
            tpl = None
            for key in keys:
                tpl = data[key] if key in data else tpl
            if not isinstance(tpl, str) or tpl == '':
                continue
            cleaned = self._clean_tag(tag[1], data)
            tag_data = cleaned.rsplit(' + ', 1)
            tag_query = cleaned.rsplit(' ~ ', 1)
            if len(tag_data) > 1:
                result = self._tpl_file_data(tpl, tag_data[0], tag_data[1], data, block)
            elif len(tag_query) > 1:
                result = self._tpl_file_query(tpl, tag_query[0], tag_query[1], data, block)
            else:
                result = self._tpl_file(tpl, cleaned, data, block)
            content = content.replace(tag[0], result)
        return content

    def _clean_tag(self, tag: str, data: dict) -> str:
        return self._se.encode_exp(self.clean(self._content_tags(data, tag, True)))

    def _tpl_file(self, template: str, args: str, data: dict, key: str) -> str:
        child_data = {}
        self._add_args_to_data(child_data, args)
        return self._get_child_content(data, child_data, template, key)

    def _tpl_file_data(self, template: str, args: str, path: str, data: dict, key: str) -> str:
        child = self._fs.get_page_data(path)
        self._add_args_to_data(child, args)
        child = self._sp.dispatch('child_content_data', child, True, key=key, env=self._env, path=self._path, data=data)
        return self._get_child_content(data, child, template, key)

    def _tpl_file_query(self, template: str, args: str, query: str, data: dict, key: str) -> str:
        pages = self._jq.fetch(query)
        pages = self._sp.dispatch(
            'child_content_query_result', pages, True, key=key, env=self._env, path=self._path, data=data
        )
        children = []
        separator = ''
        for child in pages:
            self._add_args_to_data(child[1], args)
            children.append(self._get_child_content(data, child[1], template, key))
            separator = (child[1]['delimiter'] if 'delimiter' in child[1] else '') + '\n'
        return separator.join(children)

    def _add_args_to_data(self, data: dict, args: str) -> None:
        args = args.replace('"', '').replace("'", '')
        if args.strip(' '):
            try:
                for arg in args.split(' '):
                    values = arg.split(':')
                    if len(values) == 2:
                        data[self._se.decode_exp(values[0])] = self._se.decode_exp(values[1])
            except Exception as exception:
                raise Exception('Arguments syntax error\n' + str(exception)) from exception

    def _get_child_content(self, page_data: dict, child_data: dict, template: str, key: str) -> str:
        template = child_data['_child_template'] if '_child_template' in child_data else template
        if not template:
            return ''
        child_data = {'$' + str(k): v for k, v in child_data.items()}
        merged_data = {**page_data, **child_data}
        keys = [key, key + '.' + self._env]
        for _key in keys:
            if _key in merged_data:
                del merged_data[_key]
        try:
            return self._parse(merged_data, self._fs.get_file_content(self._fs.get_source_dir(template)))
        except OSError as os_error:
            raise Exception(str(os_error)) from os_error


class StapyEncoder:
    def __init__(self, protected_exp: list = None) -> None:
        if protected_exp is None:
            protected_exp = [' ', ':', '+', '~', '"', '\'', '!=', '>=', '<=', '=', '>', '<', ')', '(', 'where', 'WHERE']
        self._protected_exp = protected_exp

    def encode_exp(self, value: str) -> str:
        value = self.__encode_escaped_quotes(value, '"')
        value = self.__encode_escaped_quotes(value, "'")
        value = self.__encode_char_between_quotes(value, '"', "'")
        value = self.__encode_char_between_quotes(value, "'", '"')
        value = self.__encode_protected_exp(value, '"')
        value = self.__encode_protected_exp(value, "'")
        return re.sub(' +', ' ', value).strip(' ')

    def decode_exp(self, value: str) -> str:
        for exp in self._protected_exp:
            value = value.replace(self.hash(exp), exp)
        return value

    @staticmethod
    def hash(value: str) -> str:
        return '^' + hashlib.md5(value.encode()).hexdigest() + '$'

    def __encode_escaped_quotes(self, value: str, quote: str) -> str:
        return value.replace(f'\\{quote}', self.hash(quote))

    def __encode_char_between_quotes(self, value: str, quote: str, char: str) -> str:
        strings = re.findall(rf'{quote}(.+?){quote}', value)
        for string in strings:
            value = value.replace(string, string.replace(char, self.hash(char)))
        return value

    def __encode_protected_exp(self, value: str, quote: str) -> str:
        strings = re.findall(rf'{quote}(.+?){quote}', value.replace(f':{quote}{quote} ', ': '))
        for string in strings:
            origin = string
            for exp in self._protected_exp:
                string = string.replace(exp, self.hash(exp))
            value = value.replace(f'{quote}{origin}{quote}', f'{quote}{string}{quote}')
        return value


class StapyGenerator:
    def __init__(self, file_system, json_query, parser) -> None:
        self._fs = file_system
        self._jq = json_query
        self._ps = parser

    def build(self, envs: list = None) -> dict:
        if envs is None:
            envs = []
        self.reset(envs)
        self.copy_resources(envs)
        pages = self.get_pages()
        result = {}
        for env in self._fs.get_environments().keys():
            if envs and env not in envs:
                continue
            if env != self._fs.get_local_environment():
                start = time.time()
                for page_path, enable in list(pages.items()):
                    if not enable:
                        del pages[page_path]
                        continue
                    self.generate_page(page_path, env)
                result[env] = {"number": len(pages), "time": round((time.time() - start), 4)}
        return result

    def get_pages(self, full: bool = False) -> dict:
        pages = self._fs.get_pages_data()
        result = {}
        for page, data in pages.items():
            if not self._fs.get_file_extension(page):
                continue
            result[page] = data if full else self._fs.is_enabled(data)
        return result

    def generate_page(self, page_path: str, env: str) -> str:
        data = self.get_page_data(page_path)
        try:
            template = '{% content %}'
            if data.get('template', False):
                template = self._fs.get_file_content(self._fs.get_source_dir(str(data['template'])))
        except OSError as os_error:
            raise Exception(str(os_error)) from os_error
        result = self._ps.process(data, template, env, page_path)
        if env != self._fs.get_local_environment():
            self.save_page(result, env, page_path)
        return result

    def get_page_data(self, page_path: str):
        self._fs.get_file_content(self._fs.get_page_config(page_path))
        return self._fs.get_page_data(page_path)

    def copy_resources(self, envs: list = None) -> dict or None:
        if envs is None:
            envs = []
        for env, directory in self._fs.get_environments().items():
            if directory and (not envs or env in envs):
                self._fs.copy_tree(self._fs.get_source_dir('assets'), directory, env)

    def save_page(self, content: str, env: str, page_path: str) -> None:
        if env != self._fs.get_local_environment():
            self._fs.create_file(self._fs.get_environments()[env] + page_path, content)

    def reset(self, envs: list = None) -> None:
        if envs is None:
            envs = []
        self._fs.reset_pages_data()
        for path in self._fs.get_environments().values():
            if path and (not envs or os.path.basename(path) in envs):
                self._fs.rm_directory_content(path)


class StapyPlugins(StapyPluginsInterface):
    def __init__(self, file_system, json_query, parser, generator) -> None:
        self._fs = file_system
        self._jq = json_query
        self._gs = generator
        self._ps = parser
        self._plugins = self._load()

    def dispatch(self, method: str, value: Any, same_type: bool, args: dict) -> Any:
        type_origin = type(value)
        for name, module in self._plugins.items():
            _method = method
            if '.' in method:
                plugin, _method = method.split('.', 1)
                if name not in ['plugins.' + plugin, 'plugins.' + plugin + '.main']:
                    continue
            if not _method:
                raise Exception('Failed to load plugin. Method name in "' + method + '" is missing.')
            if _method[0] == '_':
                raise Exception('Failed to load plugin. "' + method + '" is a protected method.')
            if hasattr(module['module'], _method):
                arg_count = getattr(module['module'], _method).__code__.co_argcount
                if arg_count == 0:
                    value = getattr(module['module'], _method)()
                elif arg_count == 1:
                    value = getattr(module['module'], _method)(value)
                else:
                    args['_stapy'] = {
                        'file_system': self._fs,
                        'json_query': self._jq,
                        'parser': self._ps,
                        'generator': self._gs,
                        'plugins': self
                    }
                    value = getattr(module['module'], _method)(value, args)
            if same_type and not isinstance(value, type_origin):
                raise Exception(
                    'Error in "' + name + '.' + _method + '" return statement.\n\n' +
                    'Expected "' + type_origin.__name__ + '" object, got "' + type(value).__name__ + '"'
                )
        return value

    def reload(self) -> None:
        files = self._get_plugin_files()
        for name, file in files.items():
            if name in self._plugins and self._plugins[name]['updated_at'] != os.path.getmtime(file):
                importlib.reload(self._plugins[name]['module'])
                self._plugins[name]['updated_at'] = os.path.getmtime(file)
            if name not in self._plugins:
                self._plugins[name] = {'module': importlib.import_module(name), 'updated_at': os.path.getmtime(file)}
        for name in list(self._plugins.keys()):
            if name not in files:
                del self._plugins[name]

    def _load(self) -> dict:
        files = self._get_plugin_files()
        plugins = {}
        for name, file in files.items():
            plugins[name] = {'module': importlib.import_module(name), 'updated_at': os.path.getmtime(file)}
        return plugins

    def _get_plugin_files(self) -> dict:
        plugins = {}
        src = os.path.normpath(self._fs.get_plugins_dir())
        for item in os.listdir(src):
            path = os.path.join(src, item)
            if os.path.isdir(path):
                file = path + os.sep + 'main.py'
                if os.path.isfile(file):
                    plugins['plugins.' + os.path.basename(path) + '.main'] = file
            else:
                if path.endswith('.py'):
                    plugins['plugins.' + os.path.basename(path).replace('.py', '')] = path
        return plugins


class StapyHTTPRequestHandler(BaseHTTPRequestHandler):
    _sp = StapyPluginsAdapter()
    _fs = StapyFileSystem(_sp)
    _se = StapyEncoder()
    _jq = StapyJsonQuery(_fs, _se)
    _ps = StapyParser(_sp, _fs, _jq, _se)
    _gs = StapyGenerator(_fs, _jq, _ps)
    _sp.set(StapyPlugins(_fs, _jq, _ps, _gs))

    def __init__(self, request: Any, client_address: tuple, server: HTTPServer) -> None:
        self.path = '/'
        try:
            super().__init__(request, client_address, server)
            self._sp.dispatch('http_request_initialized', self.path, False)
        except ConnectionResetError:
            pass

    def __del__(self) -> None:
        self._sp.dispatch('http_request_sent', self.path, False)

    def do_GET(self) -> None:
        query = self.parse_path().query
        self.send(self.plugins() or self.reserved_request(parse_qs(query, keep_blank_values=True)) or self.process())

    def do_POST(self) -> None:
        if 'multipart/form-data' in self.headers.get('Content-Type', ''):
            data = self.parse_multipart_form_data()
        else:
            data = parse_qs(
                qs=self.rfile.read(int(self.headers.get('content-length', 0))).decode(),
                keep_blank_values=True
            )
        rst = {**parse_qs(qs=self.parse_path().query, keep_blank_values=True), **data}
        self.send(self.plugins() or self.reserved_request(rst) or self.not_found())

    def do_HEAD(self) -> None:
        self.parse_path()
        self.send(self.plugins() or self.process(), False)

    def parse_multipart_form_data(self) -> dict:
        data = {}
        body = self.rfile.read(int(self.headers.get('content-length', 0)))
        post = message_from_bytes(f'Content-Type: {self.headers.get("Content-Type", "")}\n'.encode() + body)
        if not post.is_multipart():
            return data
        for part in post.get_payload():
            name = part.get_param('name', header='content-disposition')
            if not name:
                continue
            if name not in data:
                data[name] = []
            if part.get_filename():
                data[name].append({'filename': part.get_filename(), 'content': part.get_payload(decode=True)})
            else:
                data[name].append(part.get_payload(decode=True).decode(self._fs.get_encoding()))
        return data

    def parse_path(self):
        parsed = urlparse(self.path)
        self.path = parsed.path
        return parsed

    def process(self) -> dict:
        try:
            result = self.get_page()
        except OSError:
            try:
                result = self.get_file()
            except OSError:
                result = self.not_found()
            except Exception as exception:
                result = self.server_error(exception)
        except Exception as exception:
            result = self.server_error(exception)
        return result

    def plugins(self) -> dict or None:
        try:
            self._sp.reload()
        except Exception as exception:
            return self.server_error(exception)
        return None

    def send(self, result: dict, content: bool = True) -> None:
        self.send_response_only(result['status'])
        self.send_header('Date', self.date_time_string())
        self.send_header('Content-type', result['type'])
        for header in result.get('headers', []):
            if len(header) == 2:
                self.send_header(header[0], header[1])
        self.end_headers()
        if content:
            try:
                self.wfile.write(result['content'])
            except ConnectionError:
                pass

    def get_file(self) -> dict:
        file = self._fs.get_source_dir('assets') + unquote(self.path)
        return self.get_response(200, self._fs.get_file_content(file, 'rb'), self._fs.get_file_type(file))

    def get_page(self) -> dict:
        page_path = self.get_page_path()
        result = self._gs.generate_page(page_path, self._fs.get_local_environment())
        return self.get_response(200, result.encode(), self._fs.get_file_type(page_path))

    def reserved_request(self, data: dict) -> dict or None:
        try:
            result = self.get_reserved_request_data(data)
            if not result:
                return None
            return self.get_response(200, str(result[0]).encode(), result[1], result[2] if len(result) > 2 else [])
        except Exception as exception:
            return self.server_error(exception)

    def get_reserved_request_data(self, data: dict) -> tuple or None:
        if self.path in ['/_pages', '/_pages/']:
            self._fs.reset_pages_data()
            return json.dumps(self._gs.get_pages()), 'application/json'
        if self.path in ['/_pages/data', '/_pages/data/']:
            self._fs.reset_pages_data()
            return json.dumps(self._gs.get_pages(True)), 'application/json'
        if self.path in ['/_environments', '/_environments/']:
            return json.dumps(self._fs.get_environments()), 'application/json'
        if self.path in ['/_cache/clear', '/_cache/clear/']:
            total = self._fs.reset_pages_data()
            result = {'status': False, 'message': 'Nothing to clear'}
            if total:
                result = {'status': True, 'message': f'Cache for {total} page{"s" if total > 1 else ""} cleared'}
            return json.dumps(result), 'application/json'
        page = re.search(r'^/_page/(.*?)$', self.path, flags=re.IGNORECASE)
        if page:
            return json.dumps(self._gs.get_page_data('/' + page.group(1))), 'application/json'
        tpl = re.search(r'^/_content/(.*?)$', self.path, flags=re.IGNORECASE)
        if tpl:
            content = json.dumps({'content': self._fs.get_file_content(self._fs.get_source_dir(tpl.group(1)))})
            return content, 'application/json'
        return self._sp.dispatch('custom_http_response', None, False, request=data, path=self.path)

    def get_page_path(self) -> str:
        return self._fs.get_page_path(self.path)

    @staticmethod
    def get_response(status: int, content: bytes, file_type: str = None, headers: list = None) -> dict:
        return {
            'status': status,
            'content': content,
            'type': file_type or 'text/html; charset=utf-8',
            'headers': headers or []
        }

    def not_found(self) -> dict:
        path = self._fs.get_page_config(self.get_page_path())
        if self._fs.is_secure():
            path = path.replace(self._fs.get_root_dir(), '')
        template = self.default_tpl(
            'Page Not Found',
            '<h1>Page Not Found</h1><p><i>"' + path + '"</i> does not exist</p>'
        )
        return self.get_response(404, template.encode())

    def server_error(self, exception: Exception) -> dict:
        error = type(exception).__name__
        trace_back = 'Exception printing is disabled by default for security reasons.'
        if not self._fs.is_secure():
            error = type(exception).__name__ + ': ' + str(exception)
            trace_back = re.sub(r' {2}File', '\nFile', traceback.format_exc().split('\n', 1)[1])
        template = self.default_tpl(
            'There has been an error processing your request',
            '<h1>Oops, an error occurred</h1><pre><span>' + error + '</span>\n\n' + html.escape(trace_back) + '</pre>',
            '#5e0006'
        )
        return self.get_response(500, template.encode())

    @staticmethod
    def default_tpl(title: str, content: str, background: str = '#070026') -> str:
        return '<!DOCTYPE html><html><head><title>' + title + '</title><style>body{font:normal 18px system-ui;' \
          'margin:0 auto;max-width:900px;padding:40px 10px;text-align:center;background:' + background + ';color:#fff' \
          '}pre{text-align:left;background:#fff;color:#000;padding:20px 10px;overflow-x:auto;font-size:16px;' \
          'height:600px;box-shadow:0 0 20px -5px #000}pre span{color:#a4000a}</style></head>' \
          '<body>' + content + '</body></html>'


class StapyHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    """Handle requests in a separate thread."""


def build(envs: list = None) -> None:
    if envs is None:
        envs = []
    print(f'=^..^= Welcome to Stapy {VERSION}')
    print('Build in progress...')
    _sp = StapyPluginsAdapter()
    _fs = StapyFileSystem(_sp)
    _se = StapyEncoder()
    _jq = StapyJsonQuery(_fs, _se)
    _ps = StapyParser(_sp, _fs, _jq, _se)
    _gs = StapyGenerator(_fs, _jq, _ps)
    _sp.set(StapyPlugins(_fs, _jq, _ps, _gs))
    result = _gs.build(envs)
    if not result:
        print('Nothing to build. You need to add environment in the web directory.')
    for env, data in result.items():
        print(f'[{env}] {str(data["number"])} pages generated in {str(data["time"])} seconds')


def serve(host: tuple) -> None:
    try:
        print(f'=^..^= Welcome to Stapy {VERSION}')
        print(f'Serving under http://{":".join([str(v) for v in host])}')
        httpd = StapyHTTPServer(host, StapyHTTPRequestHandler)
        httpd.serve_forever()
    except socket.gaierror:
        print(f'Name or service not known: {str(host)}')


def main():
    try:
        if 'build' in sys.argv:
            envs = []
            for env in sys.argv[2:]:
                envs.append(env)
            build(envs)
        else:
            host = ('127.0.0.1', 1985)
            for arg in sys.argv:
                match = re.findall(r'(?P<host>.*):(?P<port>[0-9]+)', arg)
                if match:
                    host = (match[0][0], int(match[0][1]))
            serve(host)
    except KeyboardInterrupt:
        print("\nGood bye!")


if __name__ == "__main__":
    main()
