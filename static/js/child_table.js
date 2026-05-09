/* 
  #ChildListViewRelated 
  child_table.js — Client-side orchestration for dynamic child tables.
*/

/**
 * GLOBAL NAMESPACE & HOOK SYSTEM
 * Allows registering custom behaviors for specific models or fields.
 */
window.Aras = window.Aras || {};
Aras.ChildTable = {
    hooks: {}, // { model_name: { field_name: handler } }
    
    /** Registers a callback for a field change in any child table. */
    registerHook: function(model, field, handler) {
        if (!this.hooks[model]) this.hooks[model] = {};
        this.hooks[model][field] = handler;
    },

    /** Executes a hook if registered. Internal use. */
    triggerHook: async function(model, field, ctx) {
        console.log('Aras.ChildTable.triggerHook:', model, field, ctx.value);
        // Try specific model hook first
        if (this.hooks[model] && this.hooks[model][field]) {
            console.log('  Executing specific hook for', model);
            return await this.hooks[model][field](ctx);
        }
        // Fallback to generic hook
        if (this.hooks['*'] && this.hooks['*'][field]) {
            console.log('  Executing generic hook for', field);
            return await this.hooks['*'][field](ctx);
        }
        console.log('  No hook found for', model, field);
        return false;
    }
};

/**
 * GENERIC FIELD BEHAVIORS
 * Default logic for product/price resolution used by ERP modules.
 * Note: These can be overridden by registering hooks for specific models.
 */
Aras.ChildTable.registerHook('*', 'product_id', async (ctx) => {
    if (!ctx.meta.price_api || !ctx.value) return;
    
    /* Reset manual-edit flags to allow fresh data to overwrite old values. */
    ctx.setFieldData('unit_price', {manualEdit: ''});
    ctx.setFieldData('description', {manualEdit: ''});
    
    /* Clear UoM field so the backend resolves the product's default UOM. */
    ctx.setFieldValue('uom_id', '');

    _ctLoadPrice(ctx.idx, ctx.value, 
        ctx.getField('qty'),
        ctx.getField('unit_price'),
        ctx.getField('description'),
        ctx.getField('uom_id'),
        ctx.prefix);
});

Aras.ChildTable.registerHook('*', 'uom_id', async (ctx) => {
    if (!ctx.meta.price_api || !ctx.value) return;
    
    var prodEl = ctx.getField('product_id');
    var pid = prodEl ? (prodEl.tomselect ? prodEl.tomselect.getValue() : prodEl.value) : '';
    if (!pid) return;

    /* When UOM changes, we fetch the specific price for that UOM. */
    _ctLoadPrice(ctx.idx, pid, 
        ctx.getField('qty'),
        ctx.getField('unit_price'),
        ctx.getField('description'),
        ctx.getField('uom_id'),
        ctx.prefix);
});

/* Example of model-specific customization for Invoices */
Aras.ChildTable.registerHook('acc_purchase_invoice_line', 'product_id', async (ctx) => {
    // We just reuse the generic logic for now, but this shows where to add 
    // invoice-specific logic (e.g. checking project_id or warehouse_id).
    return await Aras.ChildTable.triggerHook('*', 'product_id', ctx);
});
Aras.ChildTable.registerHook('acc_sales_invoice_line', 'product_id', async (ctx) => {
    return await Aras.ChildTable.triggerHook('*', 'product_id', ctx);
});

/**
 * Initializes a child table instance.
 */
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

    /* Bind to static parts (Input row + Modal) */
    var modal = document.querySelector('[data-ct-modal="'+li+'"]');
    if (modal) _ctBindHooks(li, 'ct-modal-' + li + '-', modal);
    
    var inputRow = document.getElementById('ct-input-row-' + li);
    if (inputRow) _ctBindHooks(li, 'ct-' + li + '-', inputRow);
}

/* ── Public API (called from HTML templates via onclick) ── */

/** Toggles visibility of the column picker popover. */
function toggleCtSettings(idx, e) {
    if (e) e.stopPropagation();
    var p = document.getElementById('ct-settings-' + idx);
    if (p) p.style.display = p.style.display === 'none' ? 'block' : 'none';
}

