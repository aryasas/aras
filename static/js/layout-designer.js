const { useState, useEffect, useCallback, useRef } = React;

const getCsrf = () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

function LayoutDesigner() {
    const [table, setTable] = useState(null);
    const [columns, setColumns] = useState([]);
    const [layout, setLayout] = useState([]);
    const [activeTabIdx, setActiveTabIdx] = useState(0);
    const [loading, setLoading] = useState(true);
    const [dragOverSection, setDragOverSection] = useState(null);
    const [dragOverItem, setDragOverItem] = useState(null);
    const [draggedItem, setDraggedItem] = useState(null);
    const [draggedSection, setDraggedSection] = useState(null);
    const [dragOverSectionIdx, setDragOverSectionIdx] = useState(null);
    const [showPreview, setShowPreview] = useState(true);
    const [jsonError, setJsonError] = useState(null);

    const refreshData = useCallback(() => {
        const tableId = window.FORM_BUILDER_TABLE_ID;
        const childTables = window.FORM_BUILDER_CHILD_TABLES || [];
        setLoading(true);
        Promise.all([
            fetch(`/api/admin/apps/tables/${tableId}/`).then(r => r.json()),
            fetch(`/api/admin/apps/tables/columns/?filter[table_id]=${tableId}&per_page=200`).then(r => r.json())
        ]).then(([tableData, colsData]) => {
            const systemFields = ['id', 'created_at', 'updated_at', 'deleted_at', 'created_by_id', 'updated_by_id', 'is_active'];
            let colMap = new Map();
            (colsData.data || []).forEach(c => {
                if (!systemFields.includes(c.name.toLowerCase())) colMap.set(c.name, c);
            });
            childTables.forEach(ct => {
                colMap.set(ct.name, { ...ct, id: ct.name, type: 'child_table' });
            });
            setColumns(Array.from(colMap.values()));

            if (tableData.id) {
                setTable(tableData);
                let initialLayout = [];
                try {
                    initialLayout = typeof tableData.layout_json === 'string' ? JSON.parse(tableData.layout_json) : (tableData.layout_json || []);
                } catch(e) { console.error("Layout parse error", e); }

                // Bootstrap default if empty
                if (!Array.isArray(initialLayout) || initialLayout.length === 0) {
                    const fields = Array.from(colMap.values()).filter(c => c.type !== 'child_table');
                    initialLayout = [{
                        label: tableData.title || 'General',
                        sections: [{
                            label: 'Details',
                            width: 12,
                            fields: fields.slice(0, 10).map(c => ({ name: c.name, width: 6, type: 'field' }))
                        }]
                    }];
                }
                setLayout(initialLayout);
            }
            setLoading(false);
        }).catch(err => { console.error(err); setLoading(false); });
    }, []);

    useEffect(() => { refreshData(); }, [refreshData]);

    const getCol = (name) => columns.find(c => c.name === name) || { label: name, name, type: 'field' };
    const isFieldUsed = (name) => layout.some(t => t.sections?.some(s => s.fields?.some(f => f.name === name)));

    // Actions
    const addTab = () => setLayout([...layout, { label: 'New Tab', sections: [{ label: 'Section 1', width: 12, fields: [] }] }]);
    const deleteTab = (idx) => { if(layout.length > 1 && confirm('Delete tab?')) setLayout(layout.filter((_, i) => i !== idx)); };
    const addSection = (tIdx) => {
        const nl = [...layout];
        nl[tIdx].sections.push({ label: 'New Section', width: 12, fields: [] });
        setLayout(nl);
    };
    const deleteSection = (tIdx, sIdx) => {
        const nl = [...layout];
        nl[tIdx].sections.splice(sIdx, 1);
        setLayout(nl);
    };

    // Drag & Drop Logic
    const onDragStartNew = (e, field) => setDraggedItem({ type: 'new', field });
    const onDragStartExisting = (e, fieldName, tIdx, sIdx, fIdx) => setDraggedItem({ type: 'existing', fieldName, tIdx, sIdx, fIdx });
    
    const onDrop = (e, tIdx, sIdx) => {
        e.preventDefault();
        if (!draggedItem) return;
        const nl = JSON.parse(JSON.stringify(layout));
        let item;
        if (draggedItem.type === 'new') {
            item = { name: draggedItem.field.name, width: 12, type: draggedItem.field.type || 'field' };
        } else {
            item = nl[draggedItem.tIdx].sections[draggedItem.sIdx].fields.splice(draggedItem.fIdx, 1)[0];
        }
        
        const targetFields = nl[tIdx].sections[sIdx].fields;
        if (dragOverItem && dragOverItem.sIdx === sIdx) {
            targetFields.splice(dragOverItem.pos === 'bottom' ? dragOverItem.fIdx + 1 : dragOverItem.fIdx, 0, item);
        } else {
            targetFields.push(item);
        }
        setLayout(nl);
        setDraggedItem(null);
        setDragOverItem(null);
    };

    const saveLayout = async (layoutToSave = layout) => {
        try {
            const res = await fetch(`/admin/apps/${window.FORM_BUILDER_APP_ID}/tables/${window.FORM_BUILDER_TABLE_ID}/layout`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify({ layout: layoutToSave })
            });
            const data = await res.json();
            if (data.ok) {
                Swal.fire({ icon: 'success', title: 'Saved', toast: true, position: 'top-end', timer: 2000, showConfirmButton: false });
            }
        } catch (err) { Swal.fire({ icon: 'error', title: 'Error', text: err.message }); }
    };

    const handleJsonChange = (e) => {
        const val = e.target.value;
        try {
            const parsed = JSON.parse(val);
            setLayout(parsed);
            setJsonError(null);
        } catch(e) { setJsonError(e.message); }
    };

    if (loading) return null;

    return (
        <div id="aras-layout-designer-root">
            <div className="designer-toolbar">
                <div className="d-flex align-items-center gap-3">
                    <h5 className="mb-0 fw-bold">{table?.title} <span className="text-muted fw-normal fs-14">Layout Designer</span></h5>
                </div>
                <div className="d-flex gap-2">
                    <button className="btn btn-sm btn-outline-secondary" onClick={() => setShowPreview(!showPreview)}>
                        <i className={`fa ${showPreview ? 'fa-eye-slash' : 'fa-eye'} me-1`}></i> {showPreview ? 'Hide Preview' : 'Show Preview'}
                    </button>
                    <button className="btn btn-sm btn-primary px-3" onClick={() => saveLayout()}>
                        <i className="fa fa-save me-1"></i> Save Layout
                    </button>
                </div>
            </div>

            <div className="designer-main">
                {/* 1. Sidebar Toolset */}
                <aside className="designer-sidebar p-3">
                    <h6 className="text-uppercase fs-11 fw-bold text-muted mb-3">Available Fields</h6>
                    <div className="d-flex flex-column gap-1">
                        {columns.map(col => (
                            <div key={col.id} 
                                className={`field-draggable ${isFieldUsed(col.name) ? 'is-used' : ''} ${col.type === 'child_table' ? 'is-component' : ''}`}
                                draggable={!isFieldUsed(col.name)}
                                onDragStart={(e) => onDragStartNew(e, col)}
                            >
                                <i className={`fa ${col.type === 'child_table' ? 'fa-table' : 'fa-grip-vertical'} opacity-50`}></i>
                                <span>{col.label}</span>
                            </div>
                        ))}
                    </div>
                </aside>

                {/* 2. Designer Canvas */}
                <main className="designer-canvas">
                    <div className="mock-form-card">
                        <div className="mock-tab-strip">
                            {layout.map((tab, idx) => (
                                <div key={idx} className={`mock-tab-item ${activeTabIdx === idx ? 'active' : ''}`} onClick={() => setActiveTabIdx(idx)}>
                                    {tab.label}
                                </div>
                            ))}
                            <button className="btn btn-link btn-xs text-muted" onClick={addTab}>+ Add Tab</button>
                        </div>
                        
                        {layout[activeTabIdx] && (
                            <div className="p-4">
                                <div className="mb-4 d-flex justify-content-between">
                                    <input className="form-control form-control-sm border-0 bg-light fw-bold" style={{width:'200px'}} 
                                        value={layout[activeTabIdx].label} onChange={(e) => {
                                            const nl = [...layout]; nl[activeTabIdx].label = e.target.value; setLayout(nl);
                                        }} />
                                    <button className="btn btn-xs btn-outline-danger border-0" onClick={() => deleteTab(activeTabIdx)}>Delete Tab</button>
                                </div>

                                <div className="row g-4">
                                    {layout[activeTabIdx].sections.map((sec, sIdx) => (
                                        <div key={sIdx} className={`col-md-${sec.width || 12}`}>
                                            <div className="mock-section border rounded p-3 bg-white shadow-sm"
                                                onDragOver={(e) => { e.preventDefault(); setDragOverSection(sIdx); }}
                                                onDrop={(e) => onDrop(e, activeTabIdx, sIdx)}
                                            >
                                                <div className="d-flex justify-content-between mb-3 align-items-center">
                                                    <input className="border-0 fw-bold fs-12 text-uppercase text-muted" style={{outline:'none'}}
                                                        value={sec.label} onChange={(e) => {
                                                            const nl = [...layout]; nl[activeTabIdx].sections[sIdx].label = e.target.value; setLayout(nl);
                                                        }} />
                                                    <div className="d-flex gap-2">
                                                        <select className="form-select form-select-xs py-0" style={{fontSize:'10px', width:'70px'}} 
                                                            value={sec.width} onChange={(e) => {
                                                                const nl = [...layout]; nl[activeTabIdx].sections[sIdx].width = parseInt(e.target.value); setLayout(nl);
                                                            }}>
                                                            <option value="12">Full</option>
                                                            <option value="6">Half</option>
                                                        </select>
                                                        <i className="fa fa-times text-danger fs-12 cursor-pointer opacity-50" onClick={() => deleteSection(activeTabIdx, sIdx)}></i>
                                                    </div>
                                                </div>

                                                <div className="row g-2" style={{minHeight:'40px'}}>
                                                    {sec.fields.map((f, fIdx) => {
                                                        const col = getCol(f.name);
                                                        return (
                                                            <div key={fIdx} className={`col-md-${f.width || 12}`}>
                                                                <div className="mock-field-row border rounded px-2 py-1 fs-12 d-flex align-items-center gap-2 bg-light"
                                                                    draggable onDragStart={(e) => onDragStartExisting(e, f.name, activeTabIdx, sIdx, fIdx)}
                                                                    onDragOver={(e) => {
                                                                        e.preventDefault();
                                                                        const rect = e.currentTarget.getBoundingClientRect();
                                                                        const pos = (e.clientY - rect.top) < rect.height/2 ? 'top' : 'bottom';
                                                                        setDragOverItem({ sIdx, fIdx, pos });
                                                                    }}
                                                                >
                                                                    <i className="fa fa-grip-vertical opacity-25"></i>
                                                                    <span className="flex-grow-1">{col.label}</span>
                                                                    <div className="field-meta d-flex gap-1">
                                                                        <button className="btn btn-xs p-0 px-1 border" onClick={() => {
                                                                            const nl = [...layout]; 
                                                                            nl[activeTabIdx].sections[sIdx].fields[fIdx].width = f.width === 6 ? 12 : 6;
                                                                            setLayout(nl);
                                                                        }}>{f.width === 6 ? '1/2' : '1/1'}</button>
                                                                        <button className="btn btn-xs p-0 px-1 border text-danger" onClick={() => {
                                                                            const nl = [...layout]; nl[activeTabIdx].sections[sIdx].fields.splice(fIdx, 1); setLayout(nl);
                                                                        }}><i className="fa fa-times"></i></button>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    <div className="col-12">
                                        <button className="btn btn-xs btn-outline-secondary border-dashed w-100 py-2" onClick={() => addSection(activeTabIdx)}>
                                            <i className="fa fa-plus me-1"></i> Add Section
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </main>

                {/* 3. Preview & JSON Pane */}
                <aside className={`designer-preview-pane ${showPreview ? '' : 'collapsed'}`}>
                    <div className="preview-header">
                        <span><i className="fa fa-mobile-alt me-2"></i> Form Preview</span>
                    </div>
                    <div className="preview-content bg-light">
                        <div className="card shadow-sm border-0" style={{borderRadius:'12px'}}>
                            <div className="card-body p-3">
                                <h6 className="fw-bold mb-3">{layout[activeTabIdx]?.label}</h6>
                                {layout[activeTabIdx]?.sections.map((sec, i) => (
                                    <div key={i} className="mb-4">
                                        <div className="fs-10 fw-bold text-uppercase text-muted border-bottom mb-2 pb-1">{sec.label}</div>
                                        <div className="row g-2">
                                            {sec.fields.map((f, j) => {
                                                const col = getCol(f.name);
                                                return (
                                                    <div key={j} className={`col-${f.width === 6 ? '6' : '12'}`}>
                                                        <label className="fs-10 fw-bold text-muted mb-1">{col.label}</label>
                                                        <div className="bg-white border rounded px-2 py-1 text-muted fs-11" style={{height:'28px', opacity:0.6}}>
                                                            {col.field_type === 'boolean' ? '[ ]' : '...'}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div className="json-editor-pane">
                        <div className="preview-header border-top">
                            <span><i className="fa fa-code me-2"></i> layout_json</span>
                            {jsonError && <span className="text-danger fs-10 fw-normal">Invalid JSON</span>}
                        </div>
                        <textarea id="json-editor-textarea" value={JSON.stringify(layout, null, 2)} onChange={handleJsonChange} spellCheck="false" />
                    </div>
                </aside>
            </div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('aras-layout-designer-root'));
root.render(<LayoutDesigner />);
