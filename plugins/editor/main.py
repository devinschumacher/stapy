"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
import json
import os
import re
import time
import unicodedata
import zlib
from html import escape, unescape
from pathlib import Path
from urllib.parse import quote, unquote

VERSION = '1.3.3'


def custom_http_response(response: tuple or None, args: dict) -> tuple or None:
    """
    Test if the requested path matches with an editor page
    """
    editor = Editor(
        args['path'],
        args['request'],
        args['_stapy']['file_system'],
        args['_stapy']['json_query'],
        args['_stapy']['generator'],
        args['_stapy']['plugins']
    )
    return editor.match() or response


class Editor:
    _config = {}
    _messages = {}
    _editor_key = None

    def __init__(self, path, request, file_system, json_query, generator, plugins) -> None:
        self._path = path or '/'
        self._request = request
        self._fs = file_system
        self._jq = json_query
        self._gs = generator
        self._sp = plugins
        self._load_config(path.split('/')[1])

    def match(self) -> tuple or None:
        """
        Test if the requested path matches with an editor page
        """
        if not self._editor_key:
            return None

        if self._path.rstrip('/') == self._editor_key:
            return self.page_list(), 'text/html'

        if self._path.rstrip('/') == f'{self._editor_key}/build':
            self._build()
            return self.page_list(), 'text/html'

        if self._path.rstrip('/') == f'{self._editor_key}/media' and self.get_config().get('media', False):
            if self._request.get('form_method', [''])[0] == 'save':
                self._media_save()
            if self._request.get('remove', False):
                self._media_remove(self._request.get('remove')[0])
            return self.page_media(), 'text/html'

        if self._path.rstrip('/') == f'{self._editor_key}/page':
            path = unquote(self._request.get('edit', [''])[0]).replace('../', '/')
            if self._request.get('form_method', [''])[0] == 'save':
                path = self._page_save(path)
                if self._request.get('ajax', ['0'])[0] == '1':
                    return self._block_messages(), 'text/html'
            if self._request.get('remove', ['0'])[0] == '1' and path:
                self._page_remove(path)
                return self.page_list(), 'text/html'
            return self.page_edit(path or None), 'text/html'

        asset = re.search(rf'^{self._editor_key}/assets/(.*?)$', self._path, flags=re.IGNORECASE)
        if asset:
            file = f'{os.path.dirname(__file__)}{os.sep}assets{os.sep}{asset.group(1)}'
            headers = [('Cache-Control', 'max-age=86400')]
            return self._fs.get_file_content(file, 'r', 'utf-8'), self._fs.get_file_type(file), headers

        return self._sp.dispatch('editor_plugin_match', None, False, {'editor': self})

    def add_message(self, level: str, message: str) -> None:
        """
        Add a message
        """
        if not self._messages.get(level):
            self._messages[level] = []
        self._messages[level].append(message)

    def get_messages(self, level: str, reset: bool = True) -> list:
        """
        Retrieve messages by level
        """
        messages = dict(self._messages)
        if reset:
            self._messages[level] = []
        return messages.get(level, [])

    def get_config(self) -> dict:
        """
        Retrieve configuration
        """
        return self._config

    def get_path(self) -> str:
        """
        Retrieve path
        """
        return self._path

    def get_editor_key(self) -> str or None:
        """
        Retrieve editor key
        """
        return self._editor_key

    def _load_config(self, key) -> dict:
        """
        Load the editor config file
        """
        self._config = {}
        file = self._fs.get_source_dir() + os.sep + 'editor.json'
        if not os.path.isfile(file):
            file = os.path.dirname(__file__) + os.sep + 'editor.json'
        if not os.path.isfile(file):
            return self._config
        config = self._fs.merge_json([file]).get(key, {})
        if config:
            self._editor_key = '/' + key
            self._config = config
        return self._config

    def _build(self) -> None:
        """
        Build the website for all environments
        """
        try:
            result = self._gs.build()
            if not result:
                self.add_message('error', 'Nothing to build. You need to add an environment in the web directory.')
            else:
                messages = []
                for env, data in result.items():
                    messages.append(
                        '[' + env + '] ' + str(data['number']) + ' pages generated in ' + str(data['time']) + ' seconds'
                    )
                self.add_message('success', '<br />'.join(messages))
        except PermissionError:
            self.add_message('error', 'Build: permission denied')

    def _page_remove(self, current_path) -> str:
        """
        Remove the page with all child blocks
        """
        if not current_path:
            self.add_message('error', 'The page path is missing')
            return current_path

        if not self._can_edit_page(current_path):
            self.add_message('error', 'The page cannot be deleted')
            return current_path

        json_path = self._fs.get_page_config(current_path)
        if not os.path.exists(json_path):
            self.add_message('error', f'Page "{current_path}" does not exist')
            return current_path

        page = self._fs.get_page_data(current_path, False)
        config = self.get_config().get('form', {})

        if not config.get('actions', {}).get('delete', False):
            self.add_message('error', 'Access denied')
            return current_path

        # Remove the page child blocks
        for fieldset in config.get('fieldsets', []):
            for var, options in fieldset.get('fields', {}).items():
                if var in page and options.get('type') == 'block':
                    file = self._fs.get_source_dir(page[var])
                    if os.path.exists(file):
                        try:
                            os.remove(file)
                        except PermissionError:
                            self.add_message('error', 'Remove page content: permission denied')

        # Remove the page config file
        try:
            os.remove(json_path)
            self.add_message('success', f'Page "{current_path}" has been deleted')
        except PermissionError:
            self.add_message('error', 'Remove page data: permission denied')

        return current_path

    def _media_remove(self, file) -> str:
        """
        Remove the media file
        """
        if not file:
            self.add_message('error', 'The file path is missing')
            return file

        config = self.get_config().get('media', {})

        path = self._fs.get_source_dir('assets/' + unquote(file).replace('../', '/').strip('/'))

        if not 'assets' + os.sep + os.path.normpath(config.get('root', 'media')) in path:
            self.add_message('error', 'Directory: permission denied')
            return path

        if os.path.isfile(path):
            try:
                os.remove(path)
                self.add_message('success', f'File "{os.path.basename(file)}" has been deleted')
            except PermissionError:
                self.add_message('error', 'Remove file: permission denied')

        if os.path.isdir(path) and not len(os.listdir(path)):
            try:
                os.rmdir(path)
                self.add_message('success', f'Folder "{os.path.basename(file)}" has been deleted')
            except PermissionError:
                self.add_message('error', 'Remove directory: permission denied')

        return path

    def _page_save(self, current_path) -> str:
        """
        Save the posted data in the page JSON data for the path (pages/{path}.json
        """
        if '_full_path' not in self._request:
            self.add_message('error', 'Page path is missing')
            return current_path
        if '_page_type' not in self._request:
            self.add_message('error', 'Page type is missing')
            return current_path

        config = self.get_config().get('form', {})

        if not config.get('actions', {}).get('save', False):
            self.add_message('error', 'Access denied')
            return current_path

        # Clean the page path
        page_type = self._request.get('_page_type')[0]
        page_extension = '.' + ('html' if page_type in ['md'] else page_type)
        new_path = self._format_path((self._request.get('_full_path')[0]).replace(page_extension, ''))
        if not new_path:
            self.add_message('error', 'Page path is empty')
            return current_path
        new_path += page_extension

        if not self._can_edit_page(new_path):
            self.add_message('error', 'The page cannot be edited')
            return current_path

        new_full_path = self._fs.get_page_config(new_path)
        current_full_path = self._fs.get_page_config(current_path)

        # Test if the new page path already exists
        if not current_path and os.path.exists(new_full_path):
            self.add_message('error', 'Page path already exists')
            return current_path

        # Test if the updated page path already exists
        if current_path and new_full_path != current_full_path and os.path.exists(new_full_path):
            self.add_message('error', 'Page path already exists')
            return current_path

        # Load JSON page data
        data = self._fs.merge_json([current_full_path])\
            if current_path and os.path.exists(current_full_path)\
            else json.loads('{}')

        # Loop in config fields and add it to JSON data if required
        for fieldset in config.get('fieldsets', []):
            for var, options in fieldset.get('fields', {}).items():
                if not options.get('save', True) or var not in self._request:
                    continue
                values = self._request[var]
                if options.get('type') in ['file', 'image']:
                    if var + '_remove' in self._request and self._request[var + '_remove'][0] == '1':
                        if data.get(var, None) and os.path.exists(self._fs.get_source_dir('assets/' + data[var])):
                            os.unlink(self._fs.get_source_dir('assets/' + data[var]))
                        data[var] = ''
                    path = self._save_file(values[0], options)
                    if path:
                        if data.get(var, None)\
                                and path != data[var]\
                                and os.path.exists(self._fs.get_source_dir('assets/' + data[var])):
                            os.unlink(self._fs.get_source_dir('assets/' + data[var]))
                        data[var] = path
                elif options.get('type') == 'multiselect':
                    data[var] = list(filter(None, values))
                elif options.get('type') == 'block':
                    data[var] = values[0].replace('\r\n', '\n')
                    extension = options.get('mode', 'html')
                    if extension[0] == '$':
                        extension = self._request.get(extension.lstrip('$'), ['html'])[0]
                    if extension == 'html':
                        code_elements = self.__extract_code(data[var])
                        for code in code_elements:
                            data[var] = data[var].replace(
                                '<code' + code.get('attr') + '>' + code.get('content') + '</code>',
                                '<code' + code.get('attr') + '>' + escape(code.get('content')) + '</code>'
                            )
                    save_dir = options.get('save_dir', '').strip('/')
                    content_file = os.path.splitext(new_path)[0] + '.' + extension
                    try:
                        self._fs.create_file(self._fs.get_source_dir(save_dir) + os.sep + content_file, data[var])
                    except PermissionError:
                        self.add_message('error', 'Save page content: permission denied')
                    data[var] = (save_dir + '/' if save_dir else '') + content_file
                else:
                    result = values[0] if options.get('allow_html', False) else escape(values[0], False)
                    result = result if options.get('line_break', True) else re.sub('\r\n|\n|\r', ' ', result)
                    data[var] = result

        # Remove the old page path if path has been updated
        if current_path and new_full_path != current_full_path:
            self._page_remove(current_path)

        # Save the JSON data
        try:
            self._fs.create_file(new_full_path, json.dumps(data, indent=2, ensure_ascii=False))
            self.add_message('success', 'The page has been saved')
        except PermissionError:
            self.add_message('error', 'Save page data: permission denied')

        return new_path

    def _media_save(self) -> None:
        """
        Adds a file or a directory
        """
        config = self.get_config().get('media', {})
        current = os.path.normpath(
            config.get('root', 'media').strip('/') + os.sep + self._request.get('directory', [''])[0].strip('/')
        )

        # Save the file in the current directory
        if self._request.get('media', [''])[0]:
            path = self._save_file(
                self._request.get('media', [''])[0],
                {'directory': current, 'label': 'Media', 'extensions': config.get('extensions', None)}
            )
            if path:
                self.add_message('success', 'The file has been uploaded')
            else:
                self.add_message('error', 'Unable to upload file')

        # Create a new directory in the current directory
        if self._request.get('folder', [''])[0]:
            name = self._format_path(self._request.get('folder')[0])
            if name:
                path = self._fs.get_source_dir('assets/' + current + os.sep + name).rstrip(os.sep)
                try:
                    Path(os.path.normpath(path)).mkdir(parents=True, exist_ok=True)
                    self.add_message('success', 'The folder has been created')
                except PermissionError:
                    self.add_message('error', 'Add a new folder: permission denied')
            else:
                self.add_message('error', 'Unable to create directory with this name')

    def _save_file(self, upload: dict, options: dict) -> str:
        """
        Save the file and return the path from the asset directory
        """
        if isinstance(upload, dict) and upload.get('filename', ''):
            file = self._format_path(upload.get('filename'), '[^0-9a-z.]')
            extension = self._fs.get_file_extension(file)
            if not options.get('extensions') or extension in options.get('extensions'):
                path = (options.get('directory', '').strip('/') + '/' + str(int(time.time())) + '-' + file).strip('/')
                try:
                    self._fs.create_directory(self._fs.get_source_dir('assets/' + path))
                    with open(self._fs.get_source_dir('assets/' + path), 'wb') as file:
                        file.write(upload.get('content'))
                    return path
                except PermissionError:
                    self.add_message('error', f'{options.get("label", "")}: permission denied')
                    return ''
            if extension:
                self.add_message('error', f'{options.get("label", "")}: "{extension}" is not allowed')
            else:
                self.add_message('error', f'{options.get("label", "")}: file extension is required')
        return ''

    def page_list(self) -> str:
        """
        List all the pages in a table
        """
        config = self.get_config().get('grid', {})

        # Load the pages
        pages = self._jq.fetch(config.get('query', ''), True)

        # Build the table head
        table_head = '<tr><th>Path</th>'
        for key, options in config.get('columns', {}).items():
            table_head += f'<th>{options.get("label", "")}</th>'
        table_head += '</tr>'

        # Build table body
        table_body = ''
        for page in pages:
            data = page[1]
            path = data['_full_path']
            if not self._can_edit_page(path):
                continue
            table_body += f'''
            <tr>
                <td class="path{" protected" if not self._can_edit_page(path) else ""}">
                    <a href="{self._editor_key}/page?edit={quote(path)}" class="pure-menu-link">{path}</a>
                </td>
            '''
            for key, options in config.get('columns', {}).items():
                value = data[key] if key in data else ""
                if 'options' in options:
                    for option in options['options']:
                        if 'values' in option and value in option['values']:
                            value = option['label']
                table_body += f'<td class="{key}"><span>{value}</span></td>'
            table_body += '</tr>'

        content = f'''
        <div>{self._block_list_actions(config)}<h1>Pages</h1></div>
        <div class="page-list">
            <table class="pure-table pure-table-bordered">
                <thead>{table_head}</thead>
                <tbody>{table_body}</tbody>
            </table>
        </div>
        '''

        return self.to_html(content, 'Editor - Pages')

    def _block_list_actions(self, config: dict) -> str:
        """
        Adds the action buttons on the list page
        """
        item = ''
        for action in config.get('actions', {}):
            data = ''
            for key, value in action.get('data', {}).items():
                data += f' data-{key}="{self.__protect(value)}" '
            item += f'''
            <li class="pure-menu-item">
                <a href="{self._editor_key}/{action.get("path", "")}" class="{action.get("class", "")}"{data}>
                    {action.get("label", "{label}")}
                </a>
            </li>
            '''
        if item:
            return f'<div class="pure-menu pure-menu-horizontal actions"><ul class="pure-menu-list">{item}</ul></div>'
        return ''

    def page_edit(self, page_path: str = None) -> str:
        """
        Build the page form
        """
        if not self._can_edit_page(page_path):
            self.add_message('error', 'The page cannot be edited')

        config = self.get_config().get('form', {})

        # Init and load the page data
        if page_path is not None:
            data = self._fs.get_page_data(page_path)
            data['_page_type'] = self._fs.get_file_extension(page_path)
        else:
            data = self._fs.get_page_data()

        # Build the form
        columns = {"left": "", "right": ""}
        for fieldset in config.get('fieldsets', []):
            if not self.__can_show_fieldset(fieldset.get('depends', {}), data):
                continue
            columns[fieldset.get('column', 'left')] += self.__build_fieldset(fieldset, page_path, data)

        two_columns = columns.get('right') and columns.get('left')
        l_c = 'pure-u-1' + (' pure-u-md-7-24' if two_columns else '') + (' hide' if not columns.get('left') else '')
        r_c = 'pure-u-1' + (' pure-u-md-17-24' if two_columns else '') + (' hide' if not columns.get('right') else '')

        content = f'''
        <form method="post"
            action="{self._editor_key}/page?edit={quote(page_path) if page_path else ""}"
            class="pure-form pure-form-stacked"
            enctype="multipart/form-data"
            id="edit_page"
            data-new="{"0" if page_path else "1"}">
            <h1>Page</h1>
            {self._block_form_actions(page_path, config)}
            <div class="pure-g">
                <div class="{l_c} left"><div class="left-content">{columns.get("left", "")}</div></div>
                <div class="{r_c} right"><div class="right-content">{columns.get("right", "")}</div></div>
            </div>
        </form>
        <script>
            editor.ajaxSend();
            editor.isSaved();
        </script>
        '''

        return self.to_html(content, f'Editor - {page_path if page_path else "New page"}')

    def page_media(self) -> str:
        """
        Display media page
        """
        config = self.get_config().get('media', {})

        current = self._request.get('directory', [''])[0].strip('/').replace('\\', '/')
        root = config.get('root', 'media').strip('/')

        directory = self._fs.get_source_dir('assets/' + root + '/' + current)

        if not os.path.isdir(directory):
            return self.to_html(
                f'<p><em>"{directory}"</em> directory does not exist. Create the directory to manage the media.</p>',
                'Editor - Media'
            )

        folders = ''
        files = sorted(Path(directory).iterdir(), key=os.path.getmtime, reverse=True)
        for folder in files:
            if not folder.is_dir():
                continue
            items = len(os.listdir(folder))
            dirpath = str(folder).replace(self._fs.get_source_dir('assets'), '')

            # Display remove link
            remove_html = ''
            if not items:
                remove_html = f'''
                <a href="{self._editor_key}/media?remove={quote(dirpath)}{"&directory=" + current if current else ""}"
                    class="remove" data-cy="delete-folder" data-filename="{quote(os.path.basename(dirpath))}"
                    onclick="javascript:return confirm('Are you sure you want to delete this folder?');">
                    <img src="{self._editor_key}/assets/trash.svg" alt="">
                </a>
                '''

            # Display item number
            count_html = f'<span>{items}</span>'
            if items:
                count_html = f'<span>{items} item{"s" if items > 1 else ""}</span>'

            param = quote((current + "/" if current else "") + folder.name)

            folders += f'''<div class="media-container folders pure-u-1-3 pure-u-sm-1-6 pure-u-lg-3-24 pure-u-xl-2-24">
                <div class="media-content">
                    <div class="media-file">
                        <a href="{self._editor_key}/media?directory={param}" class="preview" data-cy="folder-link"
                            style="background-image: url('{self._editor_key}/assets/folder.svg')"></a>
                    </div>
                    <div class="media-info">
                        <input class="pure-u-1" value="{escape(folder.name)}" readonly>
                        {count_html}
                        {remove_html}
                    </div>
                </div>
            </div>'''

        folders_html = ''
        if folders:
            folders_html = f'''<div class="pure-g">
                <div class="pure-u-1"><div class="media-list">{folders}</div></div>
            </div>'''

        media = ''
        for file in files:
            if not file.is_file() or file.name[0] == '.':
                continue

            filepath = str(file).replace(self._fs.get_source_dir('assets'), '').replace(os.sep, '/')
            extension = self._fs.get_file_extension(file.name)

            # Retrieve the file size
            stat = file.stat()
            file_size = str(round(stat.st_size / 1024, 2)) + ' kB'
            if stat.st_size >= 1000000:
                file_size = str(round(stat.st_size / (1024 * 1024), 2)) + ' MB'

            # The default file snippet content
            tip_html = f'<a href="{quote(filepath)}">{file.name}</a>'
            tip_md = f'[{file.name}]({quote(filepath)})'
            preview = f'{self._editor_key}/assets/file.svg'

            # File snippet content for images
            if extension in ['svg', 'jpg', 'jpeg', 'gif', 'png', 'webp', 'apng', 'avif']:
                tip_html = f'<img src="{quote(filepath)}" alt="Image description">'
                tip_md = f'![Image description]({quote(filepath)})'
                preview = quote(filepath)

            # Show snippets as configured
            snippets = []
            if 'filepath' in config.get('snippets', []):
                snippets.append(f'<input class="pure-u-1 clipboard" value="{escape(quote(filepath))}" readonly>')
            if 'html' in config.get('snippets', []):
                snippets.append(
                    f'<input class="pure-u-1 clipboard" value="{escape(tip_html)}" readonly data-cy="media-html">'
                )
            if 'markdown' in config.get('snippets', []):
                snippets.append(
                    f'<input class="pure-u-1 clipboard" value="{escape(tip_md)}" readonly data-cy="media-markdown">'
                )

            # Display file extension
            extension_html = ''
            if extension:
                background = self.__color_hexa(extension.lower())
                extension_html = f'''
                <span style="background:{background};color:{self.__color_contrast(background)}">
                    {extension.lower()}
                </span>
                '''

            # Display file size
            size_html = f'<span>{file_size}</span>'

            # Display remove link
            remove_html = f'''
            <a href="{self._editor_key}/media?remove={quote(filepath)}{"&directory=" + current if current else ""}"
                class="remove" data-cy="delete-file" data-filename="{quote(os.path.basename(filepath))}"
                onclick="javascript:return confirm('Are you sure you want to delete this file?');">
                <img src="{self._editor_key}/assets/trash.svg" alt="">
            </a>
            '''

            media += f'''<div class="media-container pure-u-1-2 pure-u-sm-1-3 pure-u-lg-6-24 pure-u-xl-4-24">
                <div class="media-content">
                    <div class="media-file">
                        <a href="{quote(filepath)}" class="preview"
                            style="background-image: url('{preview}')" target="_blank"></a>
                    </div>
                    <div class="media-info">
                        {extension_html}
                        {size_html}
                        {remove_html}
                    </div>
                    <div class="media-snippet">{"".join(snippets)}</div>
                </div>
            </div>'''

        files_html = ''
        if media:
            files_html = f'''<div class="pure-g">
                <div class="pure-u-1"><div class="media-list">{media}</div></div>
            </div>'''

        if not folders_html and not files_html:
            files_html = f'''<p class="message-info">
                The folder "{os.path.basename(root)}{"/" if current else ""}{current}" is empty.
            </p>'''

        breadcrumb = f'<a href="{self._editor_key}/media">{os.path.basename(root)}</a>'
        links = list(filter(None, current.split('/')))
        link_path = ''
        for link in links:
            link_path += quote(link + '/')
            breadcrumb += f'<a href="{self._editor_key}/media?directory={link_path.strip("/")}">{link}</a>'

        content = f'''
        <form method="post"
            action="{self._editor_key}/media{"?directory=" + current if current else ""}"
            class="pure-form"
            enctype="multipart/form-data"
            id="media_page">
            <h1>Media</h1>
            <p class="breadcrumb">{breadcrumb}</p>
            <div class="actions media-form">
                <input type="hidden" name="form_method" value="save">
                <div class="media-field-group">
                    <label for="media-folder">Folder:</label>
                    <input type="text" id="media-folder" name="folder" class="media-field" value="" data-cy="folder">
                </div>
                <div class="media-field-group">
                    <label for="media-file">File:</label>
                    <input type="file" id="media-file" name="media" class="media-field" data-cy="file">
                </div>
                <input type="submit" class="button-confirm pure-button" value="Add" data-cy="save">
            </div>
            <div class="media-content">
                {folders_html}
                {files_html}
            </div>
            <script>editor.copy();</script>
        </form>
        '''

        return self.to_html(content, 'Editor - Media')

    @staticmethod
    def __color_hexa(value: str) -> str:
        """
        Calculate hex color from string
        """
        return '#' + str(hex(zlib.crc32((str(value)).encode()) & 0xffffffff))[-6:]

    @staticmethod
    def __color_contrast(hexa: str) -> str:
        """
        Use white or black depending on the given color
        """
        color = hexa[1:]

        hexa_red = int(color[0:2], base=16)
        hexa_green = int(color[2:4], base=16)
        hexa_blue = int(color[4:6], base=16)

        luminance = hexa_red * 0.2126 + hexa_green * 0.7152 + hexa_blue * 0.0722

        if luminance < 140:
            return '#ffffff'
        return '#000000'

    def __build_fieldset(self, fieldset: dict, page_path: str, data: dict) -> str:
        """
        Build the fieldset
        """
        form = f'<fieldset><legend>{fieldset.get("label", "Fields")}</legend>'
        for var, options in fieldset.get('fields', {}).items():
            value = data[var] if var in data else ''
            if not self._can_edit_page(page_path) and not value:
                continue
            is_required = options.get('required', False)
            attributes = ' '.join([
                'disabled' if options.get('disabled', False) else '',
                'required' if is_required else '',
                'readonly' if options.get('readonly', False) else ''
            ]).strip()
            style = 'style="' + options.get("style").replace('"', "'") + '"' if options.get("style", False) else ''
            form += f'<div class="field pure-u-1{" hide" if options.get("hide", False) else ""}">'
            form += f'''
            <label for="i_{var}" id="l_{var}">
                {options.get("label", "Option")}{" <span>*</span>" if is_required else ""}
            </label>
            '''
            f_type = options.get('type', 'text')
            if f_type in ['text']:
                form += f'<input type="text" id="i_{var}" name="{var}" value="{self.__protect(str(value))}"' \
                        f' class="pure-u-1 i-reload" {attributes} {style}>'
            if f_type in ['file', 'image']:
                if value:
                    form += f'<input type="checkbox" value="1" name="{var}_remove" class="i-reload" id="r_{var}">' \
                            f'<label for="r_{var}" class="remove">Remove</label>'
                    if f_type == 'image':
                        form += f'<a href="/{value}" target="_blank" class="media">' \
                                f'<img src="/{value}" alt="{value}" height="70">' \
                                f'</a>'
                        form += f'<figcaption class="pure-u-1">{value}</figcaption>'
                    else:
                        form += f'<a href="/{value}" target="_blank" class="media">{value}</a>'
                form += f'<input type="file" id="i_{var}" name="{var}"' \
                        f' class="pure-u-1 i-reload" {attributes} {style}>'
            elif f_type in ['date']:
                form += f'<input type="date" id="i_{var}" name="{var}" value="{self.__protect(str(value))}"' \
                        f' class="pure-u-1 i-reload" {attributes} {style}>'
            elif f_type in ['textarea']:
                form += f'<textarea id="i_{var}" name="{var}"' \
                        f' class="pure-u-1 i-reload" {attributes} {style}>{self.__protect(str(value))}</textarea>'
            elif f_type in ['select', 'multiselect']:
                multiple = 'multiple' if f_type == 'multiselect' else ""
                form += f'<select id="i_{var}" name="{var}" class="pure-u-1 i-reload" {multiple} {attributes} {style}>'
                form += '<option value="">&nbsp;</option>'
                for option in options.get('options', []):
                    values = [str(value)] if not multiple else value
                    selected = 'selected="selected"' if str(option.get('value')) in values else ''
                    form += f'<option value="{self.__protect(str(option.get("value", "")))}" {selected}>' \
                            f'{str(option.get("label", ""))}' \
                            '</option>'
                form += '</select>'
            elif f_type in ['block']:
                file = None
                if value:
                    file = self._fs.get_source_dir(value)
                    if os.path.exists(file):
                        with open(os.path.normpath(file), 'r', encoding=self._fs.get_encoding()) as content:
                            value = content.read()
                            if self._fs.get_file_extension(file) == 'html':
                                code_elements = self.__extract_code(value)
                                for code in code_elements:
                                    value = value.replace(
                                        '<code' + code.get('attr') + '>' + code.get('content') + '</code>',
                                        '<code' + code.get('attr') + '>' + unescape(code.get('content')) + '</code>'
                                    )
                form += f'''
                <textarea class="pure-u-1" id="i_{var}" name="{var}" {attributes}>{escape(str(value))}</textarea>
                <span class="pure-form-message">
                    <span>Ctrl-F / Cmd-F:</span> Start searching<br>
                    <span>Ctrl-G / Cmd-G:</span> Find next<br>
                    <span>Shift-Ctrl-G / Shift-Cmd-G:</span> Find previous<br>
                    <span>Alt-G:</span> Jump to line<br><br>
                </span>
                <script>
                    editor.initBlock(
                        "i_{var}",
                        "{options.get("mode", "html")}",
                        "{self._fs.get_file_extension(file) if file else ""}",
                        {"true" if options.get("focus", False) else "false"}
                    );
                </script>
                '''
            form += '</div>'
        form += '</fieldset>'
        return form

    @staticmethod
    def __extract_code(content: str) -> list:
        """
        Retrieve all code elements with attributes in the content
        """
        search = re.compile(r'<code(.*?)>(.*?)</code>', re.IGNORECASE | re.DOTALL).finditer(content)
        result = []
        for element in search:
            code = element.groups()
            result.append({'attr': code[0], 'content': code[1]})
        return result

    @staticmethod
    def __protect(value: str) -> str:
        """
        Protect the value by replacing special characters to HTML-safe sequences
        """
        return escape(unescape(value))

    @staticmethod
    def __can_show_fieldset(depends: dict, data: dict) -> bool:
        """
        Whether field set can be displayed based on field dependencies
        """
        can_show = True
        for depend in depends:
            if not depend.get('field') in data:
                can_show = False
            else:
                to_match = data[depend.get('field')]
                if not isinstance(to_match, list):
                    to_match = [to_match]
                if not any(item in to_match for item in depend.get('values')):
                    can_show = False
        return can_show

    def _block_form_actions(self, page_path: str or None, config: dict) -> str:
        """
        Menu with actions on the form page
        """
        actions = config.get('actions', {})
        menu = ''
        if actions.get('back', False):
            menu += f'<li class="pure-menu-item"><a href="{self._editor_key}/" class="pure-button">Back</a></li>'
        if actions.get('reset', False):
            menu += f'''
            <li class="pure-menu-item">
                <a href="{self._editor_key}/page?edit={quote(page_path) if page_path else ""}" class="pure-button">
                    Reset
                </a>
            </li>
            '''
        if page_path:
            if actions.get('data', False):
                menu += f'''
                <li class="pure-menu-item">
                    <a href="/_page/{page_path}" class="button-secondary pure-button" target="_blank">Data</a>
                </li>
                '''
            if actions.get('view', False):
                menu += f'''
                <li class="pure-menu-item">
                    <a href="/{page_path}" class="button-secondary pure-button" target="_blank" data-cy="view">View</a>
                </li>
                '''
        if page_path and self._can_edit_page(page_path) and actions.get('delete', False):
            menu += f'''
            <li class="pure-menu-item">
            <a href="{self._editor_key}/page?edit={quote(page_path)}&remove=1" 
                class="button-warning pure-button" data-cy="delete"
                onclick="javascript:return confirm('Are you sure you want to delete this page?');">Delete</a>
            </li>
            '''
        if self._can_edit_page(page_path) and actions.get('save', False):
            menu += f'''
            <li class="pure-menu-item">
                <input type="hidden" name="form_method" value="save">
                <input type="submit" class="button-confirm pure-button" value="Save" data-cy="save">
            </li>
           '''
        if not menu:
            return ''
        return f'''
        <div class="pure-menu pure-menu-horizontal actions">
            <span class="warning" id="warning_message" data-cy="warning"></span>
            <ul class="pure-menu-list">{menu}</ul>
        </div>
        '''

    def _block_head_stylesheets(self) -> str:
        """
        Stylesheets
        """
        links = [
            self._editor_key + '/assets/pure.css',
            self._editor_key + '/assets/codemirror.css',
            self._editor_key + '/assets/editor.css'
        ]
        stylesheets = ''
        for css in links:
            stylesheets += f'<link rel="stylesheet" href="{css}">'
        return stylesheets

    def _block_head_scripts(self) -> str:
        """
        Scripts
        """
        links = [
            self._editor_key + '/assets/codemirror.js',
            self._editor_key + '/assets/editor.js'
        ]
        scripts = ''
        for script in links:
            scripts += f'<script src="{script}"></script>'
        return scripts

    def _block_messages(self) -> str:
        """
        Messages block
        """
        html = ''
        success = self.get_messages('success')
        if success:
            html += '<div class="system-message success" data-cy="message-success">'
            html += '<br><br>'.join(success)
            html += '</div>'
        errors = self.get_messages('error')
        if errors:
            html += '<div class="system-message error" data-cy="message-error">'
            html += '<br><br>'.join(errors)
            html += '</div>'
        if errors or success:
            html += '<script>editor.messages();</script>'
        return html

    def to_html(self, content, title: str = 'Editor', custom_head: str = '') -> str:
        """
        The editor page template
        """
        html = f'''
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta name="robots" content="noindex,nofollow">
                <title>{title}</title>
                {self._block_head_scripts()}
                {self._block_head_stylesheets()}
                {custom_head}
            </head>
            <body>
                {self._block_header()}
                <div id="system-messages">{self._block_messages()}</div>
                <main>{content}</main>
            </body>
        </html>
        '''
        return self._clean_html(html)

    def _block_header(self) -> str:
        """
        Editor header HTML content
        """
        media_link = ''
        if self.get_config().get('media', False):
            media_link = f'<li><a href="{self._editor_key}/media">Media</a></li>'
        return f'''
        <header>
            <div class="header-content pure-g">
                <div class="pure-u-1-2 pure-u-md-1-3">
                    <ul>
                        <li><a href="{self._editor_key}">Pages</a></li>
                        {media_link}
                        <li><a href="/" target="_blank">Site</a></li>
                    </ul>
                </div>
                <div class="pure-u-1-2 pure-u-md-1-3">
                    <div class="switcher">{self._editor_switcher()}</div>
                </div>
                <div class="pure-u-1-3 desktop">
                    <div class="info">
                        <span>Stapy {self._fs.get_version()}</span> &bull; <span>Editor {VERSION}</span>
                    </div>
                </div>
            </div>
        </header>
        '''

    def _editor_switcher(self) -> str:
        """
        Editor config switcher HTML content
        """
        switcher = self.get_config().get('editor_switcher', {})
        options = ''
        for label, key in switcher.items():
            link = self._editor_key.replace(self._editor_key, key, 1)
            if self._request.get('edit', False):
                link += f'/page?edit={self._request.get("edit")[0]}'
            options += f'<a href="{link}" class="{"current" if self._editor_key == key else ""}">{label}</a>'
        return options

    def _can_edit_page(self, page_path: str or None) -> bool:
        """
        Test if the given page path can be edited
        """
        if not page_path:
            return True
        pages = self.get_config().get('protected_pages', [])
        for path in pages:
            if re.match(path, page_path):
                return False
        return True

    @staticmethod
    def _string_to_tuple(string: str) -> tuple or None:
        """
        Convert the string to tuple
        """
        return tuple(item for item in string.split(':')) if string else None

    @staticmethod
    def _format_path(path: str, replace_regex: str = '[^0-9a-z/]+') -> str:
        """
        Format the page path into a regular allowed path
        """
        path = path.lstrip('/')
        path = path.lower()
        nfkd_form = unicodedata.normalize('NFKD', path)
        path = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        path = re.sub(replace_regex, '-', path)
        path = path.strip('-')
        return path

    @staticmethod
    def _clean_html(content: str) -> str:
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
