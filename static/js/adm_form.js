/* Aras Admin Form — Core JS */
(function () {
    function formatRelativeTime(iso) {
        if (!iso) return "";
        var d = new Date(iso), diff = Math.round((Date.now() - d) / 1000);
        if (diff < 30) return "Just now";
        if (diff < 60) return diff + "s ago";
        if (diff < 3600) return Math.round(diff / 60) + "m ago";
        if (diff < 86400) return Math.round(diff / 3600) + "h ago";
        if (diff < 172800) return "Yesterday";
        return Math.round(diff / 86400) + "d ago";
    }

    document.querySelectorAll(".aras-timeline-time[data-ts]").forEach(function (el) {
        var t = el.dataset.ts;
        if (t) {
            var rel = formatRelativeTime(t);
            if (rel.indexOf("d ago") === -1 && rel !== "Yesterday") el.textContent = rel;
        }
    });

    var mainForm = document.getElementById("mainForm");
    if (mainForm) {
        var isDirty = false;
        mainForm.addEventListener("change", function () { isDirty = true; });
        window.addEventListener("beforeunload", function (e) {
            if (isDirty) { var msg = "You have unsaved changes."; e.returnValue = msg; return msg; }
        });
        mainForm.addEventListener("submit", function () { isDirty = false; });
    }

    /* Aras Document Totals (Header recalc) */
    function formatNumber(val) {
        var cfg = (window.ArasConfig && window.ArasConfig.numberFormat) || { thousandsSep: ',', decimalSep: '.', precision: 2 };
        var n = parseFloat(val);
        if (isNaN(n)) return val;
        var s = n.toFixed(cfg.precision);
        var parts = s.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, cfg.thousandsSep);
        return parts.join(cfg.decimalSep);
    }

    function parseNumber(val) {
        var cfg = (window.ArasConfig && window.ArasConfig.numberFormat) || { thousandsSep: ',', decimalSep: '.', precision: 2 };
        if (!val) return 0;
        var s = String(val);
        if (cfg.thousandsSep) {
            s = s.replace(new RegExp('\\' + cfg.thousandsSep, 'g'), '');
        }
        s = s.replace(cfg.decimalSep, '.');
        return parseFloat(s) || 0;
    }

    function recalcHeaderTotal() {
        var sub    = parseNumber(document.getElementById('subtotal')?.value);
        var charge = parseNumber(document.getElementById('charge_amt')?.value);
        var disc   = parseNumber(document.getElementById('discount_amt')?.value);
        var totalEl = document.getElementById('total');
        if (totalEl) {
            totalEl.value = formatNumber(sub + charge - disc);
        }
    }
    ['subtotal', 'charge_amt', 'discount_amt'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) {
            el.addEventListener('input',  recalcHeaderTotal);
            el.addEventListener('change', recalcHeaderTotal);
        }
    });

    /* Global Numeric Formatting */
    function initNumericFields() {
        document.querySelectorAll(".aras-numeric-input").forEach(function (el) {
            if (el.dataset.numericInited) return;
            el.dataset.numericInited = "1";

            el.addEventListener("focus", function () {
                if (this.readOnly) return;
                var val = parseNumber(this.value);
                if (val === 0 && this.value === "") return;
                this.value = val; // raw number for editing
                this.select();
            });

            el.addEventListener("blur", function () {
                if (this.readOnly) return;
                this.value = formatNumber(this.value);
            });
            
            // Initial formatting if value is present and not formatted
            if (this.value && !this.value.includes((window.ArasConfig?.numberFormat?.thousandsSep || ","))) {
                this.value = formatNumber(this.value);
            }
        });
    }
    initNumericFields();
    // Re-init on HTMX load if needed
    document.addEventListener("htmx:afterSwap", initNumericFields);
})();

/* Legacy Inline Child Table Actions */
function legacyCtGetMeta(ctId) {
    try { return JSON.parse(document.getElementById("ct-meta-" + ctId).textContent); }
    catch (e) { return { vcols: [], rel_maps: {} }; }
}

function legacyCtUpdateCount(ctId) {
    var tbody = document.getElementById("ct-tbody-" + ctId);
    var count = tbody ? tbody.querySelectorAll("tr.ct-row").length : 0;
    var empty = document.getElementById("ct-empty-" + ctId);
    if (empty) empty.style.display = count === 0 ? "" : "none";
}

