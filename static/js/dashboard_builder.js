/**
 * Aras Dashboard Builder Logic
 */
(function() {
    'use strict';

    const DB = {
        isEditing: false,
        grid: document.getElementById('dashboard-grid'),
        editActions: document.getElementById('edit-actions'),
        btnEdit: document.getElementById('btn-edit-dashboard'),
        btnSave: document.getElementById('btn-save-dashboard'),
        btnCancel: document.getElementById('btn-cancel-dashboard'),
        btnAdd: document.getElementById('btn-add-widget'),
        
        init() {
            if (!this.btnEdit) return;

            this.btnEdit.addEventListener('click', () => this.toggleEdit(true));
            this.btnCancel.addEventListener('click', () => this.toggleEdit(false));
            this.btnSave.addEventListener('click', () => this.saveLayout());
            this.btnAdd.addEventListener('click', () => $('#addWidgetModal').modal('show'));

            // Widget Events (Delegated)
            this.grid.addEventListener('click', (e) => {
                if (!this.isEditing) return;

                const btnDelete = e.target.closest('.btn-widget-delete');
                if (btnDelete) {
                    this.deleteWidget(btnDelete.closest('.dashboard-widget-container'));
                    return;
                }

                const btnLeft = e.target.closest('.btn-widget-move-left');
                if (btnLeft) {
                    this.moveWidget(btnLeft.closest('.dashboard-widget-container'), -1);
                    return;
                }

                const btnRight = e.target.closest('.btn-widget-move-right');
                if (btnRight) {
                    this.moveWidget(btnRight.closest('.dashboard-widget-container'), 1);
                    return;
                }
            });

            // Add Widget Modal Logic
            document.getElementById('w-type').addEventListener('change', (e) => {
                document.getElementById('group-sum-col').style.display = 
                    (e.target.value === 'sum' || e.target.value === 'chart') ? 'block' : 'none';
            });

            document.getElementById('btn-confirm-add-widget').addEventListener('click', () => this.addNewWidget());
        },

        toggleEdit(active) {
            this.isEditing = active;
            document.body.classList.toggle('editing', active);
            this.btnEdit.classList.toggle('d-none', active);
            this.editActions.classList.toggle('d-none', !active);
            
            document.querySelectorAll('.widget-edit-overlay').forEach(el => {
                el.classList.toggle('d-none', !active);
            });
        },

        moveWidget(container, direction) {
            if (direction === -1) {
                const prev = container.previousElementSibling;
                if (prev) this.grid.insertBefore(container, prev);
            } else {
                const next = container.nextElementSibling;
                if (next) this.grid.insertBefore(next, container);
            }
        },

        deleteWidget(container) {
            if (!confirm('Are you sure you want to remove this widget?')) return;
            const dbId = container.dataset.dbId;
            
            if (!dbId) {
                // System widget - just hide for now or ignore
                container.remove();
                return;
            }

            fetch(`/admin/dashboard/builder/delete-widget/${dbId}`, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.getCsrf() }
            }).then(r => r.json()).then(res => {
                if (res.success) container.remove();
                else alert('Error: ' + res.error);
            });
        },

        addNewWidget() {
            const data = {
                label: document.getElementById('w-label').value,
                widget_type: document.getElementById('w-type').value,
                data_source: document.getElementById('w-source').value,
                config_json: JSON.stringify({
                    sum_col: document.getElementById('w-sum-col').value,
                    agg_col: document.getElementById('w-sum-col').value
                })
            };

            fetch('/admin/dashboard/builder/add-widget', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrf() 
                },
                body: JSON.stringify(data)
            }).then(r => r.json()).then(res => {
                if (res.success) window.location.reload();
                else alert('Error: ' + res.error);
            });
        },

        saveLayout() {
            const layout = [];
            document.querySelectorAll('.dashboard-widget-container').forEach((el, index) => {
                const dbId = el.dataset.dbId;
                if (dbId) {
                    layout.push({ db_id: parseInt(dbId), order: index });
                }
            });

            fetch('/admin/dashboard/builder/save-layout', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrf() 
                },
                body: JSON.stringify({ layout })
            }).then(r => r.json()).then(res => {
                if (res.success) {
                    this.toggleEdit(false);
                    window.location.reload();
                } else {
                    alert('Error: ' + res.error);
                }
            });
        },

        getCsrf() {
            return document.querySelector('input[name="csrf_token"]')?.value || '';
        }
    };

    document.addEventListener('DOMContentLoaded', () => DB.init());
})();
