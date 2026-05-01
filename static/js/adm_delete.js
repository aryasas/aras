/**
 * adm_delete.js — Generic deletion dialog with linked-docs preview.
 * Refactored for better robustness against dynamic UI changes.
 * Loaded globally from base_index.html.
 */
(function () {
    "use strict";

    var _onConfirm   = null;

    function getEl(id) { return document.getElementById(id); }

    function init() {
        var modal = getEl("arasDeleteModal");
        if (!modal) return;

        // Use delegation for modal buttons to avoid issues with button cloning/replacement
        modal.addEventListener("click", function (e) {
            var target = e.target.closest("button");
            if (!target) return;

            if (target.id === "arasDeleteModalConfirm") {
                if (_onConfirm) {
                    var cb = _onConfirm;
                    _onConfirm = null; // reset
                    cb();
                }
            } else if (target.id === "arasDeleteModalCancel" || target.id === "arasDeleteModalClose") {
                hideModal();
            }
        });

        var overlay = getEl("arasDeleteModalOverlay");
        if (overlay) {
            overlay.addEventListener("click", hideModal);
        }

        wireDeleteButton();
    }

    function showModal() {
        var modal = getEl("arasDeleteModal");
        if (modal) {
            modal.style.display = "";
            // Reset UI states
            var progressWrap = getEl("arasDeleteProgressWrap");
            if (progressWrap) progressWrap.style.display = "none";
            var confirmBtn = getEl("arasDeleteModalConfirm");
            if (confirmBtn) confirmBtn.disabled = false;
            var cancelBtn = getEl("arasDeleteModalCancel");
            if (cancelBtn) cancelBtn.style.display = "";
            var bodyEl = getEl("arasDeleteModalBody");
            if (bodyEl) bodyEl.style.opacity = "1";
        }
    }

    function hideModal() {
        var modal = getEl("arasDeleteModal");
        if (modal) modal.style.display = "none";
    }

    function getCsrf() {
        var meta = document.querySelector("meta[name='csrf-token']");
        if (meta) return meta.getAttribute("content");
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
            // Per-doc delete button
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
        var btn = getEl("btnDeleteRecord");
        if (!btn) return;

        btn.addEventListener("click", function () {
            var deleteUrl     = btn.dataset.deleteUrl;
            var linkedDocsUrl = btn.dataset.linkedDocsUrl;

            if (!deleteUrl) return;

            function triggerSingleDelete() {
                var bodyEl = getEl("arasDeleteModalBody");
                if (bodyEl) {
                    bodyEl.innerHTML = "<p>Are you sure you want to delete this record?</p>";
                    _onConfirm = function () { submitDeleteAjax(deleteUrl); };
                    showModal();
                } else {
                    if (confirm("Delete this record?")) submitDeleteAjax(deleteUrl);
                }
            }

            if (!linkedDocsUrl) {
                triggerSingleDelete();
                return;
            }

            // Fetch linked docs
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
                var bodyEl = getEl("arasDeleteModalBody");
                if (bodyEl) {
                    bodyEl.innerHTML = renderTree(tree);
                    _onConfirm = function () { submitDeleteAjax(deleteUrl); };
                    wireLinkedDocButtons(bodyEl);
                    showModal();
                }
            })
            .catch(function () {
                btn.disabled  = false;
                btn.innerHTML = origHtml;
                triggerSingleDelete();
            });
        });
    }

    function wireLinkedDocButtons(container) {
        container.querySelectorAll(".js-linked-doc-delete").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                var url = btn.dataset.url;
                if (!url) return;
                if (!confirm("Delete this linked document individually?")) return;
                hideModal();
                submitDeleteAjax(url);
            });
        });
    }

    function submitDeleteAjax(deleteUrl, multiple) {
        var progressWrap = getEl("arasDeleteProgressWrap");
        var progressBar  = getEl("arasDeleteProgressBar");
        var progressText = getEl("arasDeleteProgressText");
        var confirmBtn   = getEl("arasDeleteModalConfirm");
        var cancelBtn    = getEl("arasDeleteModalCancel");
        var bodyEl       = getEl("arasDeleteModalBody");

        if (progressWrap) progressWrap.style.display = "block";
        if (confirmBtn) confirmBtn.disabled = true;
        if (cancelBtn) cancelBtn.style.display = "none";
        if (bodyEl && !multiple) bodyEl.style.opacity = "0.5";

        var urls = Array.isArray(deleteUrl) ? deleteUrl : [deleteUrl];
        var total = urls.length;
        var completed = 0;
        var lastRedirect = null;

        function updateProgress(done) {
            if (!progressBar || !progressText) return;
            var pct = Math.round((done / total) * 100);
            progressBar.style.width = pct + "%";
            var actionText = total > 1 ? "Moving to Trash: " : "Processing: ";
            progressText.textContent = actionText + done + " / " + total;
        }

        updateProgress(0);

        function next() {
            if (completed >= total) {
                if (lastRedirect) {
                    window.location.href = lastRedirect;
                } else {
                    window.location.reload();
                }
                return;
            }

            var url = urls[completed];
            fetch(url, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrf(),
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: "csrf_token=" + encodeURIComponent(getCsrf())
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success || data.deleted) {
                    if (data.redirect) lastRedirect = data.redirect;
                    completed++;
                    updateProgress(completed);
                    setTimeout(next, total > 1 ? 50 : 200);
                } else {
                    alert("Error: " + (data.message || "Failed to delete record."));
                    window.location.reload();
                }
            })
            .catch(function (err) {
                console.error("Delete failed", err);
                alert("Network error or server failure.");
                window.location.reload();
            });
        }

        next();
    }

    // Set globally for list_view.js and others to use
    window._arasSubmitDeleteAjax = submitDeleteAjax;

    window._arasSetDeleteConfirm = function (cb) {
        _onConfirm = cb;
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
