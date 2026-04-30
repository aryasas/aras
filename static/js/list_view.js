/* list_view.js — pure JS. Config set by _list_partial.html via window._listViewCfg */
(function () {
  var cfg = window._listViewCfg || {};
  var dataEl = document.getElementById('list-view-config-data');
  if (dataEl) {
    try {
      var jsonData = JSON.parse(dataEl.textContent);
      for (var key in jsonData) { cfg[key] = jsonData[key]; }
    } catch (e) { console.error('Failed to parse list-view-config-data', e); }
  }

  var LID        = cfg.LID        || '';
  var HAS_EDIT   = cfg.HAS_EDIT   || false;
  var HAS_BULK   = cfg.HAS_BULK   || false;
  var HAS_FILTER = cfg.HAS_FILTER || false;
  var HAS_PAG    = cfg.HAS_PAG    || false;
  var HAS_TOTALS = cfg.HAS_TOTALS || false;
  var showTotals   = cfg.showTotals   || false;
  var doctypeKey   = cfg.doctypeKey   || '';
  var savedColumns = cfg.savedColumns || null;
  var filterCols        = cfg.filterCols        || [];
  var editUrlBase       = cfg.editUrlBase       || '';
  var linkedDocsUrlBase = cfg.linkedDocsUrlBase || '';
  var opOptions = [
    ['equals','='],['not_equals','≠'],
    ['like','contains'],['not_like','not contains'],
    ['in','in'],['not_in','not in'],['is','is null']
  ];

  function $id(id) { return document.getElementById(id + LID); }
  function $q(sel) { return document.querySelectorAll(sel.replace(/\{\{L\}\}/g, LID)); }

  /* ── clickable rows ── */
  if (HAS_EDIT) {
    $q('tr.is-clickable').forEach(function (row) {
      row.addEventListener('click', function (e) {
        if (e.target.type === 'checkbox' ||
            e.target.classList.contains('aras-checkmark') ||
            e.target.closest('.aras-checkbox')) return;
        window.location.href = row.dataset.editUrl;
      });
    });
  }

  /* ── checkbox selection ── */
  if (HAS_BULK) {
    var checkAll = $id('checkAll');
    function getChecked() { return Array.from(document.querySelectorAll('.js-row-check' + LID + ':checked')); }
    function updateSelectionUI() {
      var n   = getChecked().length;
      var all = document.querySelectorAll('.js-row-check' + LID).length;
      var bw  = $id('bulkWrapInline');
      if (bw) bw.style.display = n > 0 ? 'flex' : 'none';
      var bc  = $id('bulkCountInline');
      if (bc) bc.textContent = n;
      document.querySelectorAll('tr.is-clickable').forEach(function (tr) {
        var cb = tr.querySelector('.js-row-check' + LID);
        if (cb) tr.classList.toggle('is-selected', cb.checked);
      });
      if (checkAll) {
        checkAll.indeterminate = n > 0 && n < all;
        checkAll.checked = all > 0 && n === all;
      }
    }
    if (checkAll) {
      checkAll.addEventListener('change', function () {
        document.querySelectorAll('.js-row-check' + LID).forEach(function (cb) { cb.checked = checkAll.checked; });
        updateSelectionUI();
      });
    }
    document.querySelectorAll('.js-row-check' + LID).forEach(function (cb) {
      cb.addEventListener('change', updateSelectionUI);
    });
    function _getCsrfBulk() {
      var meta = document.querySelector("meta[name='csrf-token']");
      if (meta) return meta.getAttribute("content");
      var el = document.querySelector("input[name='csrf_token']");
      return el ? el.value : '';
    }
    function triggerBulkDelete() {
      var checked = getChecked();
      if (!checked.length) return;
      var idsVal  = checked.map(function (c) { return c.value; }).join(',');
      var idsInput = document.getElementById('bulkDeleteIds' + LID);
      var form     = document.getElementById('bulkDeleteForm' + LID);
      if (!idsInput || !form) return;
      function doSubmit() { idsInput.value = idsVal; form.submit(); }

      function showBulkModal(bodyHtml) {
        var modal      = document.getElementById('arasDeleteModal');
        var body       = document.getElementById('arasDeleteModalBody');
        if (!modal || !body) { doSubmit(); return; }
        body.innerHTML = bodyHtml;
        modal.style.display = '';
        
        // Use the global setter from adm_delete.js
        if (window._arasSetDeleteConfirm) {
            window._arasSetDeleteConfirm(function () { doSubmit(); });
        } else {
            // Fallback if adm_delete.js not loaded
            var confirmBtn = document.getElementById('arasDeleteModalConfirm');
            if (confirmBtn) {
                var newConfirm = confirmBtn.cloneNode(true);
                confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
                newConfirm.onclick = function() { modal.style.display = 'none'; doSubmit(); };
            }
        }
      }

      // Single record — fetch linked docs preview
      if (checked.length === 1 && linkedDocsUrlBase) {
        var id  = checked[0].value;
        var url = linkedDocsUrlBase + id + '/linked-docs/';
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': _getCsrfBulk() } })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            var tree = data.tree || [];
            var html;
            if (tree.length) {
              html = "<p class='text-danger mb-2'><strong>" + tree.length
                   + " linked record(s) will also be deleted:</strong></p>"
                   + "<ul style='list-style:none;padding:0;margin:0 0 12px;'>";
              tree.forEach(function (node) {
                var indent = node.depth > 1 ? 'margin-left:' + ((node.depth - 1) * 16) + 'px;' : '';
                var label  = node.display ? node.doc_type + ' — ' + node.display
                                          : node.doc_type + ' #' + node.doc_id;
                html += "<li style='padding:4px 0;" + indent + "'>"
                      + "<i class='fa fa-file-o mr-1 text-muted'></i>" + label + "</li>";
              });
              html += "</ul><small class='text-muted'>All records will be backed up to Trash and can be restored.</small>";
            } else {
              html = "<p>Delete this record?<br><small class='text-muted'>Will be saved to Trash and can be restored.</small></p>";
            }
            showBulkModal(html);
          })
          .catch(function () { showBulkModal("<p>Delete this record?</p>"); });
        return;
      }

      // Multiple records — simple count modal
      showBulkModal(
        "<p>Delete <strong>" + checked.length + "</strong> record(s)?<br>"
        + "<small class='text-muted'>Records will be saved to Trash and can be restored.</small></p>"
      );
    }
    document.querySelectorAll('.js-bulk-delete' + LID).forEach(function (el) {
      el.addEventListener('click', function (e) { e.preventDefault(); triggerBulkDelete(); });
    });
  }

  /* ── filter panel ── */
  if (HAS_FILTER) {
    var filterPanel  = $id('filterPanel');
    var filterToggle = $id('filterToggleBtn');
    var filterClose  = $id('filterCloseBtn');
    var addRowBtn    = $id('addFilterRowBtn');
    if (filterToggle) filterToggle.addEventListener('click', function () { filterPanel.classList.toggle('is-open'); });
    if (filterClose)  filterClose.addEventListener('click',  function () { filterPanel.classList.remove('is-open'); });
    if (addRowBtn)    addRowBtn.addEventListener('click', function () { $id('filterRows').appendChild(buildFilterRow()); });
    document.querySelectorAll('.js-remove-filter-row' + LID).forEach(bindRemoveFilter);
    document.querySelectorAll('.js-op-select' + LID).forEach(bindOpSelect);

    function buildFilterRow() {
      var row = document.createElement('div');
      row.className = 'aras-filter-row';

      var wrap = document.createElement('div');
      wrap.className = 'd-flex gap-8 flex-grow-1';

      var colSel = el('select', { name: 'f_col[]', className: 'aras-fsel' });
      filterCols.forEach(function (fc) { colSel.appendChild(el('option', { value: fc[1], textContent: fc[0] })); });

      var opSel = el('select', { name: 'f_op[]', className: 'aras-fsel aras-fsel--op js-op-select' + LID });
      opOptions.forEach(function (op) { opSel.appendChild(el('option', { value: op[0], textContent: op[1] })); });

      var valIn = el('input', { type: 'text', name: 'f_val[]', className: 'aras-finput js-val-input' + LID, placeholder: 'value…' });

      wrap.appendChild(colSel);
      wrap.appendChild(opSel);
      wrap.appendChild(valIn);

      var rm = el('button', {
        type: 'button',
        className: 'aras-btn aras-btn--outline aras-btn--sm js-remove-filter-row' + LID,
        title: 'Remove',
        innerHTML: '<i class="fa fa-times"></i>'
      });

      bindOpSelect(opSel);
      bindRemoveFilter(rm);

      row.appendChild(wrap);
      row.appendChild(rm);
      return row;
    }
    function bindOpSelect(sel) {
      sel.addEventListener('change', function () {
        var vi = this.closest('.aras-filter-row').querySelector('.js-val-input' + LID);
        if (vi) vi.style.display = this.value === 'is' ? 'none' : '';
      });
    }
    function bindRemoveFilter(btn) {
      btn.addEventListener('click', function () { btn.closest('.aras-filter-row').remove(); });
    }
  }

  /* ── per-page selector ── */
  if (HAS_PAG) {
    var ppSel = $id('perPageSelect');
    if (ppSel) ppSel.addEventListener('change', function () {
      var url = new URL(window.location.href);
      url.searchParams.set('per_page', this.value);
      url.searchParams.delete('page');
      window.location = url.toString();
    });
  }

  /* ── column totals ── */
  if (HAS_TOTALS) {
    var totalsBtn = $id('totalsToggleBtn');
    var totalsRow = $id('totalsRow');
    function computeTotals() {
      if (!totalsRow) return;
      var cells  = totalsRow.querySelectorAll('.js-col-total' + LID);
      var rows   = Array.from(document.querySelectorAll('#mainListTable' + LID + ' tbody tr'));
      var offset = HAS_BULK ? 1 : 0;
      cells.forEach(function (cell, idx) {
        var ci = idx + offset; var sum = 0; var isNum = false;
        rows.forEach(function (r) {
          var td = r.cells[ci]; if (!td) return;
          var v = parseFloat(td.textContent.trim().replace(/,/g, ''));
          if (!isNaN(v)) { sum += v; isNum = true; }
        });
        cell.textContent = isNum ? sum.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—';
      });
      totalsRow.style.display = '';
    }
    if (showTotals) computeTotals();
    if (totalsBtn) totalsBtn.addEventListener('click', function () {
      var active = this.dataset.active === 'true'; active = !active;
      this.dataset.active = String(active);
      this.classList.toggle('aras-btn--active', active);
      if (active) { computeTotals(); } else if (totalsRow) { totalsRow.style.display = 'none'; }
    });
  }

  /* ── column visibility toggle ── */
  (function () {
    var btn     = $id('colToggleBtn');
    var popover = $id('colTogglePopover');
    var table   = $id('mainListTable');
    if (!btn || !popover) return;

    function applyColVisibility(fieldName, visible) {
      if (!table) return;
      table.querySelectorAll('thead th[data-field="' + fieldName + '"]').forEach(function (th) {
        th.style.display = visible ? '' : 'none';
      });
      table.querySelectorAll('tbody td[data-field="' + fieldName + '"]').forEach(function (td) {
        td.style.display = visible ? '' : 'none';
      });
      var totalsRow = $id('totalsRow');
      if (totalsRow) {
        totalsRow.querySelectorAll('td[data-field="' + fieldName + '"]').forEach(function (td) {
          td.style.display = visible ? '' : 'none';
        });
      }
    }

    function _getCsrf() {
      var m = document.cookie.match(/csrf_token=([^;]+)/);
      return m ? decodeURIComponent(m[1]) : '';
    }

    function persistColumns() {
      if (!doctypeKey) return;
      var visible = [];
      popover.querySelectorAll('.js-col-vis' + LID).forEach(function (cb) {
        if (cb.checked && cb.dataset.field) visible.push(cb.dataset.field);
      });
      fetch('/admin/api/list-pref/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': _getCsrf()},
        body: JSON.stringify({doctype: doctypeKey, columns: visible})
      });
    }

    // Apply initial state — hide unchecked columns
    popover.querySelectorAll('.js-col-vis' + LID).forEach(function (cb) {
      if (!cb.checked) applyColVisibility(cb.dataset.field, false);
    });

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      popover.style.display = popover.style.display === 'none' ? 'block' : 'none';
    });
    document.addEventListener('click', function () { popover.style.display = 'none'; });
    popover.addEventListener('click', function (e) { e.stopPropagation(); });
    popover.querySelectorAll('.js-col-vis' + LID).forEach(function (cb) {
      cb.addEventListener('change', function () {
        applyColVisibility(cb.dataset.field, cb.checked);
        persistColumns();
      });
    });
  })();

  /* ── inline edit ── */
  if (HAS_EDIT && editUrlBase) {
    document.querySelectorAll('td.js-inline-cell' + LID).forEach(function (td) {
      td.addEventListener('dblclick', function (e) {
        e.stopPropagation();
        if (td.querySelector('input')) return;
        var orig  = td.textContent.trim();
        var field = td.dataset.field;
        var id    = td.dataset.id;
        var input = el('input', { type: 'text', value: orig, className: 'aras-inline-input', style: 'width:100%;box-sizing:border-box;' });
        td.textContent = ''; td.appendChild(input); input.focus(); input.select();
        function save() {
          var val = input.value.trim();
          if (val === orig) { td.textContent = orig; return; }
          var body = new FormData(); body.append(field, val);
          fetch(editUrlBase + '/' + id + '/', { method: 'PUT', body: body })
            .then(function (r) { td.textContent = r.ok ? val : orig; })
            .catch(function () { td.textContent = orig; });
        }
        input.addEventListener('blur', save);
        input.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
          if (e.key === 'Escape') { td.textContent = orig; }
        });
      });
    });
  }

  /* ── preserve settings panel hash on search/filter submit ── */
  (function () {
    var panel = document.getElementById('listToolbar' + LID);
    panel = panel && panel.closest('.settings-panel');
    if (!panel) return;
    var panelId = panel.id;
    [document.getElementById('searchForm' + LID), document.getElementById('listFilterForm' + LID)].forEach(function (form) {
      if (!form) return;
      form.addEventListener('submit', function () {
        form.action = (form.action || window.location.pathname) + '#' + panelId;
      });
    });
  })();

  function el(tag, props) {
    var e = document.createElement(tag);
    for (var k in props) { if (k === 'innerHTML') e.innerHTML = props[k]; else e[k] = props[k]; }
    return e;
  }
})();
