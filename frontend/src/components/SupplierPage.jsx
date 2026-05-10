import { useState, useEffect, useRef, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from '@tanstack/react-form'
import {
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  flexRender,
} from '@tanstack/react-table'
import { api } from '../lib/api'

// ── Styles ────────────────────────────────────────────────────────────────────
function injectFont() {
  if (document.getElementById('sp-fonts')) return
  const l = document.createElement('link')
  l.id = 'sp-fonts'
  l.rel = 'stylesheet'
  l.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
  document.head.appendChild(l)
}

function injectStyles() {
  if (document.getElementById('sp-styles')) return
  const s = document.createElement('style')
  s.id = 'sp-styles'
  s.textContent = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Inter, system-ui, -apple-system, sans-serif; }
    @keyframes sp-spin { to { transform: rotate(360deg); } }
    @keyframes sp-fadein { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
    .sp-fade { animation: sp-fadein 0.15s ease both; }
    .sp-input:focus { outline: none; border-color: #2563EB !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.10); }
    .sp-input::placeholder { color: #9CA3AF; }
    .sp-btn { transition: background 0.1s; }
    .sp-btn:hover:not(:disabled) { filter: brightness(0.95); }
    .sp-btn:active:not(:disabled) { transform: scale(0.98); }
    .sp-row { transition: background 0.06s; }
    .sp-row:hover { background: #F9FAFB !important; }
    .sp-row:hover .sp-more-btn { opacity: 1 !important; }
    .sp-scroll::-webkit-scrollbar { width: 4px; height: 4px; }
    .sp-scroll::-webkit-scrollbar-track { background: transparent; }
    .sp-scroll::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 99px; }
    .sp-tab { border-bottom: 2px solid transparent; transition: color 0.1s, border-color 0.1s; }
    .sp-tab:hover { color: #111827; border-color: #D1D5DB; }
    .sp-tab.active { color: #111827; border-bottom-color: #2563EB; font-weight: 500; }
    .sp-dropdown { position: absolute; top: calc(100% + 4px); left: 0; background: #fff; border: 1px solid #E5E7EB; border-radius: 8px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); z-index: 200; min-width: 160px; overflow: hidden; animation: sp-fadein 0.1s ease both; }
    .sp-dropdown-item { display: flex; align-items: center; gap: 8px; padding: 8px 14px; font-size: 13px; color: #374151; cursor: pointer; font-family: Inter, system-ui, sans-serif; }
    .sp-dropdown-item:hover { background: #F9FAFB; }
    .sp-dropdown-item.active { color: #2563EB; font-weight: 500; }
    .sp-nav-link { color: #6B7280; font-size: 13px; padding: 6px 12px; border-radius: 6px; cursor: pointer; transition: background 0.1s, color 0.1s; font-family: Inter, system-ui, sans-serif; }
    .sp-nav-link:hover { background: #F3F4F6; color: #111827; }
    .sp-nav-link.active { background: #EFF6FF; color: #2563EB; font-weight: 500; }
    .sp-sb-link { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 8px; color: #9CA3AF; transition: background 0.1s, color 0.1s; text-decoration: none; cursor: pointer; }
    .sp-sb-link:hover { background: #F3F4F6; color: #374151; }
    .sp-sb-link.active { background: #EFF6FF; color: #2563EB; }
  `
  document.head.appendChild(s)
}

// ── Constants ─────────────────────────────────────────────────────────────────
const APP = 'erp'
const RES = 'sup/supplier'
const F   = 'Inter, system-ui, -apple-system, sans-serif'

const LIST_COLS = [
  { name: 'code',    label: 'Code',          w: 120 },
  { name: 'name',    label: 'Supplier Name', w: null },
  { name: 'email',   label: 'Email',         w: 220 },
  { name: 'phone',   label: 'Phone',         w: 140 },
  { name: 'city',    label: 'City',          w: 130 },
  { name: 'country', label: 'Country',       w: 120 },
]

const FORM_SECTIONS = [
  {
    id: 'identity', label: 'Identity', cols: 3,
    fields: [
      { name: 'code',   label: 'Supplier Code', required: true, span: 1 },
      { name: 'name',   label: 'Company Name',  required: true, span: 2 },
      { name: 'tax_id', label: 'Tax ID / VAT',  span: 1 },
    ],
  },
  {
    id: 'contact', label: 'Contact', cols: 3,
    fields: [
      { name: 'email',  label: 'Email Address', type: 'email', span: 1 },
      { name: 'phone',  label: 'Phone',  span: 1 },
      { name: 'mobile', label: 'Mobile', span: 1 },
    ],
  },
  {
    id: 'location', label: 'Location', cols: 3,
    fields: [
      { name: 'address', label: 'Street Address', textarea: true, span: 3 },
      { name: 'city',    label: 'City',    span: 1 },
      { name: 'country', label: 'Country', span: 1 },
    ],
  },
  {
    id: 'financial', label: 'Financial', cols: 3,
    fields: [
      { name: 'payment_term_days', label: 'Payment Terms (days)', type: 'number', span: 1 },
      { name: 'credit_limit',      label: 'Credit Limit',         type: 'number', span: 1 },
      { name: 'bank_name',         label: 'Bank Name',    span: 1 },
      { name: 'bank_account_no',   label: 'Account No.',  span: 1 },
      { name: 'bank_account_name', label: 'Account Holder', span: 2 },
      { name: 'notes',             label: 'Internal Notes', textarea: true, span: 3 },
    ],
  },
]

const PER_PAGE_OPTIONS = [12, 25, 50, 100]

// ── Primitives ────────────────────────────────────────────────────────────────
function Spinner({ size = 16, color = '#2563EB' }) {
  return (
    <span style={{
      display: 'inline-block', width: size, height: size, flexShrink: 0,
      borderRadius: '50%', border: `2px solid ${color}30`, borderTopColor: color,
      animation: 'sp-spin 0.65s linear infinite',
    }} />
  )
}

function ChevronIcon({ dir = 'down', size = 10, color = '#9CA3AF' }) {
  const paths = {
    down: 'M2 4l4 4 4-4',
    up:   'M2 8l4-4 4 4',
    left: 'M8 2l-4 4 4 4',
    right:'M4 2l4 4-4 4',
  }
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" fill="none">
      <path d={paths[dir]} stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

// Generic dropdown wrapper
function Dropdown({ trigger, children, menuStyle = {} }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])
  return (
    <div style={{ position: 'relative', display: 'inline-block' }} ref={ref}>
      <div onClick={() => setOpen(o => !o)}>{trigger(open)}</div>
      {open && (
        <div className="sp-dropdown" style={menuStyle}>
          {typeof children === 'function' ? children(() => setOpen(false)) : children}
        </div>
      )}
    </div>
  )
}

// Filter select button (looks like the Leucine "Choose an option" dropdowns)
function FilterSelect({ label, value, options, onChange, placeholder = 'All' }) {
  const current = options.find(o => o.value === value)
  return (
    <Dropdown
      trigger={open => (
        <button style={{
          display: 'flex', alignItems: 'center', gap: 6,
          height: 36, padding: '0 12px', background: '#fff',
          border: '1px solid #D1D5DB', borderRadius: 6,
          fontFamily: F, fontSize: 13, color: value ? '#111827' : '#6B7280',
          cursor: 'pointer', whiteSpace: 'nowrap',
        }}>
          {label && <span style={{ color: '#6B7280', fontSize: 12, fontWeight: 500 }}>{label}:</span>}
          <span>{current?.label ?? placeholder}</span>
          <ChevronIcon dir={open ? 'up' : 'down'} size={10} />
        </button>
      )}
      menuStyle={{ minWidth: 180 }}
    >
      {close => (
        <>
          <div className={`sp-dropdown-item ${!value ? 'active' : ''}`} onClick={() => { onChange(null); close() }}>
            {placeholder}
          </div>
          {options.map(o => (
            <div key={o.value} className={`sp-dropdown-item ${value === o.value ? 'active' : ''}`}
              onClick={() => { onChange(o.value); close() }}>
              {o.label}
              {value === o.value && <svg style={{ marginLeft: 'auto' }} width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4L19 7" stroke="#2563EB" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
            </div>
          ))}
        </>
      )}
    </Dropdown>
  )
}

// ── Sidebar (icon-only, collapsible) ─────────────────────────────────────────
const SB_ITEMS = [
  { href: '/admin/',                    title: 'Dashboard',       icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7"/><rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7"/><rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7"/><rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7"/></svg>, label: 'Dashboard' },
  { href: '/admin/erp/',                title: 'ERP',             icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 9l9-6 9 6v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>, label: 'ERP' },
  { href: '/admin/erp/sup/supplier/',   title: 'Suppliers',       icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" stroke="currentColor" strokeWidth="1.7"/><path d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10l1 1h10M13 8h3l3 4v4h-4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>, label: 'Suppliers', active: true },
  { href: '/admin/erp/sup/purchase-order/', title: 'Purchase Orders', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>, label: 'Purchase Orders' },
]

const SB_BOTTOM = [
  { href: '/admin/settings/', title: 'Settings', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 15a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" strokeWidth="1.7"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" stroke="currentColor" strokeWidth="1.7"/></svg>, label: 'Settings' },
]

function Sidebar({ collapsed, onToggle }) {
  const W = collapsed ? 52 : 200
  return (
    <aside style={{
      width: W, flexShrink: 0,
      background: '#fff', borderRight: '1px solid #E5E7EB',
      display: 'flex', flexDirection: 'column',
      transition: 'width 0.2s cubic-bezier(0.4,0,0.2,1)',
      overflow: 'hidden',
    }}>
      {/* Logo + toggle */}
      <div style={{ height: 56, display: 'flex', alignItems: 'center', borderBottom: '1px solid #F3F4F6', flexShrink: 0, padding: '0 8px', gap: 6, overflow: 'hidden' }}>
        <a href="/admin/" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none', flexShrink: 0, width: 36, height: 36, justifyContent: 'center' }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: '#1D4ED8', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <span style={{ fontFamily: F, fontSize: 13, fontWeight: 700, color: '#fff' }}>A</span>
          </div>
        </a>
        {!collapsed && <span style={{ fontFamily: F, fontSize: 13, fontWeight: 700, color: '#111827', letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden' }}>Aras ERP</span>}
        {!collapsed && (
          <button onClick={onToggle} title="Collapse" className="sp-sb-link" style={{ marginLeft: 'auto', flexShrink: 0 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
        )}
      </div>

      {/* Nav items */}
      <nav style={{ flex: 1, padding: '8px 8px', display: 'flex', flexDirection: 'column', gap: 2, overflow: 'hidden' }}>
        {SB_ITEMS.map(item => (
          <a key={item.href} href={item.href} title={collapsed ? item.title : ''} className={`sp-sb-link ${item.active ? 'active' : ''}`}
            style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start', gap: 10, padding: collapsed ? '0' : '0 10px', borderRadius: 8, height: 36, display: 'flex', alignItems: 'center', textDecoration: 'none', fontFamily: F, fontSize: 13, fontWeight: item.active ? 500 : 400, whiteSpace: 'nowrap' }}>
            <span style={{ flexShrink: 0, display: 'flex' }}>{item.icon}</span>
            {!collapsed && item.label}
          </a>
        ))}
      </nav>

      {/* Bottom: settings + avatar + expand toggle */}
      <div style={{ padding: '8px 8px', borderTop: '1px solid #F3F4F6', display: 'flex', flexDirection: 'column', gap: 2, flexShrink: 0 }}>
        {SB_BOTTOM.map(item => (
          <a key={item.href} href={item.href} title={collapsed ? item.title : ''} className="sp-sb-link"
            style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start', gap: 10, padding: collapsed ? '0' : '0 10px', borderRadius: 8, height: 36, display: 'flex', alignItems: 'center', textDecoration: 'none', fontFamily: F, fontSize: 13, whiteSpace: 'nowrap' }}>
            <span style={{ flexShrink: 0, display: 'flex' }}>{item.icon}</span>
            {!collapsed && item.label}
          </a>
        ))}
        {/* User */}
        <div className="sp-sb-link" style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start', gap: 10, padding: collapsed ? '0' : '0 10px', borderRadius: 8, height: 36, display: 'flex', alignItems: 'center', cursor: 'default', whiteSpace: 'nowrap' }}>
          <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#DBEAFE', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <span style={{ fontFamily: F, fontSize: 10, fontWeight: 700, color: '#1D4ED8' }}>A</span>
          </div>
          {!collapsed && <span style={{ fontFamily: F, fontSize: 13, color: '#374151', fontWeight: 500 }}>Admin</span>}
        </div>
        {/* Expand toggle when collapsed */}
        {collapsed && (
          <button onClick={onToggle} title="Expand" className="sp-sb-link"
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'none', border: 'none', height: 36, borderRadius: 8, cursor: 'pointer' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
        )}
      </div>
    </aside>
  )
}

// ── Top bar (inside main content, above page) ─────────────────────────────────
function TopBar() {
  return (
    <div style={{ height: 56, flexShrink: 0, background: '#fff', borderBottom: '1px solid #E5E7EB', display: 'flex', alignItems: 'center', padding: '0 24px', gap: 16 }}>
      {/* Facility selector */}
      <Dropdown
        trigger={open => (
          <button style={{ display: 'flex', alignItems: 'center', gap: 6, height: 32, padding: '0 10px', background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 6, fontFamily: F, fontSize: 13, color: '#374151', cursor: 'pointer' }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M3 9l9-6 9 6v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Main Office
            <ChevronIcon dir={open ? 'up' : 'down'} size={9} />
          </button>
        )}
      >
        {close => ['Main Office', 'Branch A', 'Branch B'].map(f => (
          <div key={f} className="sp-dropdown-item" onClick={close}>{f}</div>
        ))}
      </Dropdown>
      <div style={{ flex: 1 }} />
      {/* Apps dot grid */}
      <button style={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'none', border: 'none', borderRadius: 6, cursor: 'pointer', color: '#9CA3AF' }}
        onMouseEnter={e => e.currentTarget.style.background = '#F3F4F6'}
        onMouseLeave={e => e.currentTarget.style.background = 'none'}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <circle cx="5" cy="5" r="1.8" fill="currentColor"/><circle cx="12" cy="5" r="1.8" fill="currentColor"/><circle cx="19" cy="5" r="1.8" fill="currentColor"/>
          <circle cx="5" cy="12" r="1.8" fill="currentColor"/><circle cx="12" cy="12" r="1.8" fill="currentColor"/><circle cx="19" cy="12" r="1.8" fill="currentColor"/>
          <circle cx="5" cy="19" r="1.8" fill="currentColor"/><circle cx="12" cy="19" r="1.8" fill="currentColor"/><circle cx="19" cy="19" r="1.8" fill="currentColor"/>
        </svg>
      </button>
    </div>
  )
}

// ── Form Field ────────────────────────────────────────────────────────────────
function FormField({ field, formApi }) {
  return (
    <formApi.Field
      name={field.name}
      validators={{ onChange: ({ value }) => field.required && !String(value ?? '').trim() ? 'Required' : undefined }}
    >
      {(f) => {
        const err = f.state.meta.errors.length > 0
        const base = {
          width: '100%', fontFamily: F, fontSize: 13, color: '#111827',
          background: '#fff', border: `1px solid ${err ? '#FCA5A5' : '#D1D5DB'}`,
          borderRadius: 6, padding: field.textarea ? '9px 11px' : '8px 11px',
          transition: 'border-color 0.15s, box-shadow 0.15s',
          resize: 'none', lineHeight: 1.5,
        }
        return (
          <div style={{ gridColumn: field.span ? `span ${field.span}` : 'span 1', display: 'flex', flexDirection: 'column', gap: 5 }}>
            <label style={{ fontFamily: F, fontSize: 12, fontWeight: 500, color: err ? '#EF4444' : '#374151' }}>
              {field.label}{field.required && <span style={{ color: '#EF4444', marginLeft: 2 }}>*</span>}
            </label>
            {field.textarea
              ? <textarea className="sp-input" rows={3} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} style={base} />
              : <input    className="sp-input" type={field.type ?? 'text'} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} style={base} />
            }
            {err && <span style={{ fontFamily: F, fontSize: 11, color: '#EF4444' }}>{f.state.meta.errors[0]}</span>}
          </div>
        )
      }}
    </formApi.Field>
  )
}

// ── Supplier Form ─────────────────────────────────────────────────────────────
function SupplierForm({ id, onDone }) {
  const qc    = useQueryClient()
  const isNew = !id
  const sync  = useRef(false)

  const { data: obj, isLoading } = useQuery({
    queryKey: [APP, RES, id],
    queryFn:  () => api.get(APP, RES, id),
    enabled:  !isNew,
  })

  const save = useMutation({
    mutationFn: data => isNew ? api.create(APP, RES, data) : api.update(APP, RES, id, data),
    onSuccess:  () => { qc.invalidateQueries([APP, RES]); onDone() },
  })

  const del = useMutation({
    mutationFn: () => api.delete(APP, RES, id),
    onSuccess:  () => { qc.invalidateQueries([APP, RES]); onDone() },
  })

  const form = useForm({ defaultValues: {}, onSubmit: async ({ value }) => save.mutate(value) })

  useEffect(() => {
    if (obj && !sync.current) {
      sync.current = true
      Object.entries(obj).forEach(([k, v]) => form.setFieldValue(k, v ?? ''))
    }
  }, [obj])

  if (isLoading) return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner size={24} />
    </div>
  )

  return (
    <div className="sp-fade" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Sub-header */}
      <div style={{ flexShrink: 0, background: '#fff', borderBottom: '1px solid #E5E7EB', height: 52, padding: '0 28px', display: 'flex', alignItems: 'center', justifyContents: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={onDone} className="sp-btn"
            style={{ display: 'flex', alignItems: 'center', gap: 5, fontFamily: F, fontSize: 13, color: '#6B7280', background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}
          >
            <ChevronIcon dir="left" size={10} color="#9CA3AF" /> Back
          </button>
          <span style={{ color: '#E5E7EB' }}>|</span>
          <span style={{ fontFamily: F, fontSize: 14, fontWeight: 600, color: '#111827' }}>{isNew ? 'New Supplier' : (obj?.name ?? `Supplier #${id}`)}</span>
          {!isNew && <span style={{ fontFamily: F, fontSize: 11, fontWeight: 600, color: '#1D4ED8', background: '#EFF6FF', padding: '2px 8px', borderRadius: 20 }}>#{String(id).padStart(5, '0')}</span>}
        </div>
        {!isNew && (
          <button onClick={() => window.confirm(`Delete "${obj?.name}"?`) && del.mutate()} disabled={del.isPending} className="sp-btn"
            style={{ display: 'flex', alignItems: 'center', gap: 5, fontFamily: F, fontSize: 13, color: '#DC2626', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', opacity: del.isPending ? 0.5 : 1 }}
          >
            Delete
          </button>
        )}
      </div>

      {/* Body */}
      <div className="sp-scroll" style={{ flex: 1, overflow: 'auto', padding: '32px 28px 48px', background: '#F9FAFB' }}>
        <div style={{ maxWidth: 760, margin: '0 auto' }}>
          {save.isError && (
            <div style={{ marginBottom: 16, padding: '10px 14px', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 7, fontFamily: F, fontSize: 13, color: '#DC2626' }}>
              {save.error.message}
            </div>
          )}

          <form onSubmit={e => { e.preventDefault(); e.stopPropagation(); form.handleSubmit() }} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {FORM_SECTIONS.map(sec => (
              <div key={sec.id} style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, overflow: 'hidden' }}>
                <div style={{ padding: '12px 20px', borderBottom: '1px solid #F3F4F6', background: '#F9FAFB' }}>
                  <span style={{ fontFamily: F, fontSize: 12, fontWeight: 600, color: '#374151' }}>{sec.label}</span>
                </div>
                <div style={{ padding: '20px', display: 'grid', gridTemplateColumns: `repeat(${sec.cols}, 1fr)`, gap: 16 }}>
                  {sec.fields.map(f => <FormField key={f.name} field={f} formApi={form} />)}
                </div>
              </div>
            ))}

            <div style={{ display: 'flex', justifyContents: 'flex-end', gap: 8, paddingTop: 4 }}>
              <button type="button" onClick={onDone} className="sp-btn"
                style={{ fontFamily: F, fontSize: 13, fontWeight: 500, color: '#6B7280', background: '#fff', border: '1px solid #E5E7EB', cursor: 'pointer', padding: '8px 18px', borderRadius: 6 }}
              >
                Cancel
              </button>
              <form.Subscribe selector={s => [s.canSubmit, s.isSubmitting]}>
                {([can, submitting]) => (
                  <button type="submit" disabled={!can || submitting || save.isPending} className="sp-btn"
                    style={{ display: 'flex', alignItems: 'center', gap: 7, fontFamily: F, fontSize: 13, fontWeight: 600, color: '#fff', background: '#2563EB', border: 'none', cursor: 'pointer', padding: '8px 20px', borderRadius: 6, opacity: (!can || save.isPending) ? 0.6 : 1 }}
                  >
                    {(submitting || save.isPending) ? <Spinner size={13} color="#fff" /> : null}
                    {isNew ? 'Create Supplier' : 'Save Changes'}
                  </button>
                )}
              </form.Subscribe>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// ── More Actions dropdown per row ─────────────────────────────────────────────
function MoreMenu({ row, onEdit, accent }) {
  return (
    <Dropdown
      trigger={open => (
        <button className="sp-more-btn" onClick={e => e.stopPropagation()} style={{
          opacity: 0, display: 'flex', alignItems: 'center', gap: 3,
          fontFamily: F, fontSize: 12, fontWeight: 500, color: '#2563EB',
          background: 'none', border: 'none', cursor: 'pointer', padding: '3px 0',
          transition: 'opacity 0.1s',
        }}>
          More <ChevronIcon dir={open ? 'up' : 'down'} size={9} color="#2563EB" />
        </button>
      )}
      menuStyle={{ minWidth: 150, right: 0, left: 'auto' }}
    >
      {close => (
        <>
          <div className="sp-dropdown-item" onClick={e => { e.stopPropagation(); onEdit(row.original.id); close() }}>
            View / Edit
          </div>
          <div className="sp-dropdown-item" style={{ color: '#DC2626' }} onClick={e => { e.stopPropagation(); close() }}>
            Delete
          </div>
        </>
      )}
    </Dropdown>
  )
}

// ── Supplier List ─────────────────────────────────────────────────────────────
function SupplierList({ onEdit, onNew }) {
  const [page, setPage]       = useState(1)
  const [perPage, setPerPage] = useState(25)
  const [q, setQ]             = useState('')
  const [rowSel, setRowSel]   = useState({})
  const [activeTab, setTab]   = useState('all')
  const qc = useQueryClient()

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: [APP, RES, page, q],
    queryFn:  () => api.list(APP, RES, { page, q: q || undefined }),
    keepPreviousData: true,
  })

  const rows       = data?.data  ?? []
  const total      = data?.meta?.total ?? rows.length
  const totalPages = Math.max(1, Math.ceil(total / perPage))
  const selCnt     = Object.keys(rowSel).length

  const TABS = [
    { key: 'all',    label: 'All Suppliers' },
    { key: 'active', label: 'Active' },
    { key: 'inactive', label: 'Inactive' },
  ]

  const colDefs = useMemo(() => [
    {
      id: 'sel', size: 44, enableSorting: false,
      header: ({ table }) => (
        <input type="checkbox"
          style={{ width: 14, height: 14, accentColor: '#2563EB', cursor: 'pointer' }}
          checked={table.getIsAllPageRowsSelected()}
          onChange={table.getToggleAllPageRowsSelectedHandler()} />
      ),
      cell: ({ row }) => (
        <input type="checkbox"
          style={{ width: 14, height: 14, accentColor: '#2563EB', cursor: 'pointer' }}
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          onClick={e => e.stopPropagation()} />
      ),
    },
    ...LIST_COLS.map(col => ({
      accessorKey: col.name,
      header: col.label,
      size: col.w ?? undefined,
      cell: info => {
        const v = info.getValue()
        if (col.name === 'code') return (
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12, fontWeight: 500, color: '#374151', background: '#F3F4F6', padding: '2px 7px', borderRadius: 4 }}>{v ?? '—'}</span>
        )
        if (!v) return <span style={{ color: '#D1D5DB' }}>—</span>
        return <span style={{ fontFamily: F, fontSize: 13, color: '#111827' }}>{v}</span>
      },
    })),
    {
      id: 'action', size: 80, enableSorting: false,
      header: () => null,
      cell: ({ row }) => <MoreMenu row={row} onEdit={onEdit} />,
    },
  ], [onEdit])

  const table = useReactTable({
    data: rows, columns: colDefs,
    state: { rowSelection: rowSel },
    enableRowSelection: true,
    onRowSelectionChange: setRowSel,
    getCoreRowModel:   getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    autoResetPageIndex: false,
  })

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#fff', minHeight: 0 }}>

      {/* Page header */}
      <div style={{ padding: '24px 28px 0', flexShrink: 0 }}>
        <h1 style={{ fontFamily: F, fontSize: 22, fontWeight: 700, color: '#111827', margin: '0 0 2px', letterSpacing: '-0.02em' }}>Suppliers</h1>
        <p style={{ fontFamily: F, fontSize: 13, color: '#6B7280', margin: '0 0 16px' }}>Create, view or edit your Suppliers and vendor records.</p>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid #E5E7EB' }}>
          {TABS.map(tab => (
            <button key={tab.key} onClick={() => setTab(tab.key)}
              className={`sp-tab ${activeTab === tab.key ? 'active' : ''}`}
              style={{
                fontFamily: F, fontSize: 13, fontWeight: activeTab === tab.key ? 500 : 400,
                color: activeTab === tab.key ? '#111827' : '#6B7280',
                background: 'none', border: 'none', padding: '10px 16px',
                cursor: 'pointer', marginBottom: -1,
              }}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filter / search row */}
      <div style={{ padding: '12px 28px', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 10, borderBottom: '1px solid #F3F4F6' }}>
        <FilterSelect
          label="Status"
          value={null}
          options={[{ value: 'active', label: 'Active' }, { value: 'inactive', label: 'Inactive' }]}
          onChange={() => {}}
        />
        <FilterSelect
          label="Country"
          value={null}
          options={[{ value: 'id', label: 'Indonesia' }, { value: 'us', label: 'United States' }, { value: 'sg', label: 'Singapore' }]}
          onChange={() => {}}
        />

        {/* Search */}
        <div style={{ position: 'relative', flex: 1, maxWidth: 340 }}>
          <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#9CA3AF', pointerEvents: 'none', display: 'flex' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="1.8"/><path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
          </span>
          <input className="sp-input" type="text" value={q}
            onChange={e => { setQ(e.target.value); setPage(1) }}
            placeholder="Search suppliers…"
            style={{ fontFamily: F, fontSize: 13, color: '#111827', background: '#fff', border: '1px solid #D1D5DB', borderRadius: 6, padding: '8px 12px 8px 34px', width: '100%', transition: 'border-color 0.15s, box-shadow 0.15s' }}
          />
        </div>

        {/* Show archived toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto' }}>
          <div style={{ width: 32, height: 18, borderRadius: 9, background: '#E5E7EB', position: 'relative', cursor: 'pointer' }}
            onClick={() => {}}>
            <div style={{ position: 'absolute', top: 2, left: 2, width: 14, height: 14, borderRadius: '50%', background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.2)', transition: 'left 0.15s' }} />
          </div>
          <span style={{ fontFamily: F, fontSize: 13, color: '#6B7280' }}>Show Archived</span>
        </div>

        {/* Refresh */}
        <button onClick={() => refetch()} className="sp-btn" title="Refresh"
          style={{ width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContents: 'center', background: '#fff', border: '1px solid #E5E7EB', borderRadius: 6, cursor: 'pointer', color: '#9CA3AF' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: isFetching ? 'sp-spin 0.8s linear infinite' : 'none' }}>
            <path d="M4 4v5h5M20 20v-5h-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M4.09 9a9 9 0 1014.82 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
        </button>

        {/* New supplier CTA */}
        <button onClick={onNew} className="sp-btn"
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: F, fontSize: 13, fontWeight: 600, color: '#fff', background: '#2563EB', border: 'none', borderRadius: 6, padding: '0 18px', height: 36, cursor: 'pointer', whiteSpace: 'nowrap' }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="white" strokeWidth="2.5" strokeLinecap="round"/></svg>
          Add Supplier
        </button>
      </div>

      {error && (
        <div style={{ padding: '10px 28px', background: '#FEF2F2', borderBottom: '1px solid #FECACA', fontFamily: F, fontSize: 13, color: '#DC2626', flexShrink: 0 }}>
          {error.message}
        </div>
      )}

      {selCnt > 0 && (
        <div style={{ padding: '8px 28px', background: '#EFF6FF', borderBottom: '1px solid #BFDBFE', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          <span style={{ fontFamily: F, fontSize: 13, fontWeight: 500, color: '#1D4ED8' }}>{selCnt} selected</span>
          <button style={{ fontFamily: F, fontSize: 12, color: '#DC2626', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>Delete selected</button>
        </div>
      )}

      {/* Table — flush, no padding */}
      <div className="sp-scroll" style={{ flex: 1, overflow: 'auto', background: '#fff' }}>
        <table style={{ width: '100%', minWidth: 600, borderCollapse: 'collapse', fontFamily: F }}>
          <thead>
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id} style={{ background: '#F9FAFB', borderBottom: '1px solid #E5E7EB' }}>
                {hg.headers.map(h => (
                  <th key={h.id} onClick={h.column.getToggleSortingHandler()}
                    style={{
                      width: h.column.columnDef.size,
                      padding: '10px 16px', textAlign: 'left',
                      fontSize: 12, fontWeight: 600, color: '#374151',
                      userSelect: 'none', cursor: h.column.getCanSort() ? 'pointer' : 'default',
                      whiteSpace: 'nowrap', letterSpacing: '0.01em',
                    }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {h.isPlaceholder ? null : flexRender(h.column.columnDef.header, h.getContext())}
                      {h.column.getCanSort() && (
                        <span style={{ color: h.column.getIsSorted() ? '#2563EB' : '#D1D5DB' }}>
                          {h.column.getIsSorted() === 'asc'
                            ? <svg width="9" height="9" viewBox="0 0 10 10" fill="none"><path d="M2 7l3-4 3 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                            : h.column.getIsSorted() === 'desc'
                            ? <svg width="9" height="9" viewBox="0 0 10 10" fill="none"><path d="M2 3l3 4 3-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                            : <svg width="9" height="9" viewBox="0 0 10 10" fill="none"><path d="M2 3.5l3-2.5 3 2.5M2 6.5l3 2.5 3-2.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                          }
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {isLoading && rows.length === 0 ? (
              <tr><td colSpan={colDefs.length} style={{ padding: '80px 0', textAlign: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
                  <Spinner size={20} />
                  <span style={{ fontFamily: F, fontSize: 13, color: '#9CA3AF' }}>Loading…</span>
                </div>
              </td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={colDefs.length} style={{ padding: '80px 0', textAlign: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" style={{ opacity: 0.2 }}><rect x="2" y="7" width="20" height="14" rx="2" stroke="#111827" strokeWidth="1.5"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" stroke="#111827" strokeWidth="1.5"/></svg>
                  <span style={{ fontFamily: F, fontSize: 14, color: '#9CA3AF', fontWeight: 500 }}>No suppliers found</span>
                  <button onClick={onNew} style={{ fontFamily: F, fontSize: 13, color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500, marginTop: 4 }}>Add your first supplier →</button>
                </div>
              </td></tr>
            ) : table.getRowModel().rows.map((row, i) => {
              const isSelected = row.getIsSelected()
              return (
                <tr key={row.id} className="sp-row" onClick={() => onEdit(row.original.id)}
                  style={{
                    background: isSelected ? '#EFF6FF' : '#fff',
                    borderBottom: '1px solid #F3F4F6', cursor: 'pointer',
                  }}>
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} style={{
                      padding: '12px 16px', verticalAlign: 'middle',
                      maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer / Pagination */}
      <div style={{ flexShrink: 0, background: '#fff', borderTop: '1px solid #E5E7EB', padding: '10px 28px', display: 'flex', alignItems: 'center', justifyContents: 'space-between' }}>
        {/* Left: per page + count */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontFamily: F, fontSize: 13, color: '#6B7280' }}>
          <span>Items per page:</span>
          <Dropdown
            trigger={open => (
              <button style={{ display: 'flex', alignItems: 'center', gap: 4, fontFamily: F, fontSize: 13, fontWeight: 500, color: '#374151', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 0' }}>
                {perPage} <ChevronIcon dir={open ? 'up' : 'down'} size={9} />
              </button>
            )}
            menuStyle={{ bottom: 'calc(100% + 4px)', top: 'auto', minWidth: 80 }}
          >
            {close => PER_PAGE_OPTIONS.map(n => (
              <div key={n} className={`sp-dropdown-item ${perPage === n ? 'active' : ''}`}
                onClick={() => { setPerPage(n); setPage(1); close() }}>
                {n}
              </div>
            ))}
          </Dropdown>
          <span style={{ color: '#D1D5DB' }}>·</span>
          <span>{rows.length > 0 ? `${(page - 1) * perPage + 1} – ${Math.min(page * perPage, total)} of ${total.toLocaleString()} items` : `${total.toLocaleString()} items`}</span>
        </div>

        {/* Right: page nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="sp-btn"
            style={{ width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContents: 'center', background: '#fff', border: '1px solid #E5E7EB', borderRadius: 5, cursor: page === 1 ? 'default' : 'pointer', color: page === 1 ? '#D1D5DB' : '#374151' }}>
            <ChevronIcon dir="left" size={10} color={page === 1 ? '#D1D5DB' : '#374151'} />
          </button>

          {/* Page number pills */}
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
            const pg = totalPages <= 5 ? i + 1 : page <= 3 ? i + 1 : page >= totalPages - 2 ? totalPages - 4 + i : page - 2 + i
            return (
              <button key={pg} onClick={() => setPage(pg)} className="sp-btn"
                style={{
                  width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContents: 'center',
                  fontFamily: F, fontSize: 12, fontWeight: pg === page ? 600 : 400,
                  background: pg === page ? '#2563EB' : '#fff',
                  color: pg === page ? '#fff' : '#374151',
                  border: '1px solid ' + (pg === page ? '#2563EB' : '#E5E7EB'),
                  borderRadius: 5, cursor: 'pointer',
                }}>
                {pg}
              </button>
            )
          })}

          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="sp-btn"
            style={{ width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContents: 'center', background: '#fff', border: '1px solid #E5E7EB', borderRadius: 5, cursor: page >= totalPages ? 'default' : 'pointer', color: page >= totalPages ? '#D1D5DB' : '#374151' }}>
            <ChevronIcon dir="right" size={10} color={page >= totalPages ? '#D1D5DB' : '#374151'} />
          </button>

          <span style={{ fontFamily: F, fontSize: 13, color: '#6B7280', marginLeft: 8 }}>
            {page} <span style={{ color: '#D1D5DB' }}>of</span> {totalPages} <span style={{ color: '#D1D5DB' }}>pages</span>
          </span>
        </div>
      </div>
    </div>
  )
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function SupplierPage() {
  const [view,      setView]     = useState('list')
  const [editId,    setEditId]   = useState(null)
  const [collapsed, setCollapsed] = useState(true)

  useEffect(() => { injectFont(); injectStyles() }, [])

  const goList = () => { setView('list'); setEditId(null) }
  const goNew  = () => { setView('new');  setEditId(null) }
  const goEdit = id => { setView('edit'); setEditId(id) }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#fff', fontFamily: F }}>
      {/* Left sidebar */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(v => !v)} />

      {/* Main content column */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        <TopBar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {view === 'list' && <SupplierList onEdit={goEdit} onNew={goNew} />}
          {(view === 'new' || view === 'edit') && <SupplierForm id={view === 'edit' ? editId : null} onDone={goList} />}
        </div>
      </div>
    </div>
  )
}
