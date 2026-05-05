/* Aras Admin — Columns / Fields page JS */
(function () {
    var hash = window.location.hash;
    if (hash) {
        var tabEl = document.querySelector('.nav-tabs a[href="' + hash + '"]');
        if (tabEl) $(tabEl).tab('show');
    }
    $('.nav-tabs a').on('shown.bs.tab', function (e) {
        var newHash = e.target.hash;
        if (history.pushState) history.pushState(null, null, newHash);
        else window.location.hash = newHash;
    });

    var sel = document.getElementById('field_type_sel');
    if (sel) {
        function updateFieldOptions() {
            var v = sel.value;
            document.getElementById('relation-options').style.display = (v === 'relation') ? 'block' : 'none';
            document.getElementById('select-options').style.display   = (v === 'select')   ? 'block' : 'none';
            document.getElementById('length-option').style.display    = (v === 'string' || v === 'email' || v === 'phone') ? 'block' : 'none';
            if (v !== 'relation') _showDefaultInput();
        }
        sel.addEventListener('change', updateFieldOptions);
        updateFieldOptions();

        // Watch relation_table_id and relation_system_table for changes
        var relTblSel = document.querySelector('select[name="relation_table_id"]');
        var relSysTbl = document.querySelector('input[name="relation_system_table"]');
        var relDispCol = document.querySelector('input[name="relation_display_col"]');
        if (relTblSel) relTblSel.addEventListener('change', function() {
            // Auto-fill system_table and display_col from FK_TABLE_MAP
            var tid = parseInt(relTblSel.value);
            var map = window.FK_TABLE_MAP || {};
            if (tid && map[tid]) {
                if (relSysTbl && !relSysTbl.value) relSysTbl.value = map[tid].db_name || '';
                if (relDispCol && !relDispCol.value) relDispCol.value = map[tid].display_col || '';
            }
            _loadFkChoices();
        });
        if (relSysTbl) {
            relSysTbl.addEventListener('blur', function() { _loadFkChoices(); });
            relSysTbl.addEventListener('change', function() { _loadFkChoices(); });
        }
    }
    function _showDefaultInput() {
        var inp = document.getElementById('default_value_input');
        var fkSel = document.getElementById('default_value_fk_select');
        if (!inp || !fkSel) return;
        inp.style.display = '';
        fkSel.style.display = 'none';
        // Sync fk select value to input
        if (fkSel.value) inp.value = fkSel.value;
    }

    function _loadFkChoices(currentDefault) {
        var fkType = document.getElementById('field_type_sel');
        if (!fkType || fkType.value !== 'relation') return;
        var relTblSel = document.querySelector('select[name="relation_table_id"]');
        var relSysTbl = document.querySelector('input[name="relation_system_table"]');
        var relDispCol = document.querySelector('input[name="relation_display_col"]');
        var tableId = relTblSel ? parseInt(relTblSel.value) : 0;
        var sysTable = relSysTbl ? relSysTbl.value.trim() : '';
        var dispCol = relDispCol ? relDispCol.value.trim() : '';
        var inp = document.getElementById('default_value_input');
        var fkSel = document.getElementById('default_value_fk_select');
        if (!inp || !fkSel) return;

        if (!tableId && !sysTable) { _showDefaultInput(); return; }

        var url = '/admin/api/fk-choices/?';
        if (tableId) url += 'table_id=' + tableId;
        else url += 'system_table=' + encodeURIComponent(sysTable);
        if (dispCol) url += '&display_col=' + encodeURIComponent(dispCol);

        fetch(url).then(function(r) { return r.json(); }).then(function(d) {
            if (!d.ok || !d.rows) { _showDefaultInput(); return; }
            fkSel.innerHTML = '<option value="">-- no default --</option>';
            d.rows.forEach(function(row) {
                var opt = document.createElement('option');
                opt.value = row.id;
                opt.textContent = row.label + ' (' + row.id + ')';
                fkSel.appendChild(opt);
            });
            var cv = currentDefault !== undefined ? currentDefault : inp.value;
            if (cv) fkSel.value = String(cv);
            inp.style.display = 'none';
            fkSel.style.display = '';
            fkSel.onchange = function() { inp.value = fkSel.value; };
        }).catch(function() { _showDefaultInput(); });
    }
})();

function fillEditForm(colId, name, label, fieldType, order, required, showInList, showInForm, searchable, readonly, unique, length, default_value, placeholder, help_text, min_value, max_value, max_length, choices, relation_table_id, relation_system_table, relation_display_col, cascade_delete, defaultSection, relationFilter) {
    var form = document.getElementById('col-form');
    form.action = window.EDIT_URL.replace('__COL_ID__', colId);
    document.getElementById('col-edit-id').value = colId;

    form.elements['name'].value           = name;
    form.elements['label'].value          = label;
    form.elements['order'].value          = order;
    form.elements['length'].value         = length || '';
    form.elements['default_value'].value  = default_value || '';
    form.elements['placeholder'].value    = placeholder || '';
    form.elements['help_text'].value      = help_text || '';
    form.elements['min_value'].value      = min_value || '';
    form.elements['max_value'].value      = max_value || '';
    if (form.elements['max_length']) form.elements['max_length'].value = max_length || '';
    form.elements['choices'].value        = choices || '';

    var ftSel = document.getElementById('field_type_sel');
    if (ftSel) ftSel.value = fieldType;

    if (form.elements['relation_table_id']) form.elements['relation_table_id'].value = relation_table_id || 0;
    form.elements['relation_system_table'].value = relation_system_table || '';
    form.elements['relation_display_col'].value  = relation_display_col || '';
    if (form.elements['relation_filter']) form.elements['relation_filter'].value = relationFilter || '';

    function setToggle(name, val) {
        var inp = form.querySelector('input[name="' + name + '"]');
        if (inp) inp.checked = val;
    }
    setToggle('required', required);
    setToggle('show_in_list', showInList);
    setToggle('show_in_form', showInForm);
    setToggle('searchable', searchable);
    setToggle('readonly', readonly);
    setToggle('unique', unique);
    setToggle('cascade_delete', cascade_delete);
    var dsSel = document.getElementById('default_section_sel');
    if (dsSel) dsSel.value = defaultSection || 'content';

    document.getElementById('col-form-title').innerHTML =
        '<i class="fa fa-pencil icon--accent-mr-2"></i>Edit Point: <b>' + label + '</b>';
    document.getElementById('col-submit-btn').innerHTML = '<i class="fa fa-save mr-2"></i> Update Point';
    document.getElementById('col-submit-btn').className = 'aras-btn aras-btn--primary flex-grow-1';
    document.getElementById('col-cancel-btn').style.display = 'inline-block';

    if (ftSel) ftSel.dispatchEvent(new Event('change'));
    if (fieldType === 'relation') _loadFkChoices(default_value);
    document.getElementById('col-form').scrollIntoView({ behavior: 'smooth' });
}

function resetColForm() {
    var form = document.getElementById('col-form');
    form.action = window.ADD_URL;
    form.reset();
    document.getElementById('col-edit-id').value = '';
    document.getElementById('col-form-title').innerHTML =
        '<i class="fa fa-plus-circle icon--accent-mr-2"></i>Define Data Point';
    document.getElementById('col-submit-btn').innerHTML = '<i class="fa fa-save mr-2"></i> Register Point';
    document.getElementById('col-submit-btn').className = 'aras-btn aras-btn--primary flex-grow-1';
    document.getElementById('col-cancel-btn').style.display = 'none';
    var ftSel = document.getElementById('field_type_sel');
    if (ftSel) ftSel.dispatchEvent(new Event('change'));
}
