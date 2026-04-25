/**
 * Aras Design System - Core JS
 * Handles Integrated Search and Studio UI interactions.
 */

(function() {
    "use strict";

    var ArasStudio = {
        init: function() {
            this.initSearch();
            this.initDropdowns();
        },

        initSearch: function() {
            var input = document.getElementById('arasTopSearchInput');
            var results = document.getElementById('arasTopSearchResults');
            var timer = null;

            if (!input || !results) return;

            input.addEventListener('focus', function() {
                if (input.value.trim().length >= 2) results.style.display = 'block';
            });

            document.addEventListener('click', function(e) {
                if (!input.contains(e.target) && !results.contains(e.target)) {
                    results.style.display = 'none';
                }
            });

            input.addEventListener('input', function() {
                clearTimeout(timer);
                var q = input.value.trim();
                if (q.length < 2) {
                    results.innerHTML = '';
                    results.style.display = 'none';
                    return;
                }
                results.style.display = 'block';
                timer = setTimeout(function() {
                    ArasStudio.doSearch(q, results);
                }, 220);
            });

            // Global shortcut ⌘K or Ctrl+K to focus search
            document.addEventListener('keydown', function(e) {
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                    e.preventDefault();
                    input.focus();
                }
                if (e.key === 'Escape') {
                    results.style.display = 'none';
                    input.blur();
                }
            });
        },

        doSearch: function(q, resultsContainer) {
            resultsContainer.innerHTML = '<div style="padding:16px;text-align:center;color:#9aacb8;"><i class="fa fa-spinner fa-spin"></i></div>';
            
            fetch('/api/_search/?q=' + encodeURIComponent(q))
                .then(function(r) { return r.json(); })
                .then(function(data) { 
                    ArasStudio.renderResults(data.results || [], resultsContainer); 
                })
                .catch(function() { 
                    resultsContainer.innerHTML = '<div style="padding:12px;color:#a05a5a;font-size:12px;text-align:center;">Search failed.</div>'; 
                });
        },

        renderResults: function(items, container) {
            if (!items.length) {
                container.innerHTML = '<div style="padding:16px;text-align:center;color:#9aacb8;font-family:serif;font-style:italic;font-size:13px;">No results</div>';
                return;
            }
            var html = '';
            items.forEach(function(item) {
                html += '<a href="' + item.url + '" style="display:flex;flex-direction:column;padding:10px 16px;text-decoration:none;color:inherit;border-bottom:1px solid #f0f3f5;transition:background 0.1s;" onmouseover="this.style.background=\'#faf8f3\'" onmouseout="this.style.background=\'\'">'
                    + '<div style="font-size:10px;font-weight:600;color:#9aacb8;text-transform:uppercase;letter-spacing:0.5px;">' + item.app + ' › ' + item.resource + '</div>'
                    + '<div style="font-size:13px;font-weight:600;color:#0f1b2d;">' + item.title + '</div>'
                    + (item.match ? '<div style="font-size:11px;color:#6c757d;font-family:serif;font-style:italic;">' + item.match + '</div>' : '')
                    + '</a>';
            });
            container.innerHTML = html;
        },

        initDropdowns: function() {
            // Dropdown hover logic if not handled by CSS
            document.querySelectorAll('.appmenu-item').forEach(function(item) {
                var dropdown = item.querySelector('.appmenu-dropdown');
                if (!dropdown) return;
                
                item.addEventListener('mouseenter', function() {
                    dropdown.style.display = 'block';
                });
                item.addEventListener('mouseleave', function() {
                    dropdown.style.display = 'none';
                });
            });
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { ArasStudio.init(); });
    } else {
        ArasStudio.init();
    }

})();
