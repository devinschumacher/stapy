#!/bin/bash

dir="$( cd "$( dirname "$0" )" && pwd )/"

rm "${dir}pure.css" 2> /dev/null
rm "${dir}codemirror.css" 2> /dev/null
rm "${dir}codemirror.js" 2> /dev/null

wget -O "${dir}pure.css" \
https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css \
https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/grids-responsive-min.css

wget -O "${dir}codemirror.css" \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/dialog/dialog.min.css

wget -O "${dir}codemirror.js" \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/search/search.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/search/searchcursor.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/search/jump-to-line.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/dialog/dialog.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/xml/xml.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/javascript/javascript.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/htmlmixed/htmlmixed.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/markdown/markdown.min.js \
https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/css/css.min.js
