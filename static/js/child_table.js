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
    if (!modal) return;

    var setupModal = function(obj) {
        if (!obj) return;
        document.querySelectorAll('#ct-modal-' + idx + ' [name]').forEach(function(el) {
            var name = el.name;
            var v = obj[name];
            
            // Try alternatives for FK fields
            if ((v === undefined || v === null || v === '') && name.endsWith('_id')) {
                var baseName = name.substring(0, name.length - 3);
                if (obj[baseName] !== undefined && obj[baseName] !== null && typeof obj[baseName] !== 'object') v = obj[baseName];
            }
            if ((v === undefined || v === null || v === '') && !name.endsWith('_id')) {
                if (obj[name + '_id'] !== undefined) v = obj[name + '_id'];
            }
            
            if (v === undefined || v === null) return; // Don't overwrite with null if we don't have to

            if (el.type === 'checkbox') {
                if (typeof v === 'string') {
                    el.checked = (v.toLowerCase() === 'true' || v === '1' || v === 'True');
                } else {
                    el.checked = !!v;
                }
            } else {
                if (el.type === 'date' && typeof v === 'string' && v.includes('T')) {
                    v = v.split('T')[0];
                }
                el.value = v;
                // Manually update the custom select UI without firing 'change' to avoid API fetch loops
                if (el.tagName === 'SELECT') {
                    var wrapper = el.closest('.aras-custom-select');
                    if (wrapper) {
                        var label = wrapper.querySelector('.aras-select-trigger span');
                        if (label && el.selectedIndex >= 0) {
                            label.textContent = el.options[el.selectedIndex].text;
                        }
                        wrapper.querySelectorAll('.aras-select-option').forEach(function(opt) {
                            opt.classList.toggle('is-selected', opt.dataset.value === String(v));
                        });
                    }
                }
            }
        });
        modal.classList.remove('d-none');
        modal.style.display = 'flex';
        if (!modal.classList.contains('is-visible')) {
            setTimeout(function() {
                modal.classList.add('is-visible');
                // Init TomSelect on modal selects that haven't been initialized yet
                if (window.TomSelect && window.ArasDesign) {
                    ArasDesign.initComponentLibrary();
                } else if (window.TomSelect) {
                    modal.querySelectorAll('select:not([data-tom-select])').forEach(function(sel) {
                        if (sel.dataset.tomSelect || sel.multiple || sel.disabled) return;
                        var addUrl = sel.getAttribute('data-rel-add-url') || '';
                        var ts = new TomSelect(sel, {
                            create: false, allowEmptyOption: true,
                            plugins: ['dropdown_input'],
                            render: { no_results: function(d, e) { return '<div class="ts-no-results">No matches for "' + e(d.input) + '"</div>'; } }
                        });
                        sel.dataset.tomSelect = "true";
                        if (addUrl) {
                            var attach = function() {
                                if (ts.dropdown.querySelector('.ts-add-new')) return;
                                var foot = document.createElement('a');
                                foot.className = 'ts-add-new'; foot.href = addUrl; foot.target = '_blank';
                                foot.innerHTML = '<i class="fa fa-plus"></i><span>Add new</span>';
                                foot.addEventListener('mousedown', function(e) { e.stopPropagation(); });
                                foot.addEventListener('click', function() { setTimeout(function(){ try{ts.close();}catch(_){} }, 0); });
                                var iw = ts.dropdown.querySelector('.dropdown-input-wrap');
                                if (iw) iw.parentNode.insertBefore(foot, iw.nextSibling);
                                else ts.dropdown.insertBefore(foot, ts.dropdown.firstChild);
                            };
                            attach(); ts.on('dropdown_open', attach);
                        }
                    });
                }
            }, 10);
        }
    };

    if (isNew) {
        document.getElementById('ct-modal-id-' + idx).value = '';
        var data = {};
        tr.querySelectorAll('.ct-cell-input').forEach(function(inp) {
            data[inp.name] = inp.type === 'checkbox' ? inp.checked : inp.value;
        });
        setupModal(data);
        return;
    }

    var id = tr.dataset.id;
    document.getElementById('ct-modal-id-' + idx).value = id;

    // Populate immediately from row data
    var rowData = {};
    tr.querySelectorAll('td[data-field]').forEach(function(td) {
        var f = td.dataset.field;
        var r = td.dataset.raw;
        if (r !== undefined && r !== null) {
            rowData[f] = r;
            // Map display field to _id if it looks like an ID
            if (!f.endsWith('_id') && !isNaN(parseInt(r)) && String(parseInt(r)) === String(r)) {
                rowData[f + '_id'] = r;
            }
        }
    });
    
    // Also merge from rel_maps if row data is missing something
    if (meta.rel_maps) {
        for (var f in meta.rel_maps) {
            var td = tr.querySelector('td[data-field="' + f + '"]');
            if (td && td.dataset.raw) {
                if (!rowData[f]) rowData[f] = td.dataset.raw;
                var fid = f.endsWith('_id') ? f : f + '_id';
                if (!rowData[fid]) rowData[fid] = td.dataset.raw;
            }
        }
    }

    setupModal(rowData);

    if (id && String(id).startsWith('local_')) {
        var arr = _getCtLocalData(idx);
        var item = arr.find(function(x) { return x.id === id; }) || {};
        setupModal(Object.assign({}, rowData, item));
        return;
    }

    var _apiBase = meta.api_url || ('/api/erp/' + MN.replace(/_/g, '-') + '/');
    var fetchUrl = _apiBase.replace(/\/$/, '') + '/' + id + '/';
    fetch(fetchUrl).then(function(r) { return r.json(); }).then(function(d) {
        var apiData = d.data || d;
        // Use a smart merge that doesn't overwrite with nulls
        var finalData = Object.assign({}, rowData);
        for (var key in apiData) {
            if (apiData[key] !== null && apiData[key] !== undefined && apiData[key] !== '') {
                finalData[key] = apiData[key];
            }
        }
        setupModal(finalData);
    }).catch(function() {
        // Fallback already handled
    });
}

