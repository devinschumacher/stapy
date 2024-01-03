# Changelog

## 1.17.12

- Behavior on unsolicited environments during build
- Allow specifying environments in the build script

## 1.17.11

- Allow adding environments to build in command parameters
- Allow rewriting Stapy tools CSS
- Editor CodeMirror updated to 5.65.15
- Editor textarea avoid horizontal resizing
- Editor new "inline style" option for fields
- Editor new "line break" option for fields

## 1.17.10

- Custom HTTP headers
- Safe mode to hide error messages on a remote server
- Editor CodeMirror updated to version 5.65.14
- Full CodeMirror JS minified (-83ko)

## 1.17.9

- Allow plugin in subdirectories
- Do not strip spaces in textarea
- Allow special chars in file path
- Editor media manager
- Editor code readability
- Editor CSS and JS outside the plugin script
- Editor warning message when changes are not saved
- Editor edit and remove pages logic updated

## 1.17.8

- Ability to use the editor offline
- File type retrievement updated
- Allow to cancel parent template

## 1.17.7

- Fix post data encoding

## 1.17.6

- Use of email module instead of deprecated cgi to parse multipart data
- Fix editor reset button path on new page
- Editor CodeMirror updated to 5.65.13

## 1.17.5

- Allow to post multipart/form-data
- Clean unknown vars in plugin and template tags
- New image and file types in editor
- Fix empty value in tag args when encode

## 1.17.4

- Fix Pymdown extension dependency

## 1.17.3

- Generate token for asset file based on update date
- Stapy toolkit added
- Do not convert markdown from the "assets" directory

## 1.17.2

- Fix plugin always reloading after an update
- Unique token available when building
- Reload plugins before matching reserved requests

## 1.17.1

- Allow to dispatch new plugin events in plugins
- Fix multiple message display in editor
- Scope of methods updated in editor plugin

## 1.17.0

- Advanced JSON query
- Custom query data cache policy with a new plugin
- Pages data logic updated
- Implemented new plugin system logic
- Serve on 127.0.0.1 to avoid resolving localhost
- New plugin events: http_request_initialized and http_request_sent
- Blue background for a page not found

## 1.16.5

- Fix double encoding in template tags
- Escape content tag included in template tags

## 1.16.4

- Fix isolated quoted string in tags

## 1.16.3

- New Stapy theme
- Current page data in child_content_data and child_content_query_result plugins
- Allow simple quote in tag arg values

## 1.16.2

- Markdown plugin added
- Editor switcher
- Editor edit page actions restriction

## 1.16.1

- Editor code char replacement improvements for HTML files

## 1.16.0

- Page editor plugin added
- Share objects for performance improvements
- Exit although all created threads are not closed
- Serve from custom host
- Catch ConnectionResetError exception

## 1.15.4

- Allow to send a custom HTTP response
- Json query and generator objects shared in all plugins
- Fix load of non script file in plugins directory
- Fix sort order with missing data
- Default template when missing, with the block "content"
- Fix full date with wrong format
- Fix minifier when css is not a physical file

## 1.15.3

- Do not force line break after each block

## 1.15.2

- Updated code style as recommended by Pylint
- Default JSON query limit updated

## 1.15.1

- Woodpecker CI/CD pipeline added
- Specify the name of the plugin where to execute the method

## 1.15.0

- Full rewrite of the parser to allow multi-line expressions

## 1.14.5

- Allow adding arguments in a child block
- Escape curly brace in template

## 1.14.4

- Post date format plugin added
- JSON query block separator option added

## 1.14.3

- Better error messages
- Plug & Play plugin system

## 1.14.2

- Allow to disable a page

## 1.14.1

- Fix colons in arguments

## 1.14.0

- Allow to build website offline with command line
- Auto-build system removed
- Useless cache system removed
- file_copy_before and file_copy_after events removed
- DELETE, PUT and POST HTTP methods removed
- Crawler removed
- Server script renamed to "stapy.py"

