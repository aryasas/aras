/* child_table.js — pure JS, no Jinja2.
   Bootstrap: com_child_table.html writes ct-meta-<li> JSON, then calls initChildTable(li).
   All per-instance state is derived from that JSON element. */

function initChildTable(li) {
    var meta = _ctGetMeta(li);
    var MN   = meta.model_name || '';

    /* ── column visibility ── */
    document.querySelectorAll('.js-ct-col-vis-' + li).forEach(function(cb) {
        if (!cb.checked) _ctApplyColVis(li, cb.dataset.field, false);
    });
    document.addEventListener('click', function(e) {
        var p = document.getElementById('ct-settings-' + li);
        if (p && !p.contains(e.target) && !e.target.closest('#ct-settings-' + li)) {
            p.style.display = 'none';
        }
    });

    /* ── calc bindings ── */
    _ctBindCalc(li, 'ct-' + li + '-');
    _ctBindCalc(li, 'ct-modal-' + li + '-');
}

/* ── Public API (called from HTML onclick attrs) ── */

function toggleCtSettings(idx, e) {
    if (e) e.stopPropagation();
    var p = document.getElementById('ct-settings-' + idx);
    if (p) p.style.display = p.style.display === 'none' ? 'block' : 'none';
}

function toggleCtTotals(idx) {
    var footer = document.getElementById('ct-footer-' + idx);
    var btn    = document.getElementById('ct-totals-btn-' + idx);
    if (!footer) return;
    var show = footer.style.display === 'none';
    if (show) {
        /* Auto-compute totals for all numeric vcol columns */
        var tbody = document.getElementById('ct-tbody-' + idx);
        if (tbody) {
            var meta = _ctGetMeta(idx);
            (meta.vcols || []).forEach(function(field) {
                var sum = 0; var isNum = false;
                tbody.querySelectorAll('.ct-data-row td[data-field="' + field + '"]').forEach(function(td) {
                    var v = parseFloat((td.dataset.raw || td.textContent || '').replace(/,/g,''));
                    if (!isNaN(v)) { sum += v; isNum = true; }
                });
                var fc = footer.querySelector('[data-total-field="' + field + '"]');
                if (fc) fc.innerHTML = isNum ? '<strong>' + sum.toLocaleString(undefined, {maximumFractionDigits:2}) + '</strong>' : '';
            });
        }
        footer.style.display = '';
    } else {
        footer.style.display = 'none';
    }
    if (btn) btn.classList.toggle('aras-btn--active', show);
}

function applyCtColVis(idx, field, visible) { _ctApplyColVis(idx, field, visible); }

function persistCtCols(idx) {
    var meta = _ctGetMeta(idx);
    var MN = meta.model_name || '';
    if (!MN) return;
    var visible = [];
    document.querySelectorAll('.js-ct-col-vis-' + idx).forEach(function(cb) {
        if (cb.checked) visible.push(cb.dataset.field);
    });
    fetch('/admin/api/list-pref/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': _ctGetCsrf()},
        body: JSON.stringify({doctype: 'child/' + MN, columns: visible})
    });
}

function ctAddRow(idx) {
    var row = document.getElementById('ct-input-row-' + idx);
    if (!row) return;
    row.classList.remove('d-none');
    var btn = document.getElementById('ct-add-btn-' + idx);
    if (btn) btn.style.display = 'none';
    var first = row.querySelector('.ct-cell-input');
    if (first) setTimeout(function() { first.focus(); }, 50);
    _ctClearInputRow(idx);
}

function ctHideInputRow(idx) {
    var row = document.getElementById('ct-input-row-' + idx);
    if (row) row.classList.add('d-none');
    var btn = document.getElementById('ct-add-btn-' + idx);
    if (btn) btn.style.display = '';
}

function _getCtLocalData(idx) {
    var inp = document.getElementById('ct-local-input-' + idx);
    if (!inp) {
        inp = document.createElement('input');
        inp.type = 'hidden';
        inp.name = 'ct_local_' + idx;
        inp.id = 'ct-local-input-' + idx;
        var form = document.getElementById('mainForm') || document.querySelector('form');
        if (form) form.appendChild(inp);
    }
    return inp.value ? JSON.parse(inp.value) : [];
}

