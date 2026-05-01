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
        }
        sel.addEventListener('change', updateFieldOptions);
        updateFieldOptions();
    }
})();

function fillEditForm(colId, name, label, fieldType, order, required, showInList, showInForm, searchable, readonly, unique, length, default_value, placeholder, help_text, min_value, max_value, max_length, choices, relation_table_id, relation_system_table, relation_display_col, cascade_delete, defaultSection) {
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
