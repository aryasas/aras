/* Aras Admin — List Detail Panel JS */
(function () {
    document.querySelectorAll('#mainListTable tbody tr.is-clickable').forEach(function (row) {
        var detailUrl = row.dataset.detailUrl;
        if (!detailUrl) return;
        row.addEventListener('click', function (e) {
            if (e.target.closest('td.td-check')) return;
            e.preventDefault();
            fetch(detailUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (r) { return r.text(); })
                .then(function (html) {
                    var panel = document.querySelector('.aras-list-detail-panel');
                    if (panel) panel.innerHTML = html;
                    document.querySelectorAll('#mainListTable tbody tr').forEach(function (r) {
                        r.classList.remove('is-selected');
                    });
                    row.classList.add('is-selected');
                });
        });
    });
})();
