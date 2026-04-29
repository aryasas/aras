const { useState, useEffect, useCallback, useRef } = React;

    // Helper to get CSRF token
    const getCsrf = () => {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "{{ csrf_token() }}";
    };

    function FormBuilder() {
        const [table, setTable] = useState(null);
        const [columns, setColumns] = useState([]);
        const [layout, setLayout] = useState([]);
        const [activeTabIdx, setActiveTabIdx] = useState(0);
        const [loading, setLoading] = useState(true);
        const [dragOverSection, setDragOverSection] = useState(null);
        const [dragOverItem, setDragOverItem] = useState(null);
        const [draggedItem, setDraggedItem] = useState(null);

        const refreshData = useCallback(() => {
            const tableId = window.FORM_BUILDER_TABLE_ID;
            const childTables = window.FORM_BUILDER_CHILD_TABLES || [];
            setLoading(true);
            Promise.all([
                fetch(`/api/admin/apps/tables/${tableId}/`).then(r => r.json()),
                fetch(`/api/admin/apps/tables/columns/?filter[table_id]=${tableId}&per_page=200`).then(r => r.json())
            ]).then(([tableData, colsData]) => {
                // SYSTEM FIELDS GUARD: Match with arasCore/lib/forms.py _FORM_HIDDEN
                const systemFields = [
                    'id', 'created_at', 'updated_at', 'deleted_at', 
                    'created_by_id', 'updated_by_id', 'is_active',
                    'owner_id', 'tenant_id', 'posted_by', 'posted_at',
                    'created_by', 'modified_by', 'modified_at',
                    'posted_by_id', 'modified_by_id', 'owner', 'tenant'
                ];
                
                // 1. FILTER & DEDUPLICATE COLUMNS
                let colMap = new Map();
                (colsData.data || []).forEach(c => {
                    const cleanName = c.name.toLowerCase();
                    const isSystem = systemFields.includes(cleanName) || 
                                     (cleanName.endsWith('_id') && systemFields.includes(cleanName.replace('_id', '_by_id')));

                    if (c.show_in_form !== false && !isSystem) {
                        // Unique name deduplication
                        if (!colMap.has(c.name)) {
                            colMap.set(c.name, c);
                        }
                    }
                });
                
                // Add Child Tables to the map so they can be processed like columns
                childTables.forEach(ct => {
                    if (!colMap.has(ct.name)) {
                        colMap.set(ct.name, { ...ct, id: ct.name }); // Use name as unique ID
                    }
                });
                const fetchedCols = Array.from(colMap.values());
                setColumns(fetchedCols);

                if (tableData.id) {
                    setTable(tableData);
                    let parsed = tableData.layout_json;
                    let initialLayout = [];
                    try {
                        initialLayout = typeof parsed === 'string' ? JSON.parse(parsed) : (parsed || []);
                    } catch(e) { console.error("Layout parse error", e); }

                    // 2. BOOTSTRAP DEFAULT LAYOUT IF EMPTY
                    if (!Array.isArray(initialLayout) || initialLayout.length === 0) {
                        const nonChildFields = fetchedCols.filter(c => c.type !== 'child_table');
                        initialLayout = [{
                            type: 'tab',
                            label: tableData.title || 'General',
                            sections: [{
                                type: 'section', label: 'Main Details', width: 12,
                                fields: nonChildFields.slice(0, 10).map(c => ({ name: c.name, width: 6, type: 'field' }))
                            }]
                        }];
                    } else {
                        // Validate and heal existing layout
                        const normField = (f) => {
                            if (colMap.has(f.name)) return f;
                            const base = f.name.replace(/_id$/, '');
                            return colMap.has(base) ? { ...f, name: base } : f;
                        };
                        initialLayout = initialLayout.map(t => ({
                            ...t,
                            type: 'tab',
                            label: t.label || 'New Segment',
                            sections: (t.sections || []).map(s => ({
                                ...s,
                                type: 'section',
                                width: s.width || 12,
                                fields: (s.fields || []).map(normField).filter(f => colMap.has(f.name))
                            }))
                        }));
                    }
                    setLayout(initialLayout);
                    console.log("Layout Synced:", initialLayout);
                }
                setLoading(false);
            }).catch(err => { console.error("Refresh Error:", err); setLoading(false); });
        }, []);

        useEffect(() => { refreshData(); }, [refreshData]);

        // Auto-switch to new tab
        const prevLayoutLength = useRef(0);
        useEffect(() => {
            if (layout.length > prevLayoutLength.current && prevLayoutLength.current !== 0) {
                setActiveTabIdx(layout.length - 1);
            }
            prevLayoutLength.current = layout.length;
        }, [layout.length]);

        const getCol = (name) => columns.find(c => c.name === name) || { label: name, name: name, type: 'field', field_type: 'string' };
        
        const isFieldUsed = (fieldName) => {
            let used = false;
            layout.forEach(t => (t.sections || []).forEach(s => (s.fields || []).forEach(f => {
                // For child tables, the name in layout is the table name.
                if (f.type === 'child_table' && f.name === fieldName) {
                    used = true;
                } else if (f.name === fieldName) {
                    used = true;
                }
            })));
            return used;
        };

        const onDragStartNew = (e, field) => { setDraggedItem({ type: 'new', field }); };
        const onDragStartExisting = (e, fieldName, tIdx, sIdx, fIdx) => { setDraggedItem({ type: 'existing', fieldName, tIdx, sIdx, fIdx }); };

        const onFieldDragOver = (e, tIdx, sIdx, fIdx) => {
            e.preventDefault(); e.stopPropagation();
            const rect = e.currentTarget.getBoundingClientRect();
            const pos = (e.clientY - rect.top) < rect.height / 2 ? 'top' : 'bottom';
            setDragOverItem({ tIdx, sIdx, fIdx, pos });
            setDragOverSection(null);
        };

        const onSectionDragOver = (e, id) => {
            e.preventDefault();
            setDragOverSection(id);
            setDragOverItem(null);
        };

        const onDrop = (e, tIdx, sIdx) => {
            e.preventDefault();
            const currentDragged = draggedItem;
            const currentDragOver = dragOverItem;
            setDragOverSection(null); setDragOverItem(null); setDraggedItem(null);
            
            if (!currentDragged) return;

            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                let itemToMove;
                if (currentDragged.type === 'new') {
                    itemToMove = { name: currentDragged.field.name, width: 12, type: currentDragged.field.type };
                } else {
                    const sourceFields = nl[currentDragged.tIdx].sections[currentDragged.sIdx].fields;
                    itemToMove = sourceFields.splice(currentDragged.fIdx, 1)[0];
                }
                const targetSection = nl[tIdx].sections[sIdx];
                if (!targetSection.fields) targetSection.fields = [];

                if (currentDragOver && currentDragOver.tIdx === tIdx && currentDragOver.sIdx === sIdx) {
                    let insertIdx = currentDragOver.fIdx;
                    if (currentDragOver.pos === 'bottom') insertIdx++;
                    targetSection.fields.splice(insertIdx, 0, itemToMove);
                } else {
                    targetSection.fields.push(itemToMove);
                }
                return nl;
            });
        };

        const updateFieldWidth = (tIdx, sIdx, fIdx, width) => {
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].sections[sIdx].fields[fIdx].width = width;
                return nl;
            });
        };

        const updateSectionWidth = (tIdx, sIdx, width) => {
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].sections[sIdx].width = width;
                return nl;
            });
        };

        const updateTabLabel = (tIdx, label) => {
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].label = label;
                return nl;
            });
        };

        const updateSectionLabel = (tIdx, sIdx, label) => {
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].sections[sIdx].label = label;
                return nl;
            });
        };

        const addTab = () => {
            const label = prompt("New Tab Name:");
            if(label) {
                const newTab = { type: 'tab', label, sections: [{type:'section', label:'Main', width:12, fields:[]}] };
                setLayout(prev => [...prev, newTab]);
            }
        };

        const deleteTab = (tIdx) => {
            if(layout.length <= 1) return;
            if(!confirm('Archive this tab segment?')) return;
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl.splice(tIdx, 1);
                return nl;
            });
            setActiveTabIdx(0);
        };

        const addSection = (tIdx) => {
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].sections.push({ type:'section', label:'New Context', width: 12, fields:[] });
                return nl;
            });
        };

        const deleteSection = (tIdx, sIdx) => {
            if(!confirm('Remove section?')) return;
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].sections.splice(sIdx, 1);
                return nl;
            });
        };

        const deleteField = (tIdx, sIdx, fIdx) => {
            setLayout(prev => {
                const nl = JSON.parse(JSON.stringify(prev));
                nl[tIdx].sections[sIdx].fields.splice(fIdx, 1);
                return nl;
            });
        };

        const saveLayout = async () => {
            try {
                // Ensure correct structure for engine compatibility
                const layoutToSave = layout.map(t => ({
                    ...t,
                    type: 'tab',
                    sections: (t.sections || []).map(s => ({
                        ...s,
                        type: 'section',
                        width: s.width || 12,
                        fields: (s.fields || []).map(f => ({
                            name: f.name,
                            width: f.width || 12,
                            type: f.type || 'field' // Ensure type is saved
                        }))
                    }))
                })).filter(t => t.label);

                console.log("Committing Layout:", layoutToSave);

                const res = await fetch(`/admin/apps/${table.app_id}/tables/${table.id}/layout`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                    body: JSON.stringify({ layout: layoutToSave })
                });

                if (!res.ok) {
                    const errorText = await res.text();
                    throw new Error(`Server status ${res.status}: ${errorText}`);
                }

                const data = await res.json();
                if (data.ok) {
                    Swal.fire({ 
                        icon: 'success', 
                        title: 'Architecture Committed', 
                        text: 'Layout successfully synchronized with database.',
                        timer: 2000, 
                        showConfirmButton: false,
                        toast: true,
                        position: 'top-end'
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Commit Failed', text: data.error });
                }
            } catch (err) { 
                console.error("Save error detail:", err);
                Swal.fire({ icon: 'error', title: 'System Error', text: err.message }); 
            }
        };

        const MockInput = ({ col }) => {
            // Mock for Child Table
            if (col.type === 'child_table') {
                return <div className="mock-child-table"><i className="fa fa-list me-2"></i> {col.label} List</div>;
            }
            if (col.field_type === 'boolean') {
                return <div className="aras-toggle active"><span className="aras-toggle-track" style={ {background:'var(--aras-accent)'} }><span className="aras-toggle-thumb" style={ {transform:'translateX(16px)'} }></span></span><span className="aras-toggle-label" style={ {fontSize:'12px'} }>{col.label}</span></div>;
            }
            if (col.field_type === 'text' || col.field_type === 'json') return <div className="aras-form-textarea-mock">Value placeholder...</div>;
            return <div className="aras-form-input-mock">Value placeholder...</div>;
        };

        if (loading) return <div className="text-center py-5"><div className="spinner-grow" style={ {color:'var(--aras-accent)'} }></div></div>;
        if (!table) return <div className="alert alert-danger">Table context lost.</div>;
        
        const activeTab = layout[activeTabIdx] || layout[0];

        return (
            <div className="aras-builder-wrapper">
                <aside className="builder-sidebar">
                    <div className="builder-sidebar-header"><h6>Architecture Toolset</h6></div>
                    <div className="field-list">
                        <div className="mb-3 px-1"><a href={`/admin/apps/${table.app_id}/tables/${table.id}/columns`} className="btn btn-outline-secondary btn-xs w-100 py-2" style={ {borderStyle:'dashed'} }><i className="fa fa-plus me-1"></i> Add Data Point</a></div>
                        {columns.map(col => (
                            <div key={col.id} className={`field-draggable ${isFieldUsed(col.name) ? 'is-used' : ''} ${col.type === 'child_table' ? 'is-component' : ''}`} draggable={!isFieldUsed(col.name)} onDragStart={(e) => onDragStartNew(e, col)}>
                                <i className={`fa ${col.type === 'child_table' ? 'fa-table' : 'fa-grip-vertical'} text-muted`}></i><span className="flex-grow-1">{col.label}</span>{col.is_standard_column && <span className="core-badge">CORE</span>}
                            </div>
                        ))}
                    </div>
                    <div className="p-3 border-top bg-light"><button className="btn btn-block py-2 shadow-sm" style={ {background:'var(--aras-accent)', color:'#fff', fontWeight:600} } onClick={saveLayout}><i className="fa fa-save me-2"></i> Commit Architecture</button></div>
                </aside>

                <main className="builder-canvas">
                    <div className="canvas-header">
                        <h4>{table.title} <small className="text-muted italic ms-2" style={ {fontFamily:'var(--aras-font-serif)', fontSize:'14px'} }>— Designer</small></h4>
                        <button className="btn btn-sm" style={ {border:'1px solid var(--aras-accent)', color:'var(--aras-accent)', fontWeight:600} } onClick={addTab}>+ NEW TAB</button>
                    </div>
                    <div className="mock-form-card">
                        <div className="mock-tab-strip">
                            {layout.map((tab, idx) => (<div key={idx} className={`mock-tab-item ${activeTabIdx === idx ? 'active' : ''}`} onClick={() => setActiveTabIdx(idx)}>{tab.label}</div>))}
                        </div>
                        {activeTab && (
                            <div className="active-tab-container">
                                <div className="tab-config-strip">
                                    <div className="d-flex align-items-center gap-3">
                                        <small className="fw-bold text-muted">TAB LABEL:</small>
                                        <input className="form-control form-control-sm py-0" style={ {width:'180px', height:'26px', fontSize:'12px', fontWeight:600} } value={activeTab.label} onChange={(e) => updateTabLabel(activeTabIdx, e.target.value)} />
                                    </div>
                                    <div className="d-flex gap-2">
                                        <button className="btn btn-link btn-xs text-primary fw-bold" onClick={saveLayout}><i className="fa fa-check"></i> QUICK SAVE</button>
                                        <button className="btn btn-link btn-xs text-danger" onClick={() => deleteTab(activeTabIdx)}><i className="fa fa-trash"></i> DELETE TAB</button>
                                    </div>
                                </div>
                                <div className="mock-form-body">
                                    <div className="row">
                                        {(activeTab.sections || []).map((sec, sIdx) => {
                                            const sectionId = `${activeTabIdx}-${sIdx}`;
                                            const sWidth = sec.width || 12;
                                            return (
                                                <div key={sIdx} className={`col-md-${sWidth}`}>
                                                    <div className={`mock-section ${dragOverSection === sectionId ? 'drag-over' : ''}`} onDragOver={(e) => onSectionDragOver(e, sectionId)} onDragLeave={() => setDragOverSection(null)} onDrop={(e) => onDrop(e, activeTabIdx, sIdx)}>
                                                        <div className="section-title-wrap">
                                                            <div className="d-flex align-items-center gap-3 flex-grow-1">
                                                                <input className="section-title-input" value={sec.label || ''} placeholder="SECTION IDENTIFIER" onChange={(e) => updateSectionLabel(activeTabIdx, sIdx, e.target.value)} />
                                                                <div className="width-picker">
                                                                    <button className={`width-btn ${sWidth === 12 ? 'active' : ''}`} onClick={() => updateSectionWidth(activeTabIdx, sIdx, 12)}>FULL</button>
                                                                    <button className={`width-btn ${sWidth === 6 ? 'active' : ''}`} onClick={() => updateSectionWidth(activeTabIdx, sIdx, 6)}>HALF</button>
                                                                </div>
                                                            </div>
                                                            <i className="fa fa-times cursor-pointer text-danger opacity-25 ms-3" onClick={() => deleteSection(activeTabIdx, sIdx)}></i>
                                                        </div>
                                                        <div className="row align-items-start" style={ {minHeight:'60px'} }>
                                                            {(sec.fields || []).map((field, fIdx) => {
                                                                const col = getCol(field.name);
                                                                const fWidth = field.width || 12;
                                                                const isTarget = dragOverItem?.tIdx === activeTabIdx && dragOverItem?.sIdx === sIdx && dragOverItem?.fIdx === fIdx;
                                                                return (
                                                                    <div key={fIdx} className={`col-md-${fWidth} mb-2`}>
                                                                        <div className={`mock-aras-row ${draggedItem?.fieldName === field.name ? 'is-dragging' : ''} ${isTarget ? `drag-target-${dragOverItem.pos}` : ''}`} draggable onDragStart={(e) => onDragStartExisting(e, field.name, activeTabIdx, sIdx, fIdx)} onDragOver={(e) => onFieldDragOver(e, activeTabIdx, sIdx, fIdx)} onDragLeave={() => setDragOverItem(null)}>
                                                                            <div className="mock-aras-label">{col.label}</div>
                                                                            <div className="flex-grow-1"><MockInput col={col} /></div>
                                                                            <div className="field-actions">
                                                                                <div className="width-picker">
                                                                                    <button className={`width-btn ${fWidth === 12 ? 'active' : ''}`} onClick={() => updateFieldWidth(activeTabIdx, sIdx, fIdx, 12)}>W:12</button>
                                                                                    <button className={`width-btn ${fWidth === 6 ? 'active' : ''}`} onClick={() => updateFieldWidth(activeTabIdx, sIdx, fIdx, 6)}>W:6</button>
                                                                                </div>
                                                                                <button className="btn btn-xs btn-outline-danger rounded" onClick={() => deleteField(activeTabIdx, sIdx, fIdx)}><i className="fa fa-trash"></i></button>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                            {(!sec.fields || sec.fields.length === 0) && <div className="col-12 text-center py-4 text-muted small border rounded" style={ {borderStyle:'dashed', borderColor:'var(--aras-line-2)'} }><i className="fa fa-plus me-1"></i> Drop Data Point</div>}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <button className="btn-ghost-studio" onClick={() => addSection(activeTabIdx)}>+ ADD NEW SECTION</button>
                                </div>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        );
    }

    const root = ReactDOM.createRoot(document.getElementById('aras-form-builder-root'));
    root.render(<FormBuilder />);