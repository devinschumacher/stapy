let editor = {
    warningFlag: false,

    /**
     * Display System Messages
     */
    messages: function () {
        const messages = document.getElementsByClassName('system-message');
        for (let i = 0; i < messages.length; i++) {
            setTimeout(function() {
                messages[messages.length - 1].remove();
            }, 3000 + (i * 3000));
        }
    },

    /**
     * Init a type block field
     *
     * @param {string} elementId: textarea identifier
     * @param {string} mode: default code editor language (html, md, xml, css, js, json...) or selector id
     * @param {string} extension: file extension
     * @param {boolean} focus: focus on the editor textarea on load
     */
    initBlock: function (elementId, mode, extension, focus) {
        const editor = this;
        const textarea = document.getElementById(elementId);
        const width = textarea.offsetWidth;
        const content = CodeMirror.fromTextArea(
            textarea,
            {lineNumbers: true, lineWrapping: true, indentWithTabs: false, tabSize: 2}
        );
        content.on('change', function () {
            if (!editor.warningFlag) {
                const warning = document.getElementById('warning_message');
                if (warning) {
                    warning.innerText = 'There are unsaved changes.';
                    editor.warningFlag = true;
                }
            }
        });
        textarea.nextSibling.style.width = width + 'px';
        if (focus) {
            content.focus();
        }
        const modes = {html: 'htmlmixed', md: 'markdown', xml: 'xml', css: 'css', js: 'javascript', json: 'javascript'};
        content.setOption('mode', typeof modes[mode] !== 'undefined' ? modes[mode] : null);
        if (mode.charAt(0) === '$') {
            const types = document.getElementById(mode.replace('$', 'i_'));
            if (!types && extension) {
                content.setOption('mode', typeof modes[extension] !== 'undefined' ? modes[extension] : null);
            }
            if (types) {
                const label = document.getElementById(elementId.replace('i_', 'l_'));
                const labelText = label.innerText;
                if (extension) {
                    types.value = extension;
                }
                label.innerText = types.options[types.selectedIndex].innerText || labelText;
                content.setOption('mode', typeof modes[types.value] !== 'undefined' ? modes[types.value] : null);
                types.addEventListener('change', function () {
                    content.setOption('mode', typeof modes[this.value] !== 'undefined' ? modes[this.value] : null);
                    label.innerText = this.options[this.selectedIndex].innerText || labelText;
                });
            }
        }
    },

    /**
     * Save content in Ajax
     */
    ajaxSend: function () {
        const editor = this;
        const form = document.getElementById('edit_page');
        if (form && form.getAttribute('data-new') === '0') {
            let ajax = true;
            const fields = document.getElementsByClassName('i-reload');
            for (let i = 0; i < fields.length; i++) {
                fields[i].addEventListener('change', function (event) {
                    ajax = false;
                });
            }
            form.addEventListener('submit', function (event) {
                if (ajax) {
                    event.preventDefault();
                    fetch(form.action + '&ajax=1', {
                        method: form.method,
                        body: new FormData(form)
                    }).then(function(response) {
                        return response.text();
                    }).then(function(html) {
                        const warning = document.getElementById('warning_message');
                        if (warning) {
                            warning.innerText = '';
                            editor.warningFlag = false;
                        }
                        document.getElementById('system-messages').innerHTML = html;
                        const messages = document.getElementsByClassName('system-message');
                        setTimeout(function() {
                            for (var i = 0; i < messages.length; i++) { messages[i].remove(); }
                        }, 3000);
                    });
                }
            });
        }
    },

    /**
     * Display a warning message when changes are not saved
     */
    isSaved: function () {
        const editor = this;
        const form = document.getElementById('edit_page');
        if (form) {
            form.addEventListener('input', function (event) {
                if (!editor.warningFlag) {
                    const warning = document.getElementById('warning_message');
                    if (warning) {
                        warning.innerText = 'There are unsaved changes.';
                        editor.warningFlag = true;
                    }
                }
            });
        }
    },

    /**
     * Copy input element content with class "clipboard"
     */
    copy: function () {
        const fields = document.getElementsByClassName('clipboard');

        for (let i = 0; i < fields.length; i++) {
            fields[i].addEventListener('click', function (event) {
                event.target.select();
                if (!navigator.clipboard) {
                    document.execCommand('copy');
                    isCopied(event.target);
                } else {
                    navigator.clipboard.writeText(event.target.value).then(
                        function () {
                            isCopied(event.target);
                        }
                    );
                }
            });
        }

        function isCopied(element) {
            const copied = document.createElement('div');
            copied.className = 'copied';
            copied.innerText = 'Copied!'
            element.parentNode.insertBefore(copied, element);

            setTimeout(function() {
                element.parentNode.removeChild(copied);
            }, 1000);
        }
    }
}