/** Calculates and displays sum for columns defined in 'footer_totals'. */
function toggleCtTotals(idx) {
    var footer = document.getElementById('ct-footer-' + idx);
    var btn    = document.getElementById('ct-totals-btn-' + idx);
    if (!footer) return;
    var show = footer.style.display === 'none';
    if (show) {
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

/** Applies column visibility setting. */
function applyCtColVis(idx, field, visible) { _ctApplyColVis(idx, field, visible); }

/** Persists column visibility preference to user profile via API. */
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

/** Reveals the hidden input row for adding new details. */
/** Append a fresh empty row in edit mode at the bottom of the table. */
function ctAddRow(idx) {
    var tbody = document.getElementById('ct-tbody-' + idx);
    if (!tbody) return;
    /* Commit any currently-editing row first so we never have two open at once. */
    _ctCloseAnyEdit(idx);
    var meta    = _ctGetMeta(idx);
    var allCols = meta.all_vcols || meta.vcols || [];
    var visCols = new Set(meta.vcols || []);
    var tr      = document.createElement('tr');
    tr.className     = 'ct-data-row';
    tr.dataset.id    = '';
    tr.dataset.isNew = '1';

    var seqTd = document.createElement('td');
    seqTd.className   = 'at__td ct-td-seq';
    seqTd.textContent = '*';
    tr.appendChild(seqTd);

    allCols.forEach(function(field) {
        var td = document.createElement('td');
        td.className = 'at__td ct-td-cell';
        td.dataset.field = field;
        td.dataset.raw   = '';
        if (!visCols.has(field)) td.style.display = 'none';
        var span = document.createElement('span');
        span.className = 'ct-cell-text';
        span.textContent = '—';
        td.appendChild(span);
        tr.appendChild(td);
    });

    var actTd = document.createElement('td');
    actTd.className = 'at__td ct-td-actions';
    actTd.innerHTML =
        '<div class="ct-row-actions">' +
        '  <button type="button" class="ct-row-btn" title="Edit in dialog" onclick="event.stopPropagation(); ctOpenModal(\'' + idx + '\', this)"><i class="fa fa-pencil"></i></button>' +
        '  <button type="button" class="ct-row-btn ct-row-btn--danger" title="Delete" onclick="ctRowDelete(\'' + idx + '\', this, event)"><i class="fa fa-times"></i></button>' +
        '</div>';
    tr.appendChild(actTd);

    tbody.appendChild(tr);
    var empty = document.getElementById('ct-empty-' + idx);
    if (empty) empty.classList.add('d-none');
    ctRowEdit(idx, tr);
}

/** Switch a row from read mode to edit mode. */
function ctRowEdit(idx, target, ev) {
    if (ev) {
        /* Avoid editing when user clicked an action button. */
        var t = ev.target;
        if (t && t.closest && t.closest('.ct-row-actions')) return;
        ev.stopPropagation();
    }
    var tr = target.tagName === 'TR' ? target : target.closest('tr');
    if (!tr || tr.classList.contains('is-editing')) return;
    _ctCloseAnyEdit(idx, tr);

    var meta    = _ctGetMeta(idx);
    var byName  = {};
    (meta.inline_columns || []).forEach(function(c) { byName[c.name] = c; });
    if (!Object.keys(byName).length) return;  /* no inline schema → bail */

    tr.classList.add('is-editing');
    var prefix = 'ct-' + idx + '-';
    tr.querySelectorAll('.ct-td-cell').forEach(function(td) {
        var field = td.dataset.field;
        var col   = byName[field];
        var raw   = td.dataset.raw || '';
        var span  = td.querySelector('.ct-cell-text');
        if (span) span.style.display = 'none';
        if (!col) return;  /* read-only display column */

        var input = _ctBuildInput(col, raw);
        input.classList.add('ct-cell-input');
        input.dataset.field = field;
        input.id = prefix + col.name;
        td.appendChild(input);
    });

    /* Hidden inputs for inline columns not represented as visible cells. */
    var renderedFields = new Set(Array.from(tr.querySelectorAll('.ct-td-cell')).map(function(td) { return td.dataset.field; }));
    (meta.inline_columns || []).forEach(function(col) {
        if (renderedFields.has(col.name)) return;
        var hid = document.createElement('input');
        hid.type = 'hidden'; hid.name = col.name; hid.id = prefix + col.name;
        hid.dataset.field = col.name;
        hid.classList.add('ct-cell-input', 'ct-cell-extra');
        tr.appendChild(hid);
    });

    tr.querySelectorAll('select.ct-cell-input').forEach(_ctEnhanceSelect);

    /* Bind UI logic (calcs + hooks) */
    _ctBindCalc(idx, prefix);
    _ctBindHooks(idx, prefix, tr);

    /* Bind keyboard shortcuts and focus first writable input. */
    var first = null;
    tr.querySelectorAll('.ct-cell-input').forEach(function(el) {
        if (el.type === 'hidden' || el.readOnly) return;
        if (!first) first = el;
        el.addEventListener('keydown', function(e) { _ctOnEditKey(idx, tr, e); });
    });

    /* Update actions to show Save/Cancel */
    var actTd = tr.querySelector('.ct-td-actions');
    if (actTd) {
        actTd.dataset.oldHtml = actTd.innerHTML;
        actTd.innerHTML =
            '<div class="ct-row-actions">' +
            '  <button type="button" class="ct-row-btn ct-row-btn--success" title="Save (Enter)" onclick="event.stopPropagation(); ctRowCommit(\'' + idx + '\', this.closest(\'tr\'))"><i class="fa fa-check"></i></button>' +
            '  <button type="button" class="ct-row-btn ct-row-btn--danger" title="Cancel (Esc)" onclick="event.stopPropagation(); ctRowCancel(\'' + idx + '\', this.closest(\'tr\'))"><i class="fa fa-times"></i></button>' +
            '</div>';
    }

    if (first) setTimeout(function() { first.focus(); first.select && first.select(); }, 30);
}

/** 
 * INTERNAL: Binds field hooks to all inputs within a container (row or modal).
 */
function _ctBindHooks(idx, prefix, container) {
    var meta = _ctGetMeta(idx);
    var MN   = meta.model_name || '';
    console.log('_ctBindHooks: container', container.id || 'unknown', 'MN', MN);

    container.querySelectorAll('[name]').forEach(function(el) {
        var fieldName = el.name;
        var fire = async function() {
            var val = el.tomselect ? el.tomselect.getValue() : el.value;
            console.log('Hook event fired for', fieldName, 'val', val);
            var ctx = {
                idx: idx,
                prefix: prefix,
                model: MN,
                fieldName: fieldName,
                value: val,
                meta: meta,
                container: container,
                getField: function(f) { 
                    var res = container.querySelector('[name="'+f+'"]') || document.getElementById(prefix + f); 
                    if (!res) console.warn('  getField failed for', f);
                    return res;
                },
                setFieldValue: function(f, v) {
                    var target = this.getField(f);
                    if (!target) return;
                    if (target.tomselect) target.tomselect.setValue(v, true);
                    else target.value = v;
                },
                setFieldData: function(f, data) {
                    var target = this.getField(f);
                    if (!target) return;
                    for (var k in data) target.dataset[k] = data[k];
                }
            };
            await Aras.ChildTable.triggerHook(MN, fieldName, ctx);
        };

        if (el.tomselect) {
            console.log('  Binding TS change to', fieldName);
            el.tomselect.on('change', fire);
        } else {
            console.log('  Binding standard change to', fieldName);
            el.addEventListener('change', fire);
        }
    });
}

/** Build a single <input>/<select>/<textarea> from an inline column descriptor. */
function _ctBuildInput(col, raw) {
    var el;
    if (col.type === 'select') {
        el = document.createElement('select');
        el.classList.add('aras-form-select');
        var blank = document.createElement('option');
        blank.value = ''; blank.textContent = '—';
        el.appendChild(blank);
        (col.options || []).forEach(function(opt) {
            var o = document.createElement('option');
            o.value = opt.value; o.textContent = opt.label;
            if (opt.price_type) o.setAttribute('data-price-type', opt.price_type);
            el.appendChild(o);
        });
        if (raw !== '' && raw != null) el.value = String(raw);
    } else if (col.type === 'textarea') {
        el = document.createElement('textarea');
        el.classList.add('aras-form-textarea');
        el.rows  = 1;
        el.value = raw;
    } else if (col.type === 'checkbox') {
        el = document.createElement('input');
        el.type = 'checkbox';
        el.classList.add('aras-form-check-input');
        el.checked = !!(raw && raw !== '0' && raw !== 'false');
    } else {
        el = document.createElement('input');
        el.type  = col.type || 'text';
        el.classList.add('aras-form-input');
        el.value = raw;
    }
    el.name = col.name;
    if (col.rel_add_url) el.setAttribute('data-rel-add-url', col.rel_add_url);
    if (col.readonly) { el.readOnly = true; el.tabIndex = -1; }
    if (col.required) el.required = true;
    return el;
}

/** Initialize TomSelect on a freshly-built inline edit select to match
 *  the generic combobox look (searchable + styled). Safe no-op when
 *  TomSelect is missing or already initialized. */
function _ctEnhanceSelect(el) {
    if (!el || el.tagName !== 'SELECT' || el.multiple) return;
    if (el.dataset.tomSelect || el.tomselect) return;
    if (!window.TomSelect) {
        return;
    }
    try {
        var ts = new TomSelect(el, {
            create: false,
            allowEmptyOption: true,
            plugins: ['dropdown_input'],
            render: {
                no_results: function(data, escape) {
                    return '<div class="ts-no-results">No matches for "' + escape(data.input) + '"</div>';
                }
            }
        });
        el.dataset.tomSelect = 'true';
        /* Mark wrapper so the closed-state CSS can adopt the inline cell look. */
        if (ts.wrapper) ts.wrapper.classList.add('ts-wrapper--inline');
        var addUrl = el.getAttribute('data-rel-add-url') || '';
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
                ts.dropdown.appendChild(foot);
            };
            attachAddNew();
            ts.on('dropdown_open', attachAddNew);
        }
    } catch (_) { /* fall back to native select */ }
}

