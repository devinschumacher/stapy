# Editor

The editor is an official Stapy plugin. Use it to more easily write page data and content.

The editor is built with [Pure CSS](https://purecss.io/) and [CodeMirror](https://codemirror.net/).

When server is running, enter the following URL to access the editor:

```
http://127.0.0.1:1985/_editor
```

## Demo

An online demo of the editor is available: [Stapy Editor demo](https://demo.stapy.net/_editor)

**Note**: You are not allowed to edit, save or delete.

## Configuration

The editor configuration file is located in the `source` directory.

```
source
+----- editor.json
```

**Note:** There is a fallback to the `editor.json` file in `plugins/editor` directory if not exists in `source`.

### Editor path

The default editor path key is `_editor`. This is set by the first parent key in the JSON data configuration:

```
{
  "_editor": {
    ...
  }
}
```

```
http://127.0.0.1:1985/_editor
```

Multiple editor paths with specific configuration are allowed:

```
{
  "_editor_posts": {
    ...
  },
  "_editor_static": {
    ...
  },
}
```

**Note:** the editor path key is case-sensitive.

### Protected pages

The "**protected_page**" config prevents access to the page. The page will not appear in the list and cannot be edited.

Add the page paths in the list, regex is allowed. Example:

```
{
  "_editor": {
    "protected_pages": [
      "robots.txt",
      "sitemap.xml",
      "secret/(.*)"
    ],
    ...
  }
}
```

### Switcher

The switcher config adds links in the header to switch between editor paths.

```
{
  "_editor": {
    "editor_switcher": {
      "Full": "/_editor",
      "Content": "/_editor_c"
    },
    ...
  }
}
```

### Media

The media config is used for the Media management page.

| Option     | Description                                        | Excepted  | Default |
|------------|----------------------------------------------------|-----------|---------|
| root       | The root folder relative to the "assets" directory | str       | media   |
| snippets   | The media snippets to display                      | Array     | []      |
| extensions | Extensions the user is allowed to upload           | Array     | None    |

```
{
  "_editor": {
    "media": {
      "root": "media",
      "snippets": ["filepath", "html", "markdown"],
      "extensions": ["svg" ,"png", "jpg", "jpeg", "gif", "webp", "apng", "avif"]
    },
    ...
  }
}
```

**Note:** If the "**media**" config path is missing, the Media page will be disabled.

### Grid

#### Columns

Choose the columns you want to display in the grid with the **grid > columns** config. You can set options for a list of defined values.

| Option  | Description    | Excepted  | Default |
|---------|----------------|-----------|---------|
| label   | Column label   | str       |         |
| options | Defined values | Array     |         |

```
{
  "_editor": {
    ...
    "grid": {
      "columns": {
        "title": {
          "label": "Title"
        },
        "enabled": {
          "label": "Enabled",
          "options": [
            {
                "values": ["", "1", 1, true],
                "label": "Yes"
            },
            {
                "values": ["0", 0, false],
                "label": "No"
            }
          ]
        }
      },
      ...
    },
    ...
  }
}
```

#### Query

A JSON query is made to get the list of pages. Set the Query with **grid > query**.

```
{
  "_editor": {
    ...
    "grid": {
      ...
      "query": "SELECT ITEMS WHERE 'post' in tags ORDER BY date desc"
    },
    ...
  }
}
```

#### Actions

An array containing the actions to display in the grid.

| Option | Description                 | Excepted  | Default |
|--------|-----------------------------|-----------|---------|
| path   | The page path               | str       |         |
| class  | The link element class name | str       |         |
| label  | The link element label      | str       | {label} |
| data   | The link data attributes    | Object    | {}      |

```
{
  "_editor": {
    ...
    "grid": {
      ...
      "actions": [
        {
          "path": "build/",
          "class": "button-secondary pure-button",
          "label": "Build"
        },
        {
          "path": "add/",
          "class": "pure-button pure-button-primary",
          "label": "Add",
          "data": {
            "cy": "add"
          }
        }
      ],
    },
    ...
  }
}
```

### Form

#### Actions

Enables or disables form page actions.

```
{
  "_editor": {
    ...
    "form": {
      "actions": {
        "back": true,
        "reset": true,
        "data": true,
        "view": true,
        "delete": true,
        "save": true
      },
      ...
    }
  }
}
```

#### Fieldsets

The form has one or more fieldsets. Set the fieldset objects in **form > fieldsets**.

| Option  | Description          | Excepted       | Default |
|---------|----------------------|----------------|---------|
| label   | Label                | str            | Fields  |
| column  | Position in the form | left, right    | left    |
| depends | Dependencies         | Array or false | false   |
| fields  | Fields               | Object         | {}      |

The "**depends**" config allows the fieldset to be displayed only when another option is selected. This is useful for defining specific fields for a page.

```
{
  "_editor": {
    ...
    "form": {
      "fieldsets": [
        {
          "label": "SEO",
          "column": "left",
          "depends": [
            {
              "field": "_page_type",
              "values": ["html"]
            }
          ],
          "fields": {
          }
        },
        ...
      ]
    }
    ...
  }
}
```

In this example, SEO fieldset appears in the left column only when the **\_page\_type** field is set to **html**. Refresh the form to update dependencies.

The fieldset position in the form is the same as the fieldset position in the configuration.

#### Fields

A fieldset has one or more fields. Set the field objects in  **form > fieldsets > fields**.

| Option     | Description                                   | Excepted                                                      | Default |
|------------|-----------------------------------------------|---------------------------------------------------------------|---------|
| label      | Label                                         | str                                                           | Option  |
| required   | Field is required                             | bool                                                          | false   |
| disabled   | Field is disabled                             | bool                                                          | false   |
| readonly   | Field is in Read-Only mode                    | bool                                                          | false   |
| style      | Field inline style                            | str                                                           |         |
| save       | Must be saved in the page data                | bool                                                          | true    |
| hide       | Dot not display the field                     | bool                                                          | false   |
| type       | Field type                                    | text, textarea, date, select, multiselect, image, file, block | text    |
| allow_html | Allow HTML elements (do not escape)           | bool                                                          | false   |
| line_break | Allow line break (replaced by a space if not) | bool                                                          | true    |
| options    | Options for select or multiselect             | Array                                                         | \[\]    |
| mode       | Editor mode for block type                    | html, md, xml, css, js, json, ${field_id}                     | html    |
| directory  | Directory of files in assets (file, image)    | text                                                          |         |
| extensions | Allowed file extensions (file, image)         | Array                                                         | None    |
  
```
{
  "_editor": {
    ...
    "form": {
      "fieldsets": [
        {
          ...
          "fields": {
            "title": {
              "label": "Title",
              "required": true,
              "type": "text"
            },
            "description": {
              "label": "Description",
              "type": "textarea",
              "style": "min-height:100px",
              "line_break": false
            },
            "picture": {
              "label": "Picture",
              "type": "image",
              "directory": "media",
              "extensions": ["png", "jpg", "jpeg", "gif", "webp"]
            },
            "tags": {
              "label": "Tags",
              "type": "multiselect",
              "options": [
                {
                  "value": "post",
                  "label": "Post"
                },
                {
                  "value": "sitemap",
                  "label": "Sitemap"
                },
                {
                  "value": "menu",
                  "label": "Menu"
                }
              ]
            },
            "inline_css": {
              "label": "CSS",
              "type": "block",
              "mode": "css",
              "save_dir": "content/css"
            }
          }
        },
        ...
      ]
    }
    ...
  }
}
```

The block type content is saved in a file in the specified directory, and will be displayed with the \{% %\} tag:

```html
<style>
{% inline_css %}
</style>
```