function ctCloseModal(idx, e) {
    var modal = document.getElementById('ct-modal-' + idx);
    if (!modal) return;
    if (e && e.target !== modal) return;
    modal.classList.remove('is-visible');
    setTimeout(function() { 
        modal.style.display = 'none'; 
        modal.classList.add('d-none');
    }, 200);
}

function ctSaveModal(idx, apiUrl, fkCol, parentId) {
    var id   = document.getElementById('ct-modal-id-' + idx).value;
    var meta = _ctGetMeta(idx);
    
    // Normalize params
    var _apiUrl = (apiUrl === 'None' || apiUrl === 'null' || !apiUrl) ? meta.api_url : apiUrl;
    var _parentId = (parentId === 'None' || parentId === 'null') ? null : parentId;

    var data = {};
    if (_parentId) data[fkCol] = _parentId;
    
    document.querySelectorAll('#ct-modal-' + idx + ' [name]').forEach(function(el) {
        if (!el.name) return;
        if (el.type === 'checkbox') data[el.name] = el.checked;
        else data[el.name] = el.value; // Send empty string instead of omitting
    });

    // Capture labels from modal selects for instant UI update
    var modalLabels = {};
    document.querySelectorAll('#ct-modal-' + idx + ' select[name]').forEach(function(sel) {
        if (sel.selectedIndex >= 0) {
            var txt = sel.options[sel.selectedIndex].text;
            if (txt && txt !== '—') modalLabels[sel.name] = txt;
        }
    });

    // Apply defaults for common numeric fields if empty
    ['qty', 'unit_price', 'discount_pct', 'amount', 'subtotal'].forEach(function(f) {
        if (data[f] === undefined) {
            var el = document.getElementById('ct-modal-' + idx + '-' + f);
            if (el) data[f] = (f === 'qty') ? '1' : '0';
        }
    });
    
    if (!data['description'] && data['product_id'] && modalLabels['product_id']) {
        data['description'] = modalLabels['product_id'];
    }

    var updateRowUI = function(tr, obj) {
        var allCols = meta.all_vcols || meta.vcols || [];
        allCols.forEach(function(field) {
            var td = tr.querySelector('td[data-field="' + field + '"]');
            if (!td) return;
            var raw = obj[field];
            if (raw === undefined && id && !String(id).startsWith('local_')) {
                raw = td.dataset.raw;
            }
            var display = (meta.rel_maps && meta.rel_maps[field] && raw != null)
                ? (meta.rel_maps[field][String(raw)] || raw) 
                : (modalLabels[field] || raw);
            
            td.dataset.raw = raw != null ? raw : '';
            td.textContent = (display != null && display !== '') ? display : '—';
        });
    };

    if (!id && (!_parentId || !_apiUrl)) {
        var fakeId = 'local_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        data.id = fakeId;
        var arr = _getCtLocalData(idx);
        arr.push(data);
        _setCtLocalData(idx, arr);
        _ctAppendRow(idx, data, modalLabels);
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
            if (tr) updateRowUI(tr, item);
            ctCloseModal(idx);
            _ctRecalcFooter(idx);
        }
        return;
    }

    if (!_apiUrl) { 
        arasNotify('Error: No API URL found for this child table. If you are adding a new record, please ensure the parent is saved first.', 'error'); 
        return; 
    }

    _ctApiSave(_apiUrl, id || null, data, idx, function(saved) {
        if (id) {
            var tr = document.querySelector('#ct-tbody-' + idx + ' tr[data-id="' + id + '"]');
            if (tr) updateRowUI(tr, saved);
        } else {
            _ctAppendRow(idx, saved, modalLabels);
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

function _ctAppendRow(idx, obj, extraLabels) {
    var meta   = _ctGetMeta(idx);
    var tbody  = document.getElementById('ct-tbody-' + idx);
    var empty  = document.getElementById('ct-empty-' + idx);
    var seq    = tbody.querySelectorAll('.ct-data-row').length + 1;
    var tr     = document.createElement('tr');
    tr.className  = 'ct-data-row';
    tr.dataset.id = obj.id;

    var seqTd = document.createElement('td');
    seqTd.className = 'ct-td-seq text-center text-muted-aras fs-11';
    seqTd.style.padding = '14px 20px';
    seqTd.textContent = seq;
    tr.appendChild(seqTd);

    var allCols  = meta.all_vcols || meta.vcols || [];
    var visCols  = new Set(meta.vcols || []);
    allCols.forEach(function(field) {
        var td  = document.createElement('td');
        var raw = obj[field];
        // If field is like 'product' (display) but 'product_id' exists in obj, use that for data-raw
        if ((raw === undefined || raw === null || typeof raw === 'object') && obj[field + '_id'] !== undefined) {
            raw = obj[field + '_id'];
        }
        td.dataset.field = field;
        td.dataset.raw   = (raw != null && typeof raw !== 'object') ? raw : '';
        
        var display = _ctResolveDisplay(idx, field, raw);
        if ((display === raw || display == null) && extraLabels && extraLabels[field]) {
            display = extraLabels[field];
        }
        
        td.textContent = display != null ? display : '—';
        if (!visCols.has(field)) td.style.display = 'none';
        td.style.padding = '14px 20px';
        td.style.borderBottom = '1px solid var(--studio-cream)';
        tr.appendChild(td);
    });

    var actTd = document.createElement('td');
    actTd.className = 'ct-td-actions text-right';
    actTd.style.padding = '8px 20px';
    actTd.style.borderBottom = '1px solid var(--studio-cream)';
    actTd.innerHTML = '<button type="button" class="ct-btn-edit" title="Edit" onclick="ctOpenModal(\'' + idx + '\', this)" style="background:none;border:none;padding:6px;cursor:pointer;color:var(--aras-ink-3);"><i class="fa fa-pencil"></i></button>'
                    + '<button type="button" class="ct-btn-del" title="Delete" onclick="ctDeleteRow(\'' + idx + '\', this)" style="background:none;border:none;padding:6px;cursor:pointer;color:var(--aras-ink-3);"><i class="fa fa-trash"></i></button>';
    tr.appendChild(actTd);

    var inputRow = document.getElementById('ct-input-row-' + idx);
    if (inputRow) tbody.insertBefore(tr, inputRow); else tbody.appendChild(tr);
    if (empty) empty.style.display = 'none';
}

function _ctApiSave(apiUrl, id, data, idx, cb) {
    var base = apiUrl.endsWith('/') ? apiUrl : apiUrl + '/';
    var url = id ? base + id + '/' : base;
    
    fetch(url, {
        method: id ? 'PUT' : 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': _ctGetCsrf()},
        body: JSON.stringify(data)
    }).then(function(r) { 
        if (!r.ok) {
            return r.text().then(function(text) {
                var err;
                try { err = JSON.parse(text); } catch(e) { err = {error: text}; }
                throw new Error(err.error || err.message || ('Server error ' + r.status + ': ' + text.substring(0, 100)));
            });
        }
        return r.json(); 
    }).then(function(d) {
        if (d.ok === false) { arasNotify(d.error || 'Error saving', 'error'); return; }
        cb(d.data || d);
    }).catch(function(e) { 
        arasNotify('Save failed: ' + e.message, 'error'); 
        console.error('Child table save error:', e);
    });
}

function _ctGetCsrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.content;
    var m = document.cookie.match(/csrf_token=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
}

function ctFilterPriceList(idx, priceType) {
    var sel = document.getElementById('ct-' + idx + '-price_list_id');
    if (!sel) return;
    sel.value = '';
    Array.from(sel.options).forEach(function(opt) {
        if (!opt.value) return;
        var pt = opt.getAttribute('data-price-type');
        opt.style.display = (pt && priceType && pt !== priceType) ? 'none' : '';
    });
}

function ctFilterPriceListModal(idx, priceType) {
    var sel = document.getElementById('ct-modal-' + idx + '-price_list_id');
    if (!sel) return;
    sel.value = '';
    Array.from(sel.options).forEach(function(opt) {
        if (!opt.value) return;
        var pt = opt.getAttribute('data-price-type');
        opt.style.display = (pt && priceType && pt !== priceType) ? 'none' : '';
    });
}
