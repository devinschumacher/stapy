/**
 * Copyright (c) 2023, Magentix
 * This code is licensed under simplified BSD license
 */

var stapy = {
    /**
     * Open a modal
     *
     * @param {string} content
     * @param {string} className
     */
    modal: function (content, className) {
        var stapy = this;
        stapy.overlay();

        var modal = document.createElement('div');
        var inner = document.createElement('div');
        var close = document.createElement('a');

        modal.className = 'modal to-close';
        if (typeof className !== 'undefined') {
            if (className) {
                modal.className += ' ' + String(className);
            }
        }

        close.className = 'modal-close close-modal-event';
        close.innerHTML = '<span>Close</span>';
        close.href = '#';

        inner.className = 'modal-inner';
        inner.innerHTML = content;

        modal.appendChild(close);
        modal.appendChild(inner);

        document.body.appendChild(modal);

        /* Allow to use CSS transitions */
        setTimeout(function () {
            modal.className = modal.className + ' modal-active';
        }, 10);

        /* Warning: for CSP style-src rule without unsafe-inline, use CSS3 Transform translateY instead. */
        modal.style.top = 'calc(50% - ' + ((Math.round(modal.offsetHeight * 100) / 100) / 2) + 'px)';
        if (modal.offsetHeight >= window.innerHeight) {
            modal.style.top = '20px';
            modal.style.bottom = '20px';
        }

        var closeEvents = document.getElementsByClassName('close-modal-event');
        for (var i = 0; i < closeEvents.length; i++) {
            closeEvents.item(i).addEventListener('click', function (event) {
                event.preventDefault();
                stapy.close();
            });
        }
    },

    /**
     * Loader
     *
     * @param {bool} status
     */
    loader: function (status) {
        if (status) {
            this.overlay();
            var loader = document.createElement('div');
            loader.className = 'loader to-close';
            document.body.appendChild(loader);
        } else {
            this.close();
        }
    },

    /**
     * Add the overlay
     */
    overlay: function () {
        var stapy = this;
        var overlay = document.createElement('div');
        overlay.className = 'overlay to-close';
        overlay.addEventListener('click', function (event) {
            stapy.close();
        });
        document.body.appendChild(overlay);
    },

    /**
     * Close all elements
     */
    close: function () {
        var toClose = document.querySelectorAll('.to-close');
        for (var i = 0; i < toClose.length; i++) {
            toClose[i].parentNode.removeChild(toClose[i]);
        }
    },

    /**
     * Retrieve form data as object
     *
     * @param {HTMLFormElement} form
     * @returns {Object}
     */
    formData: function (form) {
        var data = {}
        var elements = form.querySelectorAll('input,select,textarea');
        for (var i = 0; i < elements.length; i++) {
            if (!elements[i].name) {
                continue;
            }
            if (elements[i].hasAttribute('multiple')) {
                var options = elements[i].options;
                var values = [];
                for (var j = 0; j < options.length; j++) {
                    if (options[j].selected) {
                        values.push(options[j].value || options[j].text);
                    }
                }
                data[elements[i].name] = values;
            } else if (elements[i].type === 'radio') {
                if (!data.hasOwnProperty(elements[i].name)) {
                    data[elements[i].name] = '';
                }
                if (elements[i].checked) {
                    data[elements[i].name] = elements[i].value;
                }
            } else if (elements[i].type === 'checkbox') {
                data[elements[i].name] = elements[i].checked ? elements[i].value : '';
            } else {
                data[elements[i].name] = elements[i].value;
            }
        }
        return data;
    }
}