/** Keyboard handling inside an editing row. */
function _ctOnEditKey(idx, tr, e) {
    if (e.key === 'Escape') {
        e.preventDefault();
        ctRowCancel(idx, tr);
    } else if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        ctRowCommit(idx, tr, /*advance=*/true);
    } else if (e.key === 'Tab') {
        /* Native Tab is fine; only intercept on the last cell to commit + advance. */
        var inputs = Array.from(tr.querySelectorAll('.ct-cell-input')).filter(function(el) {
            return el.type !== 'hidden' && !el.readOnly;
        });
        var last = inputs[inputs.length - 1];
        if (e.target === last && !e.shiftKey) {
            e.preventDefault();
            ctRowCommit(idx, tr, /*advance=*/true);
        }
    }
}

/** Discard edit; if the row was newly added, remove it. */
function ctRowCancel(idx, tr) {
    if (!tr || !tr.classList.contains('is-editing')) return;
    if (tr.dataset.isNew === '1') {
        tr.remove();
        _ctUpdateSeq(idx);
        return;
    }
    _ctRevertToReadMode(tr);
}

/** Persist the editing row (locally or via API) and revert to read mode. */
function ctRowCommit(idx, tr, advance) {
    if (!tr || !tr.classList.contains('is-editing')) return;
    var meta = _ctGetMeta(idx);
    var data = {};
    var byName = {};
    (meta.inline_columns || []).forEach(function(c) { byName[c.name] = c; });

    tr.querySelectorAll('.ct-cell-input').forEach(function(el) {
        if (el.type === 'checkbox') { data[el.name] = el.checked; return; }
        var v = el.value;
        if (v === '') return;
        if (el.tagName === 'SELECT' && /_id$/.test(el.name) && v === '0') return;
        data[el.name] = v;
    });

    /* Required validation. */
    var missing = [];
    (meta.inline_columns || []).forEach(function(c) {
        if (c.required && (data[c.name] === undefined || data[c.name] === '' || data[c.name] === null)) {
            missing.push(c.label || c.name);
        }
    });
    if (missing.length) {
        _ctShowRowError(tr, 'Required: ' + missing.join(', '));
        return;
    }

    /* Compute subtotal/defaults (preserves existing behaviour). */
    if (data['qty'] === undefined && byName['qty'])                 data['qty']          = '1';
    if (data['unit_price'] === undefined && byName['unit_price'])   data['unit_price']   = '0';
    if (data['discount_pct'] === undefined && byName['discount_pct']) data['discount_pct'] = '0';
    if (byName['subtotal']) {
        var qty   = parseFloat(data['qty'] || 1);
        var price = parseFloat(data['unit_price'] || 0);
        var disc  = parseFloat(data['discount_pct'] || 0);
        data['subtotal'] = (qty * price * (1 - disc / 100)).toFixed(4);
    }

    var fkCol    = meta.fk_col;
    var parentId = meta.parent_id;
    if (fkCol) data[fkCol] = parentId || _ctReadParentIdFromUrl();

    var existingId = tr.dataset.id;
    var isLocal    = !parentId || parentId === 'None' || parentId === 'null' || !existingId || String(existingId).startsWith('local_') || existingId === '';

    var finish = function(saved) {
        var arr = _getCtLocalData(idx);
        if (existingId && String(existingId).startsWith('local_')) {
            var i = arr.findIndex(function(x) { return x.id === existingId; });
            if (i !== -1) arr[i] = saved;
        } else if (!existingId) {
            arr.push(saved);
        }
        _setCtLocalData(idx, arr);
        _ctUpdateRowDisplay(idx, tr, saved);
        _ctRecalcFooter(idx);
        _ctUpdateSeq(idx);
        if (advance) {
            var next = tr.nextElementSibling;
            if (next && next.classList.contains('ct-data-row')) ctRowEdit(idx, next);
        }
    };

    if (isLocal) {
        var fakeId = existingId && String(existingId).startsWith('local_')
            ? existingId
            : 'local_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        data.id = fakeId;
        tr.dataset.id    = fakeId;
        tr.dataset.isNew = '';
        finish(data);
        return;
    }

    var apiUrl = meta.api_url;
    var saveId = (existingId && !String(existingId).startsWith('local_')) ? existingId : null;
    _ctApiSave(apiUrl, saveId, data, idx, function(saved) {
        if (saved && saved.id != null) tr.dataset.id = saved.id;
        tr.dataset.isNew = '';
        finish(saved || data);
    });
}