function _setCtLocalData(idx, arr) {
    var inp = document.getElementById('ct-local-input-' + idx);
    if (inp) inp.value = JSON.stringify(arr);
}

function ctSaveInlineRow(idx, apiUrl, fkCol, parentId) {
    var row = document.getElementById('ct-input-row-' + idx);
    var data = {};
    data[fkCol] = parentId;
    row.querySelectorAll('.ct-cell-input').forEach(function(el) {
        if (el.type === 'checkbox') data[el.name] = el.checked;
        else if (el.value !== '') data[el.name] = el.value;
    });
    /* Auto-fill description from product select text if empty */
    if (!data['description']) {
        var prodSel = document.getElementById('ct-' + idx + '-product_id');
        if (prodSel && prodSel.selectedIndex > 0) {
            data['description'] = prodSel.options[prodSel.selectedIndex].text;
        }
    }
    /* Apply numeric defaults so DB NOT NULL constraints are satisfied */
    if (!data['qty'])           data['qty']           = '1';
    if (!data['unit_price'])    data['unit_price']    = '0';
    if (!data['discount_pct'])  data['discount_pct']  = '0';
    /* Recalc subtotal from current field values */
    var qtyEl   = document.getElementById('ct-' + idx + '-qty');
    var priceEl = document.getElementById('ct-' + idx + '-unit_price');
    var discEl  = document.getElementById('ct-' + idx + '-discount_pct');
    var qty   = parseFloat((qtyEl   && qtyEl.value)   || data['qty']          || 1);
    var price = parseFloat((priceEl && priceEl.value) || data['unit_price']   || 0);
    var disc  = parseFloat((discEl  && discEl.value)  || data['discount_pct'] || 0);
    data['subtotal'] = (qty * price * (1 - disc / 100)).toFixed(4);

    if (!parentId || parentId === 'None' || parentId === 'null') {
        var fakeId = 'local_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        data.id = fakeId;
        var arr = _getCtLocalData(idx);
        arr.push(data);
        _setCtLocalData(idx, arr);
        
        _ctAppendRow(idx, data);
        ctHideInputRow(idx);
        _ctClearInputRow(idx);
        _ctRecalcFooter(idx);
        return;
    }

    _ctApiSave(apiUrl, null, data, idx, function(saved) {
        _ctAppendRow(idx, saved);
        ctHideInputRow(idx);
        _ctClearInputRow(idx);
        _ctRecalcFooter(idx);
    });
}

function ctOpenModal(idx, btn, isNew) {
    var tr    = btn.closest('tr');
    var meta  = _ctGetMeta(idx);
    var MN    = meta.model_name || '';
    var modal = document.getElementById('ct-modal-' + idx);

    var setupModal = function(obj) {
        document.querySelectorAll('#ct-modal-' + idx + ' [name]').forEach(function(el) {
            var v = obj[el.name];
            if (v === undefined || v === null) return;
            if (el.type === 'checkbox') el.checked = !!v; else el.value = v;
        });
        modal.style.display = 'flex';
        setTimeout(function() { modal.classList.add('is-visible'); }, 10);
    };

    if (isNew) {
        document.getElementById('ct-modal-id-' + idx).value = '';
        var data = {};
        tr.querySelectorAll('[data-field] .ct-cell-input').forEach(function(inp) {
            data[inp.name] = inp.type === 'checkbox' ? inp.checked : inp.value;
        });
        setupModal(data);
        return;
    }

    var id = tr.dataset.id;
    document.getElementById('ct-modal-id-' + idx).value = id;

    if (String(id).startsWith('local_')) {
        var arr = _getCtLocalData(idx);
        var item = arr.find(function(x) { return x.id === id; }) || {};
        setupModal(item);
        return;
    }

    var _apiBase = meta.api_url || ('/api/erp/' + MN.replace(/_/g, '-') + '/');
    var fetchUrl = _apiBase.replace(/\/$/, '') + '/' + id + '/';
    fetch(fetchUrl).then(function(r) { return r.json(); }).then(function(d) {
        setupModal(d.data || d);
    }).catch(function() {
        var data = {};
        tr.querySelectorAll('td[data-field]').forEach(function(td) { data[td.dataset.field] = td.dataset.raw; });
        setupModal(data);
    });
}

