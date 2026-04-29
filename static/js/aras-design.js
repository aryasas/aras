/**
 * Aras Design System - Core JS (Midnight Editorial)
 * Handles Sidebar, Search and Dropdowns.
 */

(function() {
    "use strict";

    var ArasStudio = {
        init: function() {
            this.initSidebar();
            this.initSearch();
            this.initCustomSelects();
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

        initCustomSelects: function() {
            var selects = document.querySelectorAll('.aras-form-select, .aras-fsel');
            selects.forEach(function(select) {
                if (select.closest('.aras-custom-select') || select.classList.contains('is-hidden')) return;
                
                var wrapper = document.createElement('div');
                wrapper.className = 'aras-custom-select';
                if (select.classList.contains('aras-fsel')) wrapper.classList.add('aras-fsel-wrapper');
                
                var trigger = document.createElement('div');
                trigger.className = 'aras-select-trigger';
                
                var label = document.createElement('span');
                label.textContent = select.options[select.selectedIndex] ? select.options[select.selectedIndex].text : 'Select...';
                
                var icon = document.createElement('i');
                icon.className = 'fa fa-chevron-down';
                
                trigger.appendChild(label);
                trigger.appendChild(icon);
                
                var optionsContainer = document.createElement('div');
                optionsContainer.className = 'aras-select-options';
                
                function buildOptions() {
                    optionsContainer.innerHTML = '';
                    Array.from(select.options).forEach(function(opt) {
                        var o = document.createElement('div');
                        o.className = 'aras-select-option';
                        if (opt.selected) o.classList.add('is-selected');
                        o.textContent = opt.text;
                        o.dataset.value = opt.value;
                        
                        o.addEventListener('click', function(e) {
                            e.stopPropagation();
                            select.value = opt.value;
                            label.textContent = opt.text;
                            
                            updateSelectedState();
                            wrapper.classList.remove('is-open');
                            
                            var event = new Event('change', { bubbles: true });
                            select.dispatchEvent(event);
                        });
                        optionsContainer.appendChild(o);
                    });
                }

                function updateSelectedState() {
                    var val = select.value;
                    optionsContainer.querySelectorAll('.aras-select-option').forEach(function(el) {
                        el.classList.toggle('is-selected', el.dataset.value === val);
                    });
                    label.textContent = select.options[select.selectedIndex] ? select.options[select.selectedIndex].text : 'Select...';
                }
                
                buildOptions();
                
                wrapper.appendChild(trigger);
                wrapper.appendChild(optionsContainer);
                
                select.parentNode.insertBefore(wrapper, select);
                select.classList.add('is-hidden');
                wrapper.appendChild(select);
                
                trigger.addEventListener('click', function(e) {
                    e.stopPropagation();
                    document.querySelectorAll('.aras-custom-select.is-open').forEach(function(openSelect) {
                        if (openSelect !== wrapper) openSelect.classList.remove('is-open');
                    });
                    wrapper.classList.toggle('is-open');
                });

                select.addEventListener('change', updateSelectedState);
                
                var observer = new MutationObserver(function() {
                    buildOptions();
                    updateSelectedState();
                });
                observer.observe(select, { childList: true });
            });
            
            document.addEventListener('click', function() {
                document.querySelectorAll('.aras-custom-select.is-open').forEach(function(el) {
                    el.classList.remove('is-open');
                });
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
})();
