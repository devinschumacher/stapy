# Stapy - Toolkit

Useful Javascript toolkit to save time. Designed to work with old browsers, from:

- Internet Explorer 9 (2011)
- Firefox 16 (2012)
- Safari 6.1 (2012)
- Chrome 26 (2013)
- Opera 15 (2013)

## Installation

```html
<link rel="stylesheet" href="stapy.css" />
```

```html
<script type="text/javascript" src="stapy.js"></script>
```

## Tools

### Modal

**Description:** Open a modal with overlay.

```javascript
stapy.modal([string content], [string className]);
```

**Example:**

```javascript
stapy.modal('Modal Content', 'info center');
```

### Loader

**Description:** A full screen loader.

```javascript
stapy.loader([bool status]);
```

**Example:**

```javascript
stapy.loader(true);
setTimeout(function () {
    stapy.loader(false);
}, 1000);
```

### Form Data

**Description:** Build a set of key/value pairs representing form fields and their values.

```javascript
stapy.formData([HTMLFormElement form]);
```

**Example:**

```javascript
var form = document.getElementById('my-form');
var data = stapy.formData(form);
```