function legacyCtAddRow(ctId) {
    document.getElementById("ct-editing-id-" + ctId).value = "";
    var form = document.getElementById("ct-form-" + ctId);
    form.querySelectorAll(".ct-input").forEach(function (el) {
        if (el.type === "checkbox") el.checked = false; else el.value = "";
    });
    form.style.display = "block";
    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

function legacyCtEditRow(ctId, btn) {
    var row = btn.closest("tr"), rowId = row.dataset.id;
    document.getElementById("ct-editing-id-" + ctId).value = rowId;
    var meta = legacyCtGetMeta(ctId);
    var cells = row.querySelectorAll("td:not(.ct-actions)");
    meta.vcols.forEach(function (fname, i) {
        var inp = document.getElementById("ct-" + ctId + "-" + fname);
        if (!inp) return;
        var raw = cells[i] ? (cells[i].dataset.raw !== undefined ? cells[i].dataset.raw : cells[i].textContent.trim()) : "";
        if (raw === "—") raw = "";
        if (inp.type === "checkbox") inp.checked = raw === "True" || raw === "true" || raw === "1";
        else inp.value = raw;
    });
    var form = document.getElementById("ct-form-" + ctId);
    form.style.display = "block";
    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

function legacyCtCancelRow(ctId) {
    document.getElementById("ct-form-" + ctId).style.display = "none";
    document.getElementById("ct-editing-id-" + ctId).value = "";
}

function legacyCtGetCsrf() {
    var m = document.cookie.match(/csrf_token=([^;]+)/);
    if (m) return decodeURIComponent(m[1]);
    var tag = document.querySelector('input[name="csrf_token"]');
    return tag ? tag.value : "";
}

function legacyCtSaveRow(ctId, apiUrl, fkCol, parentId) {
    var editingId = document.getElementById("ct-editing-id-" + ctId).value;
    var form = document.getElementById("ct-form-" + ctId);
    var data = {}; data[fkCol] = parentId;
    form.querySelectorAll(".ct-input").forEach(function (el) {
        var name = el.name; if (!name) return;
        if (el.type === "checkbox") { data[name] = el.checked; return; }
        if (el.value === "") return;
        // FK select sentinel "0" → omit (server treats missing as NULL)
        if (el.tagName === "SELECT" && /_id$/.test(name) && el.value === "0") return;
        data[name] = el.value;
    });
    var method = editingId ? "PUT" : "POST";
    var url = editingId ? apiUrl.replace(/\/$/, "") + "/" + editingId + "/" : apiUrl;
    var saveBtn = form.querySelector(".aras-btn--primary");
    var oldHtml = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Saving...';
    fetch(url, { method: method, headers: { "Content-Type": "application/json", "X-CSRFToken": legacyCtGetCsrf() }, body: JSON.stringify(data) })
        .then(function (r) {
            saveBtn.disabled = false; saveBtn.innerHTML = oldHtml;
            if (!r.ok) return r.json().then(function (e) { arasNotify("Error: " + (e.error || r.status), "error"); });
            return r.json().then(function (obj) { legacyCtRenderRow(ctId, obj, editingId); legacyCtCancelRow(ctId); legacyCtUpdateCount(ctId); });
        })
        .catch(function (e) { saveBtn.disabled = false; saveBtn.innerHTML = oldHtml; arasNotify("Network error: " + e, "error"); });
}

function legacyCtRenderRow(ctId, obj, editingId) {
    var meta = legacyCtGetMeta(ctId);
    var tbody = document.getElementById("ct-tbody-" + ctId);
    var cells = meta.vcols.map(function (fname) {
        var raw = obj[fname]; if (raw === null || raw === undefined) raw = "";
        var rel = meta.rel_maps[fname], display = rel ? rel[String(raw)] || raw : raw;
        return '<td data-raw="' + String(raw).replace(/"/g, "&quot;") + '">' + String(display === "" ? "—" : display) + "</td>";
    });
    var actCell = '<td class="ct-td-actions"><button type="button" class="ct-btn-edit" title="Edit" onclick="legacyCtEditRow(' + ctId + ', this)"><i class="fa fa-pencil"></i></button><button type="button" class="ct-btn-del" title="Delete" onclick="legacyCtDeleteRow(' + ctId + ', this)"><i class="fa fa-trash"></i></button></td>';
    var rowHtml = '<tr data-id="' + obj.id + '" class="ct-row">' + cells.join("") + actCell + "</tr>";
    if (editingId) {
        var existing = tbody.querySelector('tr[data-id="' + editingId + '"]');
        if (existing) { existing.outerHTML = rowHtml; return; }
    }
    tbody.insertAdjacentHTML("beforeend", rowHtml);
}

async function legacyCtDeleteRow(ctId, btn) {
    if (!await confirm("Delete this row?")) return;
    var row = btn.closest("tr"), rowId = row.dataset.id;
    var form = document.getElementById("ct-form-" + ctId);
    var apiUrl = form ? form.dataset.apiUrl : null;
    if (!apiUrl) { arasNotify("Cannot determine API URL", "error"); return; }
    fetch(apiUrl.replace(/\/$/, "") + "/" + rowId + "/", { method: "DELETE", headers: { "X-CSRFToken": legacyCtGetCsrf() } })
        .then(function (r) {
            if (!r.ok) return r.json().then(function (e) { arasNotify("Error: " + (e.error || r.status), "error"); });
            row.remove(); legacyCtUpdateCount(ctId);
        })
        .catch(function (e) { arasNotify("Network error: " + e, "error"); });
}