/** Revert a row to read mode using its current input values (or original raw). */
function _ctRevertToReadMode(tr) {
    tr.classList.remove('is-editing');
    tr.querySelectorAll('.ct-td-cell').forEach(function(td) {
        var input = td.querySelector('.ct-cell-input');
        if (input) {
            if (input.tomselect) input.tomselect.destroy();
            input.remove();
        }
        var span = td.querySelector('.ct-cell-text');
        if (span) span.style.display = '';
    });
    tr.querySelectorAll('.ct-cell-extra').forEach(function(el) { el.remove(); });
    
    var actTd = tr.querySelector('.ct-td-actions');
    if (actTd && actTd.dataset.oldHtml) {
        actTd.innerHTML = actTd.dataset.oldHtml;
        delete actTd.dataset.oldHtml;
    }

    var err = tr.querySelector('.ct-row-error');
    if (err) err.remove();
}

/** Update read-mode cells from a saved object, then exit edit mode. */
function _ctUpdateRowDisplay(idx, tr, obj) {
    /* Resolve labels first while the in-cell <select> is still present. */
    var pending = [];
    tr.querySelectorAll('.ct-td-cell').forEach(function(td) {
        var field = td.dataset.field;
        var raw   = obj[field];
        if ((raw === undefined || raw === null || typeof raw === 'object') && obj[field + '_id'] !== undefined) {
            raw = obj[field + '_id'];
        }
        td.dataset.raw = (raw != null && typeof raw !== 'object') ? raw : '';
        var display = _ctResolveDisplay(idx, field, raw, tr);
        pending.push({ td: td, display: display });
    });
    _ctRevertToReadMode(tr);
    pending.forEach(function(p) {
        var span = p.td.querySelector('.ct-cell-text');
        if (span) span.textContent = (p.display != null && p.display !== '') ? p.display : '—';
    });
}

/** Show an inline error pill below the row's cells. */
function _ctShowRowError(tr, msg) {
    var err = tr.querySelector('.ct-row-error');
    if (!err) {
        err = document.createElement('div');
        err.className = 'ct-row-error';
        var firstCell = tr.querySelector('.ct-td-cell');
        if (firstCell) firstCell.appendChild(err);
    }
    err.textContent = msg;
    setTimeout(function() { if (err && err.parentNode) err.remove(); }, 4000);
}

/** Close any other row currently in edit mode (auto-commit). */
function _ctCloseAnyEdit(idx, except) {
    var tbody = document.getElementById('ct-tbody-' + idx);
    if (!tbody) return;
    tbody.querySelectorAll('.ct-data-row.is-editing').forEach(function(tr) {
        if (tr === except) return;
        
        // If it's a new row, check if it has any significant data before committing.
        // We consider it "has data" if any field has a non-empty, non-zero value.
        var inputs = tr.querySelectorAll('.ct-cell-input');
        var hasData = false;
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var v = el.tomselect ? el.tomselect.getValue() : el.value;
            if (v && v !== '' && v !== '0' && v !== 'null' && v !== 'undefined') {
                hasData = true;
                break;
            }
        }

        if (hasData || tr.dataset.id) {
            ctRowCommit(idx, tr, /*advance=*/false);
        } else {
            tr.remove();
            _ctUpdateSeq(idx);
        }
    });
}

