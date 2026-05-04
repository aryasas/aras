/**
 * Aras Design System - Core JS (Midnight Editorial)
 * Handles Sidebar, Search and Dropdowns.
 */

(function() {
    "use strict";

    var ArasStudio = {
        init: function() {
            this.initTheme();
            this.initSidebar();
            this.initSidebarCollapse();
            this.initRightSidebar();
            this.initSearch();
            this.initUserMenu();
            this.initComponentLibrary();
            this.initFormLoading();
        },

        initTheme: function() {
            var toggle = document.getElementById('themeToggle');
            var html = document.documentElement;
            
            if (!toggle) return;

            // Set initial icon
            var initialTheme = html.getAttribute('data-theme') || 'light';
            var icon = toggle.querySelector('i');
            if (icon) {
                icon.className = initialTheme === 'dark' ? 'fa fa-moon-o' : 'fa fa-sun-o';
            }

            toggle.addEventListener('click', function() {
                var current = html.getAttribute('data-theme');
                var next = current === 'dark' ? 'light' : 'dark';
                
                html.setAttribute('data-theme', next);
                localStorage.setItem('aras-theme', next);
                
                // Update icon
                var icon = toggle.querySelector('i');
                if (icon) {
                    icon.className = next === 'dark' ? 'fa fa-moon-o' : 'fa fa-sun-o';
                }
            });
        },

        initSidebar: function() {
            var toggle = document.getElementById('mobileSidebarToggle');
            var sidebar = document.getElementById('sidebar-menu');
            if (!toggle || !sidebar) return;

            toggle.addEventListener('click', function() {
                sidebar.classList.toggle('is-open');
            });

            // Close when clicking outside on mobile
            document.addEventListener('click', function(e) {
                if (sidebar.classList.contains('is-open') && 
                    !sidebar.contains(e.target) && 
                    !toggle.contains(e.target)) {
                    sidebar.classList.remove('is-open');
                }
            });
        },

        initFormLoading: function() {
            document.addEventListener('submit', function(e) {
                var form = e.target;
                if (form.tagName === 'FORM') {
                    var btn = form.querySelector('button[type="submit"], input[type="submit"]');
                    if (btn) {
                        // Sync Rich Text editors before submit
                        form.querySelectorAll('.ql-container').forEach(function(qlCont) {
                            var quill = Quill.find(qlCont);
                            if (quill) {
                                var textarea = qlCont.previousElementSibling;
                                if (textarea && textarea.tagName === 'TEXTAREA') {
                                    textarea.value = quill.root.innerHTML;
                                }
                            }
                        });

                        // Delay slightly to allow native validation to kick in if any
                        setTimeout(function() {
                            if (form.checkValidity()) {
                                btn.classList.add('is-loading');
                            }
                        }, 10);
                    }
                }
            });
        },

        initUserMenu: function() {
            var toggle = document.getElementById('arasUserMenuToggle');
            var menu   = document.getElementById('arasUserMenu');
            if (!toggle || !menu) return;

            toggle.addEventListener('click', function(e) {
                e.stopPropagation();
                var open = menu.classList.toggle('is-open');
                toggle.classList.toggle('is-open', open);
            });

            document.addEventListener('click', function() {
                menu.classList.remove('is-open');
                toggle.classList.remove('is-open');
            });
        },

        initComponentLibrary: function() {
            // ── Tom Select (Searchable Combobox + "Add new" footer) ──
            if (window.TomSelect) {
                var sel = 'select.aras-form-select:not([disabled]):not([data-tom-select])'
                    + ', select.aras-searchable:not([disabled]):not([data-tom-select])'
                    + ', select.ct-cell-input:not([disabled]):not([data-tom-select])'
                    + ', select.data-typeahead:not([data-tom-select])'
                    + ', select[data-typeahead]:not([data-tom-select])';
                document.querySelectorAll(sel).forEach(function(el) {
                    if (el.dataset.tomSelect) return;
                    if (el.multiple) return;  // leave multi-selects alone
                    var addUrl = el.getAttribute('data-rel-add-url') || '';
                    var ts = new TomSelect(el, {
                        create: false,
                        allowEmptyOption: true,
                        plugins: ['dropdown_input'],
                        render: {
                            no_results: function (data, escape) {
                                return '<div class="ts-no-results">No matches for "' + escape(data.input) + '"</div>';
                            }
                        }
                    });
                    el.dataset.tomSelect = "true";

                    // Inject "+ Add new" footer when this select points to a relation table.
                    if (addUrl) {
                        var attachAddNew = function () {
                            if (ts.dropdown.querySelector('.ts-add-new')) return;
                            var foot = document.createElement('a');
                            foot.className = 'ts-add-new';
                            foot.href = addUrl;
                            foot.target = '_blank';
                            foot.innerHTML = '<i class="fa fa-plus"></i><span>Add new</span>';
                            foot.addEventListener('mousedown', function(e) { e.stopPropagation(); });
                            foot.addEventListener('click', function() {
                                setTimeout(function(){ try { ts.close(); } catch(_){} }, 0);
                            });
                            var inputWrap = ts.dropdown.querySelector('.dropdown-input-wrap');
                            if (inputWrap) {
                                inputWrap.parentNode.insertBefore(foot, inputWrap.nextSibling);
                            } else {
                                ts.dropdown.insertBefore(foot, ts.dropdown.firstChild);
                            }
                        };
                        attachAddNew();
                        ts.on('dropdown_open', attachAddNew);
                    }
                });
            }

            // ── Flatpickr (Datepicker) ──
            if (window.flatpickr) {
                flatpickr('input[type="date"], .aras-datepicker', {
                    altInput: true,
                    altFormat: "F j, Y",
                    dateFormat: "Y-m-d",
                    allowInput: true
                });
            }

            // ── Quill (Rich Text) ──
            if (window.Quill) {
                document.querySelectorAll('textarea.richtext').forEach(function(el) {
                    if (el.style.display === 'none') return;
                    
                    var container = document.createElement('div');
                    container.className = 'quill-editor-wrapper';
                    el.parentNode.insertBefore(container, el);
                    
                    var quill = new Quill(container, {
                        theme: 'snow',
                        modules: {
                            toolbar: [
                                [{'header': [1, 2, 3, false]}],
                                ['bold', 'italic', 'underline', 'strike'],
                                [{'list': 'ordered'}, {'list': 'bullet'}],
                                ['link', 'clean']
                            ]
                        }
                    });
                    
                    quill.root.innerHTML = el.value;
                    el.style.display = 'none';
                    
                    quill.on('text-change', function() {
                        el.value = quill.root.innerHTML;
                    });
                });
            }
        },

        initSidebarCollapse: function() {
            var toggle = document.getElementById('sidebarCollapseToggle');
            var html = document.documentElement;
            if (!toggle) return;

            // Note: State is now pre-loaded in base_partial_head.html for early detection
            
            toggle.addEventListener('click', function() {
                html.classList.toggle('aras-mini-sidebar-active');
                var collapsed = html.classList.contains('aras-mini-sidebar-active');
                localStorage.setItem('aras-sidebar-mini', collapsed);
                
                // Update icon
                toggle.querySelector('i').className = collapsed ? 'fa fa-angle-right' : 'fa fa-angle-left';
            });
        },

        initRightSidebar: function() {
            var toggle = document.getElementById('rightSidebarToggle');
            var closeBtn = document.getElementById('closeRightSidebar');
            var sidebar = document.getElementById('arasRightSidebar');
            var frame = document.querySelector('.aras-frame');
            
            if (!toggle || !sidebar) return;

            toggle.addEventListener('click', function(e) {
                e.stopPropagation();
                sidebar.classList.toggle('is-open');
                if (frame) frame.classList.toggle('has-right-sidebar');
            });

            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    sidebar.classList.remove('is-open');
                    if (frame) frame.classList.remove('has-right-sidebar');
                });
            }

            // Close when clicking outside
            document.addEventListener('click', function(e) {
                if (sidebar.classList.contains('is-open') && 
                    !sidebar.contains(e.target) && 
                    !toggle.contains(e.target)) {
                    sidebar.classList.remove('is-open');
                    if (frame) frame.classList.remove('has-right-sidebar');
                }
            });
        },

        initSearch: function() {
            var input = document.getElementById('arasTopSearchInput');
            var results = document.getElementById('arasTopSearchResults');
            var timer = null;

            if (!input || !results) return;

            input.addEventListener('input', function() {
                var q = input.value.trim();
                clearTimeout(timer);
                if (q.length < 2) {
                    results.style.display = 'none';
                    return;
                }

                timer = setTimeout(function() {
                    fetch('/api/search?q=' + encodeURIComponent(q))
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            ArasStudio.renderResults(data, results);
                            results.style.display = 'block';
                        });
                }, 300);
            });

            // Keyboard shortcut (Cmd+K or Ctrl+K)
            document.addEventListener('keydown', function(e) {
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                    e.preventDefault();
                    input.focus();
                }
            });

            // Hide results on blur
            document.addEventListener('click', function(e) {
                if (!input.contains(e.target) && !results.contains(e.target)) {
                    results.style.display = 'none';
                }
            });
        },

        renderResults: function(items, container) {
            if (!items.length) {
                container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--aras-ink-3);font-family:var(--aras-font-serif);font-style:italic;font-size:13px;">No results</div>';
                return;
            }
            var html = '';
            items.forEach(function(item) {
                html += '<a href="' + item.url + '" class="aras-search-result-item">'
                    + '<div style="font-size:9px;font-weight:700;color:var(--aras-accent);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:2px;">' + item.app + ' › ' + item.resource + '</div>'
                    + '<div style="font-size:14px;font-weight:700;color:var(--aras-brand);font-family:var(--aras-font-serif);">' + item.title + '</div>'
                    + (item.match ? '<div style="font-size:11px;color:var(--aras-ink-2);font-family:var(--aras-font-serif);font-style:italic;">' + item.match + '</div>' : '')
                    + '</a>';
            });
            container.innerHTML = html;
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { ArasStudio.init(); });
    } else {
        ArasStudio.init();
    }

    // Global Aras Object
    window.Aras = {
        toast: function(msg, type) {
            type = type || 'info';
            var wrap = document.querySelector('.aras-alert-toast-wrap');
            if (!wrap) {
                wrap = document.createElement('div');
                wrap.className = 'aras-alert-toast-wrap';
                wrap.setAttribute('role', 'log');
                wrap.setAttribute('aria-live', 'polite');
                document.body.appendChild(wrap);
            }
            var toast = document.createElement('div');
            // Support both aras-badge-- classes and new aras-alert-toast-- classes
            var categoryClass = (type === 'error' || type === 'danger') ? 'danger' : type;
            toast.className = 'aras-alert-toast aras-alert-toast-' + type + ' aras-badge--' + categoryClass;
            toast.setAttribute('role', 'alert');
            
            var icon = 'fa-info-circle';
            if (type === 'success') icon = 'fa-check-circle';
            if (type === 'error' || type === 'danger') icon = 'fa-exclamation-circle';
            if (type === 'warning') icon = 'fa-warning';
            
            toast.innerHTML = '<i class="fa ' + icon + ' mt-1"></i>' +
                             '<span style="flex:1">' + msg + '</span>' +
                             '<button type="button" onclick="this.parentElement.remove()">&times;</button>';
            
            wrap.appendChild(toast);
            
            // Auto-remove after 4s
            setTimeout(function() {
                if (!toast.parentElement) return;
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300);
            }, 4000);
        },

        dialog: function(options) {
            return new Promise(function(resolve) {
                var type = options.type || 'alert'; // alert, confirm, prompt
                var title = options.title || (type === 'alert' ? 'Notification' : (type === 'confirm' ? 'Confirmation' : 'Input Required'));
                var message = options.message || '';
                var defaultValue = options.defaultValue || '';
                var okText = options.okText || 'OK';
                var cancelText = options.cancelText || 'Cancel';

                var modal = document.createElement('div');
                modal.className = 'aras-modal';
                
                var overlay = document.createElement('div');
                overlay.className = 'aras-modal__overlay';
                
                var content = document.createElement('div');
                content.className = 'aras-modal__content';
                
                var html = '<div class="aras-dialog-header">' +
                           '<h4 class="aras-dialog-title">' + title + '</h4>' +
                           '</div>' +
                           '<div class="aras-dialog-body">' +
                           '<div>' + message.replace(/\n/g, '<br>') + '</div>';
                
                if (type === 'prompt') {
                    html += '<input type="text" class="aras-dialog-input" value="' + defaultValue + '">';
                }
                
                html += '</div>' +
                        '<div class="aras-dialog-footer">';
                
                if (type !== 'alert') {
                    html += '<button class="aras-btn aras-btn--outline aras-dialog-cancel">' + cancelText + '</button>';
                }
                
                html += '<button class="aras-btn aras-btn--primary aras-dialog-ok">' + okText + '</button>' +
                        '</div>';
                
                content.innerHTML = html;
                modal.appendChild(overlay);
                modal.appendChild(content);
                document.body.appendChild(modal);

                var okBtn = content.querySelector('.aras-dialog-ok');
                var cancelBtn = content.querySelector('.aras-dialog-cancel');
                var input = content.querySelector('.aras-dialog-input');

                if (input) {
                    input.focus();
                    input.select();
                } else {
                    okBtn.focus();
                }

                var close = function(result) {
                    modal.style.opacity = '0';
                    content.style.transform = 'scale(0.95) translateY(10px)';
                    setTimeout(function() {
                        modal.remove();
                        resolve(result);
                    }, 200);
                };

                content.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        if (cancelBtn) cancelBtn.click();
                        else okBtn.click();
                    }
                    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                        okBtn.click();
                    }
                });

                okBtn.addEventListener('click', function() {
                    var val = input ? input.value : true;
                    close(val);
                });

                if (cancelBtn) {
                    cancelBtn.addEventListener('click', function() {
                        close(type === 'prompt' ? null : false);
                    });
                }

                overlay.addEventListener('click', function() {
                    if (type === 'alert') okBtn.click();
                    else if (cancelBtn) cancelBtn.click();
                });
            });
        },

        alert: function(msg, title) {
            return Aras.dialog({ type: 'alert', message: msg, title: title });
        },

        confirm: function(msg, title) {
            return Aras.dialog({ type: 'confirm', message: msg, title: title });
        },

        prompt: function(msg, defaultValue, title) {
            return Aras.dialog({ type: 'prompt', message: msg, defaultValue: defaultValue, title: title });
        }
    };

    // Override native browser dialogs
    window.alert = function(msg) { Aras.alert(msg); };
    window.confirm = function(msg) { 
        console.warn("Native confirm() overridden by Aras.dialog. This is asynchronous and may break legacy synchronous code.");
        return Aras.confirm(msg); 
    };
    window.prompt = function(msg, def) { 
        console.warn("Native prompt() overridden by Aras.dialog. This is asynchronous and may break legacy synchronous code.");
        return Aras.prompt(msg, def); 
    };

    // Backward compatibility
    window.arasNotify = window.Aras.toast;
})();
