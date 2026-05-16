Plan: Child Table Local Storage & Saving in "Add" View
Objective
Enable child tables (like acc_sales_invoice_line) to temporarily store data in the browser when creating a new parent record (in the "Add" view), and then correctly save those rows to the database when the main parent form is submitted.
Scope & Impact
Frontend JS (static/js/child_table.js): Implement a "local mode" for child table row operations (ctSaveInlineRow, ctOpenModal, ctSaveModal, ctDeleteRow). When the parent ID is missing, rows will be assigned a temporary local_ ID and stored as a JSON string in a hidden input (ct_local_{model_name}) appended to the main form.
Backend Python (arasCore/admin/crud_factory.py): Update the make_add method to generically parse the ct_local_{model_name} hidden inputs upon successful submission of the main form. It will insert the new child records into the database with the newly generated parent ID.
Proposed Solution
1. Frontend Updates (child_table.js)
Add helper functions _getCtLocalData(idx) and _setCtLocalData(idx, arr) to manage local rows in a hidden <input name="ct_local_{idx}">.
Modify ctSaveInlineRow: If parentId is empty, generate a local_{timestamp} ID, push the row data to local storage, and call _ctAppendRow instead of hitting the API.
Modify ctOpenModal: If id starts with local_, fetch the row data from local storage to populate the edit modal.
Modify ctSaveModal: If id starts with local_, update the local storage array and refresh the row's DOM elements without hitting the API.
Modify ctDeleteRow: If id starts with local_, remove the row from local storage and the DOM.
2. Backend Updates (crud_factory.py)
In make_add, right after db.session.flush() (when obj.id is available but before db.session.commit()), iterate over all child tables defined for the model using _get_child_tables_for_model(model).
For each child table, check request.form.get(f"ct_local_{child_table_name}").
If JSON data exists, parse it, instantiate the child model objects, set the foreign key (fk_col) to obj.id, populate the fields, and add them to db.session.
Alternatives Considered
Hiding Child Tables in "Add" View: The simpler Aras-standard approach would be to disable child tables until the parent is saved (Edit view). However, since POS creates them together and the user prefers inline adding, local temporary storage provides a better user experience.
Using a Server Script Hook: Relying on an after_insert hook in invoice.py would only fix it for Sales Invoices. The generic crud_factory.py approach fixes local storage for all child tables across the entire framework.
Implementation Steps
Execute string replacements in static/js/child_table.js to integrate the local storage functions and update the row manipulation methods.
Execute string replacements in arasCore/admin/crud_factory.py within make_add to parse and insert the local child table data.
Test creating a new Sales Invoice with child rows to ensure data persists correctly to the database.
