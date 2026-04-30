/**
 * adm_delete.js — Generic deletion dialog with linked-docs preview.
 * Loaded globally from base_index.html.
 */
(function () {
    "use strict";

    var modal        = null;
    var overlay      = null;
    var bodyEl       = null;
    var confirmBtn   = null;
    var cancelBtn    = null;
    var closeBtn     = null;
    var _onConfirm   = null;

    function init() {
        modal      = document.getElementById("arasDeleteModal");
        if (!modal) return;
        overlay    = document.getElementById("arasDeleteModalOverlay");
        bodyEl     = document.getElementById("arasDeleteModalBody");
        confirmBtn = document.getElementById("arasDeleteModalConfirm");
        cancelBtn  = document.getElementById("arasDeleteModalCancel");
        closeBtn   = document.getElementById("arasDeleteModalClose");

        cancelBtn.addEventListener("click", hideModal);
        closeBtn.addEventListener("click",  hideModal);
        if (overlay) overlay.addEventListener("click", hideModal);
        confirmBtn.addEventListener("click", function () {
            hideModal();
            if (_onConfirm) _onConfirm();
        });

        wireDeleteButton();
    }

    function showModal() { if (modal) modal.style.display = ""; }
    function hideModal() { if (modal) modal.style.display = "none"; }

    function getCsrf() {
        var el = document.querySelector("input[name='csrf_token']");
        return el ? el.value : "";
    }

    function renderTree(tree) {
        if (!tree || !tree.length) {
            return "<p>Are you sure you want to delete this record?<br>"
                 + "<small class='text-muted'>This action will be saved to Trash and can be restored.</small></p>";
        }
        var html = "<p class='text-danger mb-2'><strong>"
                 + tree.length + " linked record(s) will also be deleted:</strong></p>"
                 + "<ul style='list-style:none;padding:0;margin:0 0 12px;'>";
        tree.forEach(function (node) {
            var indent = node.depth > 1 ? "margin-left:" + ((node.depth - 1) * 16) + "px;" : "";
            var label  = node.display ? node.doc_type + " — " + node.display
                                      : node.doc_type + " #" + node.doc_id;
            html += "<li style='padding:4px 0 4px;" + indent + "display:flex;align-items:center;gap:8px;'>";
            html += "<span style='flex:1;'><i class='fa fa-file-o mr-1 text-muted'></i>";
            if (node.admin_url) {
                html += "<a href='" + node.admin_url + "' target='_blank'>" + label + "</a>";
            } else {
                html += label;
            }
            html += "</span>";
            // Per-doc delete button (goes to admin_url + delete)
            if (node.admin_url) {
                var docDeleteUrl = node.admin_url.replace(/\/$/, "") + "/delete/";
                html += "<button class='aras-btn aras-btn--sm text-danger aras-btn--outline js-linked-doc-delete' "
                      + "data-url='" + docDeleteUrl + "' style='padding:2px 6px;font-size:11px;' "
                      + "title='Delete this document individually'>"
                      + "<i class='fa fa-times'></i></button>";
            }
            html += "</li>";
        });
        html += "</ul>"
              + "<small class='text-muted'>All records will be backed up to Trash and can be restored.</small>";
        return html;
    }

    function wireDeleteButton() {
        var btn = document.getElementById("btnDeleteRecord");
        if (!btn) return;

        btn.addEventListener("click", function () {
            var deleteUrl     = btn.dataset.deleteUrl;
            var linkedDocsUrl = btn.dataset.linkedDocsUrl;

            if (!deleteUrl) return;

            if (!linkedDocsUrl) {
                // No API URL — simple confirm
                if (!confirm("Delete this record?")) return;
                submitDeletePost(deleteUrl);
                return;
            }

            // Fetch linked docs first
            btn.disabled = true;
            var origHtml = btn.innerHTML;
            btn.innerHTML = "<i class='fa fa-spinner fa-spin'></i>";

            fetch(linkedDocsUrl, {
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCsrf() }
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                btn.disabled  = false;
                btn.innerHTML = origHtml;
                var tree = data.tree || [];
                if (!tree.length) {
                    // No linked docs — simple confirm
                    if (!confirm("Delete this record? This will be saved to Trash.")) return;
                    submitDeletePost(deleteUrl);
                    return;
                }
                // Show modal
                bodyEl.innerHTML = renderTree(tree);
                _onConfirm = function () { submitDeletePost(deleteUrl); };
                wireLinkedDocButtons();
                showModal();
            })
            .catch(function () {
                btn.disabled  = false;
                btn.innerHTML = origHtml;
                if (confirm("Delete this record?")) submitDeletePost(deleteUrl);
            });
        });
    }

    function wireLinkedDocButtons() {
        if (!bodyEl) return;
        bodyEl.querySelectorAll(".js-linked-doc-delete").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                var url = btn.dataset.url;
                if (!url) return;
                if (!confirm("Delete this linked document individually?")) return;
                hideModal();
                submitDeletePost(url);
            });
        });
    }

    function submitDeletePost(deleteUrl) {
        var form = document.createElement("form");
        form.method = "POST";
        form.action = deleteUrl;
        var csrf = document.createElement("input");
        csrf.type  = "hidden";
        csrf.name  = "csrf_token";
        csrf.value = getCsrf();
        form.appendChild(csrf);
        document.body.appendChild(form);
        form.submit();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