/** Delete a row from anywhere in its action cluster. */
function ctRowDelete(idx, btn, ev) {
    if (ev) ev.stopPropagation();
    var tr = btn.closest('tr');
    if (!tr) return;
    if (tr.dataset.isNew === '1' || !tr.dataset.id) {
        tr.remove();
        _ctUpdateSeq(idx);
        return;
    }
    /* Delegate to legacy ctDeleteRow which handles local + API delete. */
    ctDeleteRow(idx, btn);
}

/** Move a row up or down. Local-only ordering — server reorder is out of scope here. */
function ctRowMove(idx, btn, dir, ev) {
    if (ev) ev.stopPropagation();
    var tr = btn.closest('tr');
    if (!tr) return;
    var sib = dir < 0 ? tr.previousElementSibling : tr.nextElementSibling;
    if (!sib || !sib.classList.contains('ct-data-row')) return;
    if (dir < 0) tr.parentNode.insertBefore(tr, sib);
    else tr.parentNode.insertBefore(sib, tr);
    _ctUpdateSeq(idx);
}

/** Read parent id from the form action URL when meta.parent_id is missing (new parent). */
function _ctReadParentIdFromUrl() {
    var f = document.querySelector('form[action]');
    if (!f) return null;
    var m = f.action.split('/').filter(function(x) { return x.match(/^[0-9]+$/); }).pop();
    return m || null;
}

/* ── Legacy compat shims (older call sites still reference these) ── */
function ctHideInputRow(idx) {
    var tbody = document.getElementById('ct-tbody-' + idx);
    if (!tbody) return;
    var editing = tbody.querySelector('.ct-data-row.is-editing');
    if (editing) ctRowCancel(idx, editing);
}

/** Helper to retrieve local storage/hidden form field data. */
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

/** Updates hidden input with serialized local changes. */
function _setCtLocalData(idx, arr) {
    var inp = document.getElementById('ct-local-input-' + idx);
    if (inp) inp.value = JSON.stringify(arr);
}