function ctCloseModal(idx, e) {
    var modal = document.getElementById('ct-modal-' + idx);
    if (e && e.target !== modal) return;
    modal.classList.remove('is-visible');
    setTimeout(function() { modal.style.display = 'none'; }, 200);
}

function ctSaveModal(idx, apiUrl, fkCol, parentId) {
    var id   = document.getElementById('ct-modal-id-' + idx).value;
    var meta = _ctGetMeta(idx);
    var data = {};
    data[fkCol] = parentId;
    document.querySelectorAll('#ct-modal-' + idx + ' [name]').forEach(function(el) {
        if (el.type === 'checkbox') data[el.name] = el.checked;
        else if (el.value !== '') data[el.name] = el.value;
    });
    if (!data['qty'])           data['qty']           = '1';
    if (!data['unit_price'])    data['unit_price']    = '0';
    if (!data['discount_pct'])  data['discount_pct']  = '0';
    if (!data['description'] && data['product_id']) {
        var prodSel = document.querySelector('#ct-modal-' + idx + ' [name="product_id"]');
        if (prodSel && prodSel.selectedIndex > 0)
            data['description'] = prodSel.options[prodSel.selectedIndex].text;
    }

    if (!id && (!parentId || parentId === 'None' || parentId === 'null')) {
        var fakeId = 'local_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        data.id = fakeId;
        var arr = _getCtLocalData(idx);
        arr.push(data);
        _setCtLocalData(idx, arr);
        
        _ctAppendRow(idx, data);
        _ctClearInputRow(idx);
        ctHideInputRow(idx);
        ctCloseModal(idx);
        _ctRecalcFooter(idx);
        return;
    }

    if (id && String(id).startsWith('local_')) {
        var arr = _getCtLocalData(idx);
        var item = arr.find(function(x) { return x.id === id; });
        if (item) {
            Object.assign(item, data);
            _setCtLocalData(idx, arr);
            
            var tr = document.querySelector('#ct-tbody-' + idx + ' tr[data-id="' + id + '"]');
            if (tr) {
                (meta.all_vcols || meta.vcols || []).forEach(function(field) {
                    var td = tr.querySelector('td[data-field="' + field + '"]');
                    if (!td) return;
                    var raw = item[field];
                    var display = (meta.rel_maps && meta.rel_maps[field] && raw != null)
                        ? (meta.rel_maps[field][String(raw)] || raw) : raw;
                    td.dataset.raw = raw != null ? raw : '';
                    td.textContent = display != null ? display : '—';
                });
            }
            ctCloseModal(idx);
            _ctRecalcFooter(idx);
        }
        return;
    }

    _ctApiSave(apiUrl, id || null, data, idx, function(saved) {
        if (id) {
            var tr = document.querySelector('#ct-tbody-' + idx + ' tr[data-id="' + id + '"]');
            if (tr) {
                (meta.all_vcols || meta.vcols || []).forEach(function(field) {
                    var td = tr.querySelector('td[data-field="' + field + '"]');
                    if (!td) return;
                    var raw = saved[field];
                    var display = (meta.rel_maps && meta.rel_maps[field] && raw != null)
                        ? (meta.rel_maps[field][String(raw)] || raw) : raw;
                    td.dataset.raw = raw != null ? raw : '';
                    td.textContent = display != null ? display : '—';
                });
            }
        } else {
            _ctAppendRow(idx, saved);
            ctHideInputRow(idx);
            _ctClearInputRow(idx);
        }
        ctCloseModal(idx);
        _ctRecalcFooter(idx);
    });
}

function ctDeleteRow(idx, btn) {
    var tr = btn.closest('tr');
    var id = tr.dataset.id;
    if (!confirm('Delete this row?')) return;
    
    if (String(id).startsWith('local_')) {
        var arr = _getCtLocalData(idx);
        arr = arr.filter(function(x) { return x.id !== id; });
        _setCtLocalData(idx, arr);
        tr.remove();
        _ctRecalcFooter(idx);
        var tbody = document.getElementById('ct-tbody-' + idx);
        var empty = document.getElementById('ct-empty-' + idx);
        if (empty) empty.style.display = tbody.querySelectorAll('.ct-data-row').length === 0 ? '' : 'none';
        return;
    }

    var meta   = _ctGetMeta(idx);
    var MN     = meta.model_name || '';
    var apiUrl = meta.api_url || ('/api/erp/' + MN.replace(/_/g, '-') + '/');
    fetch(apiUrl.replace(/\/$/, '') + '/' + id + '/', {method: 'DELETE', headers: {'X-CSRFToken': _ctGetCsrf()}})
    .then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.ok !== false) {
            tr.remove();
            _ctRecalcFooter(idx);
            var tbody = document.getElementById('ct-tbody-' + idx);
            var empty = document.getElementById('ct-empty-' + idx);
            if (empty) empty.style.display = tbody.querySelectorAll('.ct-data-row').length === 0 ? '' : 'none';
        }
    });
}

