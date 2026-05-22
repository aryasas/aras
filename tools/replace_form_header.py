with open('ui/src/aras-core/components/DynamicForm.tsx', 'r') as f:
    content = f.read()

start_marker = "      {/* ── Sticky Toolbar Header ────────────────────────────────────────── */}"
end_marker = "      {/* ── Workflow & Custom Actions ────────────────────────────────────── */}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find boundaries")
    exit(1)

new_header = """      {/* ── Portaled Header Actions ──────────────────────────────────────── */}
      {document.getElementById('header-actions-portal') && createPortal(
        <div className="flex items-center gap-2 md:gap-3 shrink-0 mr-2 md:mr-4 border-r border-[var(--aras-border)] pr-2 md:pr-4">
          <button
            onClick={onCancel}
            className="group flex h-9 w-9 md:h-10 md:w-10 items-center justify-center rounded-[var(--aras-radius)] border border-[var(--aras-border-strong)] bg-[var(--aras-panel)] text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)] transition-all shadow-sm"
            title="Go Back"
          >
            <ArrowLeft size={18} className="group-hover:-translate-x-0.5 transition-transform" />
          </button>
          
          <div className="hidden lg:flex items-center gap-1 border-r border-[var(--aras-border)] pr-2 mr-2">
            {currentId != null && metadata.is_auditable && (
              <button onClick={handleShowHistory} className="p-2 hover:bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius)] text-[var(--aras-muted)] transition-colors" title="View History"><HistoryIcon size={18} /></button>
            )}
            <button onClick={handleCustomize} className="p-2 hover:bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius)] text-[var(--aras-muted)] transition-colors" title="Customize Form"><Settings size={18} /></button>
            {metadata.app_name === 'erp_accounting' && currentId != null && (
              <button onClick={() => setShowPrintPreview(true)} className="p-2 hover:bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius)] text-[var(--aras-muted)] transition-colors" title="Print Document"><Printer size={18} /></button>
            )}
            {currentId != null && (
              <button onClick={handleDelete} className="p-2 hover:bg-rose-50 rounded-[var(--aras-radius)] text-rose-400 hover:text-rose-600 transition-colors" title="Delete record"><Trash2 size={18} /></button>
            )}
          </div>

          {currentId != null && (
            <button
              onClick={handleDuplicate}
              className="hidden md:flex h-9 md:h-10 items-center gap-2 rounded-[var(--aras-radius)] border border-[var(--aras-border-strong)] bg-[var(--aras-panel)] px-4 text-xs md:text-sm font-bold text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)] transition-all shadow-sm"
            >
              <Copy size={16} />
              <span>Duplicate</span>
            </button>
          )}

          <button
            onClick={() => handleSubmit()}
            disabled={saving}
            className="flex h-9 md:h-10 items-center gap-2 rounded-[var(--aras-radius)] bg-[var(--aras-accent)] px-4 md:px-6 text-xs md:text-sm font-bold text-white shadow-md hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {saving ? <RefreshCw className="animate-spin" size={16} /> : <Save size={16} />}
            <span className="hidden md:inline">{saving ? 'Saving...' : 'Save Record'}</span>
          </button>
        </div>,
        document.getElementById('header-actions-portal')!
      )}

"""

content = content[:start_idx] + new_header + content[end_idx:]

with open('ui/src/aras-core/components/DynamicForm.tsx', 'w') as f:
    f.write(content)

print("Form header replaced correctly!")
