/**
 * aras_code_editor.js
 * 
 * Integrates Ace Editor into Aras Admin forms for specific fields.
 * Targets fields: code, formula, layout_json, config_json, payload_json.
 */

(function() {
    "use strict";

    // Load Ace Editor from CDN if not already loaded
    function loadAce(callback) {
        if (window.ace) {
            callback();
            return;
        }
        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.2/ace.js';
        script.onload = function() {
            // Load some common modes/themes
            var modes = ['python', 'json', 'javascript', 'html', 'css'];
            var loaded = 0;
            
            function checkDone() {
                loaded++;
                if (loaded >= modes.length) {
                    // Give a small delay for themes/modes to actually be available in ace object
                    setTimeout(callback, 100);
                }
            }

            modes.forEach(function(mode) {
                var s = document.createElement('script');
                s.src = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.2/mode-' + mode + '.js';
                s.onload = checkDone;
                s.onerror = checkDone; // Still proceed even if a mode fails
                document.head.appendChild(s);
            });
            
            var theme = document.createElement('script');
            theme.src = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.2/theme-monokai.js';
            document.head.appendChild(theme);
        };
        script.onerror = function() {
            console.error("Failed to load Ace editor from CDN");
            // Do not call callback so we don't crash on 'ace' not defined, 
            // or we could fallback to regular textareas.
            // Let's just leave textareas as is.
        };
        document.head.appendChild(script);
    }

    function initEditors() {
        var textareas = document.querySelectorAll('textarea.aras-form-textarea');
        textareas.forEach(function(textarea) {
            var name = textarea.getAttribute('name');
            var mode = null;

            if (name === 'code' || name === 'formula') {
                mode = 'python';
            } else if (name && (name.endsWith('_json') || name === 'layout_json' || name === 'config_json' || name === 'payload_json')) {
                mode = 'json';
            } else if (textarea.classList.contains('code-python')) {
                mode = 'python';
            } else if (textarea.classList.contains('code-json')) {
                mode = 'json';
            }

            if (mode) {
                setupAce(textarea, mode);
            }
        });
    }

    function setupAce(textarea, mode) {
        // Hide original textarea
        textarea.style.display = 'none';

        // Create editor container
        var container = document.createElement('div');
        container.style.width = '100%';
        container.style.height = '400px';
        container.style.border = '1px solid #ddd';
        container.style.borderRadius = '4px';
        container.style.marginBottom = '10px';
        textarea.parentNode.insertBefore(container, textarea.nextSibling);

        var editor = ace.edit(container);
        editor.setTheme("ace/theme/monokai");
        editor.session.setMode("ace/mode/" + mode);
        editor.setValue(textarea.value, -1);
        
        // Options
        editor.setOptions({
            fontSize: "14px",
            showPrintMargin: false,
            useSoftTabs: true,
            tabSize: 4,
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: true
        });

        // Sync back to textarea on change
        editor.getSession().on('change', function() {
            textarea.value = editor.getValue();
        });

        // Handle form submit (optional but good for robustness)
        var form = textarea.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                textarea.value = editor.getValue();
            });
        }
        
        // Expose editor on the textarea element for debugging
        textarea.aceEditor = editor;
    }

    document.addEventListener('DOMContentLoaded', function() {
        loadAce(initEditors);
    });

    // Expose loadAce and initEditors for manual trigger
    window.ArasCodeEditor = {
        loadAce: loadAce,
        init: initEditors,
        setup: setupAce
    };

})();