function ctOnProductChange(idx, sel) {
    var prefix = 'ct-' + idx + '-';
    _ctLoadPrice(idx, sel.value,
        document.getElementById(prefix + 'qty'),
        document.getElementById(prefix + 'unit_price'),
        document.getElementById(prefix + 'description'),
        document.getElementById(prefix + 'uom_id'), prefix);
}

function ctOnProductChangeModal(idx, sel) {
    var prefix = 'ct-modal-' + idx + '-';
    _ctLoadPrice(idx, sel.value,
        document.getElementById(prefix + 'qty'),
        document.getElementById(prefix + 'unit_price'),
        document.getElementById(prefix + 'description'),
        document.getElementById(prefix + 'uom_id'), prefix);
}

/* ── Private helpers ── */

function _ctGetMeta(idx) {
    try { return JSON.parse(document.getElementById('ct-meta-' + idx).textContent); }
    catch(e) { return {}; }
}

function _ctApplyColVis(idx, field, visible) {
    var t = document.getElementById('ct-table-' + idx);
    var f = document.getElementById('ct-footer-' + idx);
    if (t) t.querySelectorAll('[data-field="' + field + '"]').forEach(function(el) { el.style.display = visible ? '' : 'none'; });
    if (f) f.querySelectorAll('[data-total-field="' + field + '"]').forEach(function(el) { el.style.display = visible ? '' : 'none'; });
}

function _ctClearInputRow(idx) {
    var row = document.getElementById('ct-input-row-' + idx);
    if (!row) return;
    row.querySelectorAll('.ct-cell-input').forEach(function(el) {
        if (el.type === 'checkbox') el.checked = false; else el.value = '';
    });
}

function _ctLoadPrice(idx, productId, qtyEl, priceEl, descEl, uomEl, prefix) {
    var meta = _ctGetMeta(idx);
    if (!meta.price_api || !productId) return;
    var qty  = qtyEl ? (parseFloat(qtyEl.value) || 1) : 1;
    var plEl = meta.price_list_field ? document.querySelector(meta.price_list_field) : null;
    var plId = plEl ? (plEl.value || null) : null;
    var url  = meta.price_api + '?product_id=' + productId + '&qty=' + qty +
               '&price_type=' + (meta.price_type || 'sales') +
               (meta.company_id ? '&company_id=' + meta.company_id : '') +
               (plId ? '&price_list_id=' + plId : '');
    fetch(url).then(function(r) { return r.json(); }).then(function(d) {
        if (!d.ok) return;
        if (priceEl && !priceEl.dataset.manualEdit) priceEl.value = d.unit_price || '';
        if (descEl  && !descEl.dataset.manualEdit)  descEl.value  = d.description || '';
        if (uomEl) uomEl.value = d.uom_id || '';
        var accEl = document.getElementById(prefix + 'account_id');
        if (accEl && d.account_id) accEl.value = d.account_id;
        _ctRecalcRow(idx, prefix);
    }).catch(function() {});
}

function _ctRecalcRow(idx, prefix) {
    var qty   = parseFloat((document.getElementById(prefix + 'qty')          || {}).value) || 0;
    var price = parseFloat((document.getElementById(prefix + 'unit_price')   || {}).value) || 0;
    var disc  = parseFloat((document.getElementById(prefix + 'discount_pct') || {}).value) || 0;
    var subEl = document.getElementById(prefix + 'subtotal');
    if (subEl) subEl.value = (qty * price * (1 - disc / 100)).toFixed(4);
}

