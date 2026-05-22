import re

with open('ui/src/aras-core/components/ListView.tsx', 'r') as f:
    content = f.read()

old_table_start = "        {viewMode === 'list' && (\n          <table"
old_table_end = "          </table>\n        )}"

start_idx = content.find(old_table_start)
end_idx = content.find(old_table_end) + len(old_table_end)

if start_idx == -1 or end_idx == -1:
    print("Could not find table boundaries")
    exit(1)

new_code = """        {viewMode === 'list' && (
          <div className="flex flex-col divide-y divide-[var(--aras-border)] min-w-[800px]">
            {/* Desktop Header Row */}
            <div className="hidden md:flex items-center px-4 md:px-6 py-3 bg-[var(--aras-table-head)] border-b border-[var(--aras-border)] text-[10px] font-bold text-[var(--aras-muted)] uppercase tracking-wider sticky top-0 z-10">
              <div className="w-12 shrink-0">
                <button onClick={handleSelectAll} className="hover:text-[var(--aras-accent)] transition-colors">
                  {selectedIds.length === data.length && data.length > 0 ? <CheckSquare size={16} className="text-[var(--aras-accent)]" /> : <Square size={16} />}
                </button>
              </div>
              <div className="w-12 shrink-0"></div>
              
              {orderedFields.map((field, idx) => (
                <div 
                  key={field.name}
                  className={`flex items-center gap-1.5 cursor-pointer hover:text-[var(--aras-text)] ${idx === 0 ? 'flex-1' : idx === orderedFields.length - 1 ? 'w-32 justify-end' : 'flex-1'}`}
                  onClick={() => {
                    if (orderBy === field.name) setDesc(!desc)
                    else { setOrderBy(field.name); setDesc(true); }
                  }}
                >
                  {vocabulary.get(field.label)}
                  {orderBy === field.name && (desc ? <ChevronDown size={14} className="text-[var(--aras-accent)]" /> : <ChevronUp size={14} className="text-[var(--aras-accent)]" />)}
                </div>
              ))}
              <div className="w-10 shrink-0"></div>
            </div>

            {loading ? (
              [...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse p-4 md:p-6 flex items-center gap-4">
                  <div className="w-5 h-5 bg-[var(--aras-panel-soft)] rounded"></div>
                  <div className="w-12 h-12 bg-[var(--aras-panel-soft)] rounded-2xl"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-[var(--aras-panel-soft)] rounded w-1/3"></div>
                    <div className="h-3 bg-[var(--aras-panel-soft)] rounded w-1/4"></div>
                  </div>
                </div>
              ))
            ) : data.length === 0 ? (
              <div className="px-6 py-20 text-center">
                <div className="max-w-xs mx-auto flex flex-col items-center text-[var(--aras-muted)]">
                  {search || filters.length > 0 ? (
                    <>
                      <Search size={48} className="mb-4 opacity-20" />
                      <p className="text-[15px] font-bold text-[var(--aras-text)]">No records match your search.</p>
                      <button onClick={() => {setSearch(''); setFilters([]);}} className="mt-3 text-sm text-[var(--aras-accent)] font-bold hover:underline">Clear filters</button>
                    </>
                  ) : (
                    <>
                      <Plus size={48} className="mb-4 opacity-20" />
                      <p className="text-[15px] font-bold text-[var(--aras-text)]">No records yet.</p>
                      {onAdd && (
                        <button onClick={onAdd} className="mt-4 px-5 py-2.5 text-sm font-bold bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] shadow-sm hover:opacity-90 transition-opacity">
                          Create First Record
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            ) : (
              data.map((item) => {
                const primaryField = orderedFields[0];
                const secondaryField = orderedFields.find(f => f.name === 'id' || f.name.includes('no') || f.name.includes('code')) || orderedFields[1];
                const statusField = orderedFields.find(f => f.name === 'status' || f.name === 'workflow_status');
                const lastField = orderedFields[orderedFields.length - 1];
                
                const titleStr = String(item[`${primaryField?.name}_label`] ?? item[primaryField?.name] ?? '');
                const initials = titleStr.substring(0, 2).toUpperCase();
                
                return (
                  <div
                    key={item.id}
                    className={`p-4 md:p-5 flex items-center gap-3 md:gap-4 hover:bg-[var(--aras-panel-soft)] transition-colors cursor-pointer group ${selectedIds.includes(item.id) ? 'bg-[var(--aras-panel-soft)]/80' : ''}`}
                    onClick={() => onRowClick ? onRowClick(item.id) : null}
                  >
                    <div className="w-8 md:w-10 shrink-0" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleSelectOne(item.id)} className={`${selectedIds.includes(item.id) ? 'text-[var(--aras-accent)]' : 'text-[var(--aras-border-strong)] group-hover:text-[var(--aras-muted)]'} transition-colors`}>
                        {selectedIds.includes(item.id) ? <CheckSquare size={18} /> : <Square size={18} />}
                      </button>
                    </div>

                    <div className="hidden sm:flex w-10 h-10 md:w-12 md:h-12 rounded-[calc(var(--aras-radius)*0.8)] bg-[var(--aras-accent)]/10 text-[var(--aras-accent)] items-center justify-center font-bold text-xs md:text-sm shrink-0 shadow-inner">
                      {initials || '??'}
                    </div>

                    <div className="flex-1 min-w-0 flex flex-col md:flex-row md:items-center gap-1 md:gap-4">
                      {/* Primary Stack */}
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[14px] md:text-[15px] font-bold text-[var(--aras-text)] truncate">
                          {renderCellValue(item[`${primaryField?.name}_label`] ?? item[primaryField?.name], primaryField?.type || 'string', primaryField?.name)}
                        </h4>
                        {secondaryField && secondaryField.name !== primaryField?.name && (
                          <div className="text-[11px] md:text-xs font-semibold text-[var(--aras-muted)] font-mono mt-0.5 truncate">
                            {renderCellValue(item[`${secondaryField.name}_label`] ?? item[secondaryField.name], secondaryField.type, secondaryField.name)}
                          </div>
                        )}
                      </div>
                      
                      {/* Middle Fields */}
                      <div className="hidden lg:flex flex-1 items-center gap-4">
                        {orderedFields.slice(1, -1).map(field => {
                          if (field.name === secondaryField?.name || field.name === statusField?.name) return null;
                          return (
                            <div key={field.name} className="flex-1 truncate text-[13px] text-[var(--aras-muted)] font-medium">
                              {renderCellValue(item[`${field.name}_label`] ?? item[field.name], field.type, field.name)}
                            </div>
                          )
                        })}
                      </div>

                      {/* Right Align Stack */}
                      <div className="text-left md:text-right shrink-0 mt-2 md:mt-0 flex flex-row md:flex-col items-center md:items-end justify-between md:justify-center w-full md:w-auto">
                        <div className="text-[13px] md:text-[14px] font-bold text-[var(--aras-text)] font-mono order-2 md:order-1 md:w-32 md:text-right">
                          {lastField && lastField.name !== primaryField?.name && lastField.name !== statusField?.name 
                            ? renderCellValue(item[`${lastField.name}_label`] ?? item[lastField.name], lastField.type, lastField.name) 
                            : ''}
                        </div>
                        <div className="order-1 md:order-2 md:mt-1.5 flex items-center justify-end">
                          {statusField && renderCellValue(item[`${statusField.name}_label`] ?? item[statusField.name], statusField.type, statusField.name)}
                          {!statusField && <span className="text-[10px] text-[var(--aras-muted)] font-bold">#{item.id}</span>}
                        </div>
                      </div>
                    </div>

                    <div className="hidden md:flex items-center justify-center w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteOne(item)
                        }}
                        className="p-2 text-[var(--aras-muted)] hover:text-rose-500 hover:bg-rose-50 rounded-[var(--aras-radius)] transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )}"""

content = content[:start_idx] + new_code + content[end_idx:]

with open('ui/src/aras-core/components/ListView.tsx', 'w') as f:
    f.write(content)
print("Replaced!")