## 1.13.7

- Plugin method arguments as optional

## 1.13.6

- Child block parsing improvement

## 1.13.5

- Allow to add custom arguments in a plugin method

## 1.13.4

- Code style
- Avoid to remove .gitkeep file
- tmp extension added in temporary minified CSS file

## 1.13.3

- Theme related post added
- Default theme improvements

## 1.13.2

- JSON query cache removed

## 1.13.1

- Fix minified file deletion in cssmin plugin
- Crawler performance improvement

## 1.13.0

- New plugin tag in template
- Theme element page added
- Dedicated plugin class
- Force to reload plugin before generate a page

## 1.12.3

- New default plugin for multi-pages

## 1.12.2

- Do not serve configuration file without extension

## 1.12.1

- JSON block name updated

## 1.12.0

- Allow to use JSON value in block tags
- Built-in CSS minifier without dependency
- Always load directory files in alphabetical order

## 1.11.2

- HTML tidy plugin added
- Default theme menu plugin added

## 1.11.1

- Code style improvement
- Doctype added in error template

## 1.11.0

- Welcome message added in console
- Error messages improvement

## 1.10.6

- Better error messages

## 1.10.5

- Allow to update child block template from plugin
- File System class added to plugins args
- Protected methods logic updated
- New event for update JSON single page data

## 1.10.4

- New event for update JSON query page data
- Do not remove .gitignore when deleting files

## 1.10.3

- Reserved _env variable added

## 1.10.2

- Default site content updated

## 1.10.1

- New cache system for performance improvement

## 1.10.0

- Allow default configuration for subdirectories
- Default JSON configuration moved to layout directory

## 1.9.3

- Replace tag by an empty string for None or False value

## 1.9.2

- Fix wrong plugin script name

## 1.9.1

- Type hints added (PEP 484)

## 1.9.0

- Plugin system added

## 1.8.0

- New default theme

## 1.7.2

- Do not delete protected files during the crawl

## 1.7.1

- Fix JSON query sort order with integer

## 1.7.0

- Common JSON configuration for all file type (common.json)

## 1.6.2

- JSON query tag

## 1.6.1

- Allow to run local without the "web" directory

## 1.6.0

- Resources directory renamed from "web" to "assets"
- Bash crawler replaced by an improved Python crawler
- Crawl speed improvement on Windows
- Unit test implementation
- Default JSON configuration according to file type
- Default page path variable added
- Use specific page data in block
- Reserved route added to retrieve all pages
- Reserved route added to retrieve page data
- Reserved route added to retrieve environments
- Default robots.txt added
- Default sitemap.xml added
- Force encoding to UTF-8
- Allow to serve any type of file
- HEAD request added to generate a page
- PUT request to copy all resources
- POST request to create files in specific environment
- DELETE request to remove built site

## 1.5.1

- Ignore file writing broken pipe error

## 1.5.0

- "build" directory renamed to "source"
- Default generic theme

## 1.4.2

- Print error messages in console without all backtrace

## 1.4.1

- Automatic file mime type assignation
- Default theme improvements

## 1.4.0

- Multi-environments

## 1.3.0

- Global page configuration in default.json
- Force JSON file encoding
- Normalize path for Windows
- Do not serve over SSL
- File system improvements
- Code refactoring
- Crawler timer added

## 1.2.2

- Recursive parse in blocks
- Theme style minor improvements
- Multilanguage for default theme

## 1.2.1

- Replace var with empty text for boolean value
- Default theme page 404 added

## 1.2.0

- Block inclusion with curly-brace percent expression

## 1.1.3

- Multiple thread to avoid resource latency

## 1.1.2

- Page crawler added
- Build directory moved to root

## 1.1.1

- Error messages improvement

## 1.1.0

- HTTP response code refactoring
- Fix page path for index.html in subdirectories

## 1.0.0

- First stable release