function _ctBindCalc(idx, prefix) {
    ['qty', 'unit_price', 'discount_pct'].forEach(function(f) {
        var el = document.getElementById(prefix + f);
        if (el) el.addEventListener('input', function() { _ctRecalcRow(idx, prefix); });
    });
    ['unit_price', 'description'].forEach(function(f) {
        var el = document.getElementById(prefix + f);
        if (el) el.addEventListener('input', function() { this.dataset.manualEdit = '1'; });
    });
}

function _ctRecalcFooter(idx) {
    var meta = _ctGetMeta(idx);
    if (!meta.footer_totals || !meta.footer_totals.length) return;
    var footer = document.getElementById('ct-footer-' + idx);
    if (!footer) return;
    meta.footer_totals.forEach(function(field) {
        var sum = 0;
        document.querySelectorAll('#ct-tbody-' + idx + ' .ct-data-row td[data-field="' + field + '"]').forEach(function(td) {
            sum += parseFloat(td.dataset.raw || td.textContent) || 0;
        });
        var fc = footer.querySelector('[data-total-field="' + field + '"]');
        if (fc) fc.innerHTML = '<strong>' + sum.toFixed(2) + '</strong>';
    });
}

function _ctResolveDisplay(idx, field, raw) {
    /* 1. rel_maps lookup (pre-loaded at page render) */
    var meta = _ctGetMeta(idx);
    if (meta.rel_maps && meta.rel_maps[field] && raw != null) {
        var label = meta.rel_maps[field][String(raw)];
        if (label != null) return label;
    }
    /* 2. read selected option text from the inline input row */
    var sel = document.getElementById('ct-' + idx + '-' + field);
    if (sel && sel.tagName === 'SELECT' && sel.selectedIndex >= 0) {
        var txt = sel.options[sel.selectedIndex].text;
        if (txt && txt !== '—') return txt;
    }
    return raw;
}

function _ctAppendRow(idx, obj) {
    var meta   = _ctGetMeta(idx);
    var tbody  = document.getElementById('ct-tbody-' + idx);
    var empty  = document.getElementById('ct-empty-' + idx);
    var seq    = tbody.querySelectorAll('.ct-data-row').length + 1;
    var tr     = document.createElement('tr');
    tr.className  = 'ct-data-row';
    tr.dataset.id = obj.id;

    var seqTd = document.createElement('td');
    seqTd.className = 'ct-td-seq';
    seqTd.style.cssText = 'color:var(--aras-ink-3);font-size:11px;';
    seqTd.textContent = seq;
    tr.appendChild(seqTd);

    var allCols  = meta.all_vcols || meta.vcols || [];
    var visCols  = new Set(meta.vcols || []);
    allCols.forEach(function(field) {
        var td  = document.createElement('td');
        var raw = obj[field];
        td.dataset.field = field;
        td.dataset.raw   = raw != null ? raw : '';
        var display = _ctResolveDisplay(idx, field, raw);
        td.textContent = display != null ? display : '—';
        if (!visCols.has(field)) td.style.display = 'none';
        tr.appendChild(td);
    });

    var actTd = document.createElement('td');
    actTd.className = 'ct-td-actions';
    actTd.innerHTML = '<button type="button" class="ct-btn-edit" title="Edit" onclick="ctOpenModal(\'' + idx + '\', this)"><i class="fa fa-pencil"></i></button>'
                    + '<button type="button" class="ct-btn-del" title="Delete" onclick="ctDeleteRow(\'' + idx + '\', this)"><i class="fa fa-trash"></i></button>';
    tr.appendChild(actTd);

    var inputRow = document.getElementById('ct-input-row-' + idx);
    if (inputRow) tbody.insertBefore(tr, inputRow); else tbody.appendChild(tr);
    if (empty) empty.style.display = 'none';
}

function _ctApiSave(apiUrl, id, data, idx, cb) {
    var url = id ? apiUrl + id + '/' : apiUrl;
    fetch(url, {
        method: id ? 'PUT' : 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': _ctGetCsrf()},
        body: JSON.stringify(data)
    }).then(function(r) { return r.json(); }).then(function(d) {
        if (d.ok === false) { alert(d.error || 'Error saving'); return; }
        cb(d.data || d);
    }).catch(function(e) { alert('Network error: ' + e); });
}

function _ctGetCsrf() {
    var m = document.cookie.match(/csrf_token=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
}