/** Collects input, calculates subtotals, and saves inline row locally or via API. */
function ctSaveInlineRow(idx, apiUrl, fkCol, parentId) {
    var row = document.getElementById('ct-input-row-' + idx);
    var data = {};
    data[fkCol] = parentId;
    row.querySelectorAll('.ct-cell-input').forEach(function(el) {
        if (el.type === 'checkbox') { data[el.name] = el.checked; return; }
        if (el.value === '') return;
        // FK select sentinel "0" → omit (server treats missing as NULL)
        if (el.tagName === 'SELECT' && /_id$/.test(el.name) && el.value === '0') return;
        data[el.name] = el.value;
    });
    /* Auto-fill description */
    if (!data['description']) {
        var prodSel = document.getElementById('ct-' + idx + '-product_id');
        if (prodSel && prodSel.selectedIndex > 0) {
            data['description'] = prodSel.options[prodSel.selectedIndex].text;
        }
    }
    /* Apply defaults/recalc subtotal */
    if (!data['qty'])           data['qty']           = '1';
    if (!data['unit_price'])    data['unit_price']    = '0';
    if (!data['discount_pct'])  data['discount_pct']  = '0';
    var qty   = parseFloat(data['qty'] || 1);
    var price = parseFloat(data['unit_price'] || 0);
    var disc  = parseFloat(data['discount_pct'] || 0);
    data['subtotal'] = (qty * price * (1 - disc / 100)).toFixed(4);

    if (!parentId || parentId === 'None' || parentId === 'null' || parentId === '__PID__') {
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

/** Prepares and displays modal for full-form detail editing. */
function ctOpenModal(idx, btn, isNew) {
    var tr    = btn.closest('tr');
    var meta  = _ctGetMeta(idx);
    var MN    = meta.model_name || '';
    var modal = document.getElementById('ct-modal-' + idx);
    if (!modal) return;

    var setupModal = function(obj, isFirstCall) {
        if (!obj) return;
        var modalContent = document.querySelector('#ct-modal-' + idx);
        if (!modalContent) return;

        modalContent.querySelectorAll('[name]').forEach(function(el) {
            var name = el.name;
            if (isFirstCall) {
                if (el.type === 'checkbox') el.checked = false;
                else el.value = '';
            }

            var v = obj[name];
            if ((v === undefined || v === null || v === '') && name.endsWith('_id')) {
                var baseName = name.substring(0, name.length - 3);
                var baseVal = obj[baseName];
                if (baseVal !== undefined && baseVal !== null) {
                    if (typeof baseVal === 'object') v = baseVal.id || baseVal.value || baseVal.pk;
                    else v = baseVal;
                }
            }
            if ((v === undefined || v === null || v === '') && !name.endsWith('_id')) {
                if (obj[name + '_id'] !== undefined) v = obj[name + '_id'];
            }
            
            if (v === undefined || v === null) return; 

            if (el.type === 'checkbox') {
                if (typeof v === 'string') {
                    el.checked = (v.toLowerCase() === 'true' || v === '1' || v === 'true' || v === 'yes');
                } else {
                    el.checked = !!v;
                }
            } else {
                if (el.type === 'date' && typeof v === 'string') {
                    if (v.includes('T')) v = v.split('T')[0];
                    else if (v.includes(' ')) v = v.split(' ')[0];
                }
                el.value = v;

                if (el.tomselect) {
                    el.tomselect.setValue(v, true);
                }
            }
        });

        // HTMX config for save button
        var saveBtn = modalContent.querySelector('.ct-modal-save-btn');
        if (saveBtn) {
            var idVal = document.getElementById('ct-modal-id-' + idx).value;
            var saveUrl = '/admin/api/child-table/' + MN + '/save?parent_model=' + (meta.parent_model_name || '') + '&li=' + idx;
            
            var pId = meta.parent_id;
            if (!pId || pId === '__PID__' || pId === 'None') {
                var form = document.querySelector('form[action]');
                if (form) {
                    pId = form.action.split('/').filter(x => x.match(/^[0-9]+$/)).pop() || '';
                }
            }

            if (!pId || pId === '__PID__' || pId === 'None') {
                saveBtn.removeAttribute('hx-post');
                saveBtn.removeAttribute('hx-target');
                saveBtn.removeAttribute('hx-swap');
                saveBtn.removeAttribute('hx-vals');
                saveBtn.setAttribute('onclick', 'ctSaveModalRow(\'' + idx + '\')');
            } else if (isNew || !idVal || String(idVal).startsWith('local_')) {
                saveBtn.removeAttribute('onclick');
                saveBtn.setAttribute('hx-post', saveUrl);
                saveBtn.setAttribute('hx-target', '#ct-tbody-' + idx);
                saveBtn.setAttribute('hx-swap', 'beforeend');
                if (meta.fk_col) {
                    var vals = {}; vals[meta.fk_col] = pId;
                    saveBtn.setAttribute('hx-vals', JSON.stringify(vals));
                }
            } else {
                saveBtn.removeAttribute('onclick');
                saveBtn.setAttribute('hx-post', saveUrl + '&id=' + idVal);
                saveBtn.setAttribute('hx-target', '#ct-row-' + idx + '-' + idVal);
                saveBtn.setAttribute('hx-swap', 'outerHTML');
                saveBtn.removeAttribute('hx-vals');
            }
            if (window.htmx && saveBtn.hasAttribute('hx-post')) htmx.process(saveBtn);
        }

        modal.classList.remove('d-none');
        modal.style.display = 'flex';

        if (!modal.classList.contains('is-visible')) {
            setTimeout(function() {
                modal.classList.add('is-visible');
            }, 10);
        }
    };

    if (isNew) {
        document.getElementById('ct-modal-id-' + idx).value = '';
        var data = {};
        tr.querySelectorAll('.ct-cell-input').forEach(function(inp) {
            data[inp.name] = inp.type === 'checkbox' ? inp.checked : inp.value;
        });
        setupModal(data, true);
        return;
    }

    var id = tr.dataset.id;
    document.getElementById('ct-modal-id-' + idx).value = id;

    var rowData = {};
    /* Prefer live input values when the row is currently being inline-edited
       (pencil clicked mid-edit) — dataset.raw is stale until commit. */
    var isEditing = tr.classList.contains('is-editing');
    tr.querySelectorAll('td[data-field]').forEach(function(td) {
        var f = td.dataset.field;
        var r = td.dataset.raw;
        if (isEditing) {
            var inp = td.querySelector('.ct-cell-input');
            if (inp) r = (inp.type === 'checkbox') ? (inp.checked ? '1' : '') : inp.value;
        }
        if (r !== undefined && r !== null) {
            rowData[f] = r;
            if (!f.endsWith('_id') && !isNaN(parseInt(r)) && String(parseInt(r)) === String(r)) {
                rowData[f + '_id'] = r;
            }
        }
    });
    /* Also harvest hidden .ct-cell-extra inputs (inline cols not shown as cells). */
    if (isEditing) {
        tr.querySelectorAll('.ct-cell-extra').forEach(function(inp) {
            if (inp.name && inp.value !== '') rowData[inp.name] = inp.value;
        });
    }
    
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

    setupModal(rowData, true);

    if (id && String(id).startsWith('local_')) {
        var arr = _getCtLocalData(idx);
        var item = arr.find(function(x) { return x.id === id; }) || {};
        setupModal(Object.assign({}, rowData, item), false);
        return;
    }

    var _apiBase = meta.api_url || ('/api/erp/' + MN.replace(/_/g, '-') + '/');
    var fetchUrl = _apiBase.replace(/\/$/, '') + '/' + id + '/';
    fetch(fetchUrl).then(function(r) { return r.json(); }).then(function(d) {
        var apiData = d.data || d;
        var finalData = Object.assign({}, rowData);
        for (var key in apiData) {
            if (apiData[key] !== null && apiData[key] !== undefined && apiData[key] !== '') {
                finalData[key] = apiData[key];
            }
        }
        setupModal(finalData, false);
    }).catch(function() {});
}

/** Closes the editing modal and cleans up visible CSS classes. */
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

/** Saves modal form state locally (used as fallback for non-API tables). */
function ctSaveModalRow(idx) {
    var modal = document.getElementById('ct-modal-' + idx);
    var idVal = document.getElementById('ct-modal-id-' + idx).value;
    var data = {};
    
    modal.querySelectorAll('[name]').forEach(function(el) {
        if (el.type === 'checkbox') data[el.name] = el.checked;
        else if (el.value !== '') data[el.name] = el.value;
    });

    if (!data['qty'])           data['qty']           = '1';
    if (!data['unit_price'])    data['unit_price']    = '0';
    if (!data['discount_pct'])  data['discount_pct']  = '0';

    var qty   = parseFloat(data['qty'] || 1);
    var price = parseFloat(data['unit_price'] || 0);
    var disc  = parseFloat(data['discount_pct'] || 0);
    data['subtotal'] = (qty * price * (1 - disc / 100)).toFixed(4);

    var arr = _getCtLocalData(idx);
    if (idVal && String(idVal).startsWith('local_')) {
        var existingIdx = arr.findIndex(function(x) { return x.id === idVal; });
        if (existingIdx !== -1) {
            data.id = idVal;
            arr[existingIdx] = data;
            var tr = document.getElementById('ct-row-' + idx + '-' + idVal);
            if (tr) tr.remove();
        }
    } else {
        var fakeId = 'local_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        data.id = fakeId;
        arr.push(data);
    }
    
    _setCtLocalData(idx, arr);
    _ctAppendRow(idx, data);
    ctCloseModal(idx);
    _ctRecalcFooter(idx);
    _ctUpdateSeq(idx);
}

/* ── Internal Helpers ── */

/** Retrieves JSON metadata blob from the DOM. */
function _ctGetMeta(idx) {
    try { return JSON.parse(document.getElementById('ct-meta-' + idx).textContent); }
    catch(e) { return {}; }
}

/** Toggles column display property in both table and footer. */
function _ctApplyColVis(idx, field, visible) {
    var t = document.getElementById('ct-table-' + idx);
    var f = document.getElementById('ct-footer-' + idx);
    if (t) t.querySelectorAll('[data-field="' + field + '"]').forEach(function(el) { el.style.display = visible ? '' : 'none'; });
    if (f) f.querySelectorAll('[data-total-field="' + field + '"]').forEach(function(el) { el.style.display = visible ? '' : 'none'; });
}

/** Resets all inputs in the inline row. */
function _ctClearInputRow(idx) {
    var row = document.getElementById('ct-input-row-' + idx);
    if (!row) return;
    row.querySelectorAll('.ct-cell-input').forEach(function(el) {
        if (el.type === 'checkbox') el.checked = false; else el.value = '';
    });
}

/** 
 * Fetches price/description/UOM from backend and updates UI. 
 * FRAGILE: This function orchestrates the auto-population of line details.
 * 
 * DESIGN NOTE: When productId changes, we deliberately omit uom_id from the 
 * fetch URL. This signals the backend to resolve the product's DEFAULT UoM.
 * If uom_id is present in the URL, the backend honors it and resolves 
 * the price for that specific UoM instead.
 */
function _ctLoadPrice(idx, productId, qtyEl, priceEl, descEl, uomEl, prefix) {
    var meta = _ctGetMeta(idx);
    if (!meta.price_api || !productId) return;

    var qty  = qtyEl ? (parseFloat(qtyEl.value) || 1) : 1;
    var plEl = meta.price_list_field ? document.querySelector(meta.price_list_field) : null;
    var plId = plEl ? (plEl.value || null) : null;
    
    /**
     * Logic: Only send uom_id if it's explicitly currently set in the field.
     * On product change, we usually clear this field first, which results 
     * in the backend resolving the default.
     */
    var uomVal = uomEl ? (uomEl.tomselect ? uomEl.tomselect.getValue() : uomEl.value) : '';
    
    var url  = meta.price_api + '?product_id=' + productId + '&qty=' + qty +
               '&price_type=' + (meta.price_type || 'sales') +
               (meta.company_id ? '&company_id=' + meta.company_id : '') +
               (plId ? '&price_list_id=' + plId : '') +
               (uomVal ? '&uom_id=' + uomVal : '');
               
    fetch(url).then(function(r) { return r.json(); }).then(function(d) {
        if (!d.ok && d.ok !== undefined) return;
        
        /* Apply fetched values only if user hasn't manually edited the field since fetch began. */
        if (priceEl && !priceEl.dataset.manualEdit) priceEl.value = d.unit_price || '';
        if (descEl  && !descEl.dataset.manualEdit)  descEl.value  = d.description || '';
        
        /**
         * UOM RESOLUTION:
         * If the backend returned a UOM (common when productId was changed), 
         * we sync it back to the UI. If the option doesn't exist in the 
         * current select (e.g. dynamic conversion), we inject a virtual option.
         */
        if (uomEl && d.uom_id) {
            var newUom = String(d.uom_id);
            if (uomEl.tagName === 'SELECT' &&
                !uomEl.querySelector('option[value="' + newUom + '"]')) {
                var o = document.createElement('option');
                o.value = newUom;
                o.textContent = d.uom_label || newUom;
                uomEl.appendChild(o);
                if (uomEl.tomselect) {
                    uomEl.tomselect.addOption({value: newUom, text: d.uom_label || newUom});
                }
            }
            if (uomEl.tomselect) {
                uomEl.tomselect.setValue(newUom, true); // true = silent change
            } else {
                uomEl.value = newUom;
            }
        }

        var accEl = document.getElementById(prefix + 'account_id');
        if (accEl && d.account_id) accEl.value = d.account_id;
        
        _ctRecalcRow(idx, prefix);
    }).catch(function(err) { /* silent fail */ });
}

/** Recalculates subtotal for a single row based on price/qty/disc. */
function _ctRecalcRow(idx, prefix) {
    var qty   = parseFloat((document.getElementById(prefix + 'qty')          || {}).value) || 0;
    var price = parseFloat((document.getElementById(prefix + 'unit_price')   || {}).value) || 0;
    var disc  = parseFloat((document.getElementById(prefix + 'discount_pct') || {}).value) || 0;
    var subEl = document.getElementById(prefix + 'subtotal');
    if (subEl) subEl.value = (qty * price * (1 - disc / 100)).toFixed(4);
}

/** Binds UI inputs to trigger recalcs on input change. */
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

/** Recalculates footer total row values for columns in footer_totals. */
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

/** Resolves the display label for a field value (rel_maps lookup). */
function _ctResolveDisplay(idx, field, raw, tr) {
    var meta = _ctGetMeta(idx);

    /* In-cell edit input (per-line edit) is the freshest source of the chosen label. */
    if (tr) {
        var cell = tr.querySelector('td.ct-td-cell[data-field="' + field + '"]');
        var local = cell && cell.querySelector('.ct-cell-input');
        if (local) {
            if (local.type === 'checkbox') return local.checked ? '✓' : '';
            if (local.tagName === 'SELECT' && local.selectedIndex >= 0) {
                var t = local.options[local.selectedIndex].text;
                if (t && t !== '—') return t;
            }
        }
    }

    /* inline_columns[].options carries FK label list for per-line edit. */
    if (raw != null && raw !== '' && meta.inline_columns) {
        for (var i = 0; i < meta.inline_columns.length; i++) {
            var col = meta.inline_columns[i];
            if (col.name !== field) continue;
            if (col.type === 'checkbox') {
                var truthy = (raw === true || raw === 1 || raw === '1' || raw === 'true');
                return truthy ? '✓' : '';
            }
            if (col.options && col.options.length) {
                var rs = String(raw);
                for (var j = 0; j < col.options.length; j++) {
                    if (String(col.options[j].value) === rs) return col.options[j].label;
                }
            }
            break;
        }
    }

    if (meta.rel_maps && meta.rel_maps[field] && raw != null) {
        var label = meta.rel_maps[field][String(raw)];
        if (label != null) return label;
    }
    var sel = document.getElementById('ct-' + idx + '-' + field);
    if (sel && sel.tagName === 'SELECT' && sel.selectedIndex >= 0) {
        var txt = sel.options[sel.selectedIndex].text;
        if (txt && txt !== '—') return txt;
    }
    return raw;
}

/** Renders and appends a data row into the tbody. */
function _ctAppendRow(idx, obj, extraLabels) {
    var meta   = _ctGetMeta(idx);
    var tbody  = document.getElementById('ct-tbody-' + idx);
    var empty  = document.getElementById('ct-empty-' + idx);
    var seq    = tbody.querySelectorAll('.ct-data-row').length + 1;
    var tr     = document.createElement('tr');
    tr.id         = 'ct-row-' + idx + '-' + obj.id;
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

/** Removes a row from the UI and deletes via API. */
async function ctDeleteRow(idx, btn) {
    if (!await confirm('Delete this row?')) return;
    var tr = btn.closest('tr');
    var id = tr.dataset.id;
    var meta = _ctGetMeta(idx);

    if (id && String(id).startsWith('local_')) {
        var arr = _getCtLocalData(idx);
        arr = arr.filter(function(x) { return x.id !== id; });
        _setCtLocalData(idx, arr);
        tr.remove();
        _ctUpdateSeq(idx);
        if (window.Aras) Aras.toast('Removed local row', 'info');
        return;
    }

    var MN = meta.model_name || '';
    var _apiBase = meta.api_url || ('/api/erp/' + MN.replace(/_/g, '-') + '/');
    var url = _apiBase.replace(/\/$/, '') + '/' + id + '/';

    fetch(url, {
        method: 'DELETE',
        headers: {'X-CSRFToken': _ctGetCsrf()}
    }).then(function(r) {
        if (!r.ok) throw new Error('Delete failed');
        tr.remove();
        _ctUpdateSeq(idx);
        if (window.Aras) Aras.toast('Row deleted', 'success');
    }).catch(function(e) {
        if (window.Aras) Aras.toast('Delete error: ' + e.message, 'error');
    });
}

/** Generic persistence helper using HTMX/AJAX patterns for CRUD. */
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

/** Helper to retrieve the current CSRF token from DOM meta or cookie. */
function _ctGetCsrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.content;
    var m = document.cookie.match(/csrf_token=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
}

/** Filters pricing lists based on price type (e.g., sales vs. purchase). */
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

/** Modal variation for filtering price lists. */
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

/** Renumbers rows and refreshes 'Empty Table' state UI. */
function _ctUpdateSeq(idx) {
    var tbody = document.getElementById('ct-tbody-' + idx);
    if (!tbody) return;
    var rows = tbody.querySelectorAll('.ct-data-row');
    rows.forEach(function(tr, i) {
        var seq = tr.querySelector('.ct-td-seq');
        if (seq) seq.textContent = i + 1;
    });
    
    var empty = document.getElementById('ct-empty-' + idx);
    if (empty) {
        empty.style.display = rows.length > 0 ? 'none' : 'block';
        if (rows.length === 0) empty.classList.remove('d-none');
        else empty.classList.add('d-none');
    }
    
    _ctRecalcFooter(idx);
}
