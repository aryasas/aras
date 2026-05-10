import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from '@tanstack/react-form'
import {
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  flexRender,
} from '@tanstack/react-table'
import { api, apiFetch } from '../lib/api'

// ── Components ────────────────────────────────────────────────────────────────

function Spinner({ size = 16, color = '#c9a568' }) {
  return (
    <div 
      className="animate-spin rounded-md border-2 border-t-transparent"
      style={{ width: size, height: size, borderColor: `${color} transparent ${color} ${color}` }}
    />
  )
}

function Section({ title, idx, children }) {
  return (
    <div className="p-8 md:p-10 bg-white first:rounded-t-md last:rounded-b-md">
      <div className="flex items-center gap-4 mb-8">
        <span className="text-[16px] font-studio-serif font-bold text-[#0f1b2d]">{title}</span>
        <div className="h-px flex-1 bg-[#eef0f2]"></div>
        <span className="text-[9px] font-mono text-[#9aacb8]">0{idx}</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-10 gap-y-6">
        {children}
      </div>
    </div>
  )
}

function Field({ label, required, children, error, span = 1 }) {
  const colSpan = span === 2 ? 'md:col-span-2' : span === 3 ? 'md:col-span-3' : ''
  return (
    <div className={colSpan}>
      <div className="flex items-center justify-between mb-2">
        <label className="text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em]">
          {label}
          {required && <span className="text-[#6b2c2c] ml-1">*</span>}
        </label>
        {error && (
          <span className="text-[#6b2c2c] text-[9px] font-bold uppercase tracking-widest animate-pulse">
            {error}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

// ── Customer Form ─────────────────────────────────────────────────────────────

function CustomerForm({ id, onDone }) {
  const qc = useQueryClient()
  const isNew = !id
  const [isDirty, setIsDirty] = useState(false)

  // Fetch choices for dropdowns
  const { data: groups } = useQuery({ queryKey: ['erp', 'crm/customer-group', 'list'], queryFn: () => api.list('erp', 'crm/customer-group', { per_page: 100 }) })
  const { data: currencies } = useQuery({ queryKey: ['erp', 'currency', 'list'], queryFn: () => api.list('erp', 'currency', { per_page: 100 }) })

  const { data: obj, isLoading } = useQuery({
    queryKey: ['erp', 'crm/customer', id],
    queryFn: () => api.get('erp', 'crm/customer', id),
    enabled: !isNew,
  })

  const save = useMutation({
    mutationFn: data => isNew 
      ? api.create('erp', 'crm/customer', data) 
      : api.update('erp', 'crm/customer', id, data),
    onSuccess: () => { qc.invalidateQueries(['erp', 'crm/customer']); onDone() },
  })

  const form = useForm({
    defaultValues: {},
    onSubmit: async ({ value }) => save.mutate(value),
    onValuesChange: () => setIsDirty(true),
  })

  useEffect(() => {
    if (obj) {
      form.reset(obj)
      setIsDirty(false)
    }
  }, [obj])

  if (isLoading) return (
    <div className="flex-1 flex flex-col items-center justify-center bg-[#faf8f3]">
      <Spinner size={32} />
      <span className="mt-4 text-[12px] font-studio-serif italic text-[#9aacb8]">Opening Client Registry…</span>
    </div>
  )

  const inputClass = (hasError) => `w-full bg-[#fcfcfb] border ${hasError ? 'border-[#6b2c2c]' : 'border-[#dde3e7]'} rounded-md px-4 py-2.5 text-[14px] text-[#0f1b2d] font-studio-sans focus:outline-none focus:border-[#c9a568] focus:ring-1 focus:ring-[#c9a568] transition-all shadow-inner aras-engraved`
  const selectClass = (hasError) => `w-full bg-[#fcfcfb] border ${hasError ? 'border-[#6b2c2c]' : 'border-[#dde3e7]'} rounded-md px-4 py-2.5 text-[14px] text-[#0f1b2d] font-studio-sans focus:outline-none focus:border-[#c9a568] focus:ring-1 focus:ring-[#c9a568] transition-all shadow-inner aras-engraved appearance-none`

  return (
    <div className="flex-1 flex flex-col bg-[#faf8f3] overflow-hidden animate-fade-in pb-24">
      {/* HEADER */}
      <div className="bg-white border-b border-[#dde3e7] px-8 py-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button 
            onClick={onDone}
            className="p-2 hover:bg-[#faf8f3] rounded-md text-[#9aacb8] hover:text-[#0f1b2d] transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <div className="flex flex-col">
            <span className="text-[9px] font-bold text-[#c9a568] uppercase tracking-[0.2em] mb-1">
              Customer Profile {id ? `№ ${id}` : '· New Draft'}
            </span>
            <h2 className="font-studio-serif text-[22px] font-bold text-[#0f1b2d] leading-none">
              {isNew ? 'Register New Client' : (obj?.name || 'Client Record')}
            </h2>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {isDirty && (
            <span className="text-[10px] font-bold text-[#6b2c2c] bg-[#fdf2f2] px-3 py-1.5 rounded-md uppercase tracking-wider border border-[#fecaca]">
              Pending Changes
            </span>
          )}
          {!isNew && (
            <div className="flex items-center gap-4">
               <div className="flex flex-col items-end">
                  <span className="text-[9px] font-bold text-[#9aacb8] uppercase">Group</span>
                  <span className="text-[11px] font-bold text-[#0f1b2d]">{obj?.group?.name || 'General'}</span>
               </div>
               <div className="w-px h-8 bg-[#dde3e7]"></div>
               <span className="text-[10px] font-bold text-[#9aacb8] bg-[#f4f2ee] px-3 py-1.5 rounded-md uppercase tracking-wider">
                Official Registry
              </span>
            </div>
          )}
        </div>
      </div>

      {/* FORM BODY */}
      <div className="flex-1 overflow-y-auto p-8 lg:p-12">
        <div className="max-w-5xl mx-auto">
          <form onSubmit={e => { e.preventDefault(); form.handleSubmit() }} className="space-y-8">
            <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl divide-y divide-[#eef0f2] overflow-hidden">
              
              <Section title="Identity & Classification" idx={1}>
                <form.Field name="code" children={f => (
                  <Field label="Customer Code" required error={f.state.meta.errors[0]}>
                    <input className={inputClass(f.state.meta.errors.length > 0)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="CUST-0000" />
                  </Field>
                )} />
                <form.Field name="name" children={f => (
                  <Field label="Client / Company Name" required error={f.state.meta.errors[0]} span={2}>
                    <input className={inputClass(f.state.meta.errors.length > 0)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="Full legal name" />
                  </Field>
                )} />
                <form.Field name="group_id" children={f => (
                  <Field label="Customer Group">
                    <div className="relative">
                      <select className={selectClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)}>
                        <option value="">— Select Group —</option>
                        {groups?.data?.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                      </select>
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[#9aacb8]">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
                      </div>
                    </div>
                  </Field>
                )} />
                <form.Field name="tax_id" children={f => (
                  <Field label="VAT / Tax Identification">
                    <input className={inputClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="Tax ID" />
                  </Field>
                )} />
                <form.Field name="segment" children={f => (
                  <Field label="Market Segment">
                    <input className={inputClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="e.g. Enterprise, SME" />
                  </Field>
                )} />
              </Section>

              <Section title="Contact & Communications" idx={2}>
                <form.Field name="email" children={f => (
                  <Field label="Official Email">
                    <input className={inputClass(false)} type="email" value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="client@company.com" />
                  </Field>
                )} />
                <form.Field name="phone" children={f => (
                  <Field label="Landline">
                    <input className={inputClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="+1 ..." />
                  </Field>
                )} />
                <form.Field name="mobile" children={f => (
                  <Field label="Mobile / WhatsApp">
                    <input className={inputClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="+1 ..." />
                  </Field>
                )} />
              </Section>

              <Section title="Geographic Coordinates" idx={3}>
                <form.Field name="address" children={f => (
                  <Field label="Billing / Primary Address" span={3}>
                    <textarea className={inputClass(false)} rows={3} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="Street, Building, Suite..." />
                  </Field>
                )} />
                <form.Field name="city" children={f => (
                  <Field label="City">
                    <input className={inputClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="City" />
                  </Field>
                )} />
                <form.Field name="country" children={f => (
                  <Field label="Country / Region">
                    <input className={inputClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="Country" />
                  </Field>
                )} />
              </Section>

              <Section title="Commercial Terms" idx={4}>
                 <form.Field name="currency_id" children={f => (
                  <Field label="Settlement Currency">
                    <div className="relative">
                      <select className={selectClass(false)} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)}>
                        <option value="">— Select Currency —</option>
                        {currencies?.data?.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
                      </select>
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[#9aacb8]">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
                      </div>
                    </div>
                  </Field>
                )} />
                <form.Field name="credit_limit" children={f => (
                  <Field label="Credit Limit Allowance">
                    <input className={inputClass(false)} type="number" value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} />
                  </Field>
                )} />
                <form.Field name="payment_term_days" children={f => (
                  <Field label="Payment Terms (Days)">
                    <input className={inputClass(false)} type="number" value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} />
                  </Field>
                )} />
              </Section>

              <Section title="Internal Ledger Notes" idx={5}>
                 <form.Field name="notes" children={f => (
                  <Field label="Observations & Caveats" span={3}>
                    <textarea className={inputClass(false)} rows={4} value={f.state.value ?? ''} onBlur={f.handleBlur} onChange={e => f.handleChange(e.target.value)} placeholder="Internal remarks regarding client behavior or special agreements..." />
                  </Field>
                )} />
              </Section>

            </div>
          </form>
        </div>
      </div>

      {/* FOOTER ACTIONS */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-md border-t border-[#dde3e7] p-6 z-40 flex justify-center">
        <div className="max-w-5xl w-full flex items-center justify-between px-4">
          <button 
            onClick={onDone}
            className="text-[11px] font-bold text-[#9aacb8] hover:text-[#6b2c2c] uppercase tracking-widest transition-colors"
          >
            Cancel Draft
          </button>
          
          <form.Subscribe selector={s => [s.canSubmit, s.isSubmitting]}>
            {([can, submitting]) => (
              <button 
                onClick={() => form.handleSubmit()}
                disabled={!can || submitting || save.isPending}
                className="flex items-center gap-3 px-12 py-4 bg-[#6b2c2c] text-white text-[12px] font-bold rounded-md shadow-2xl hover:bg-[#4d1e1e] transition-all active:scale-95 disabled:opacity-30 shadow-[#6b2c2c]/30"
              >
                {(submitting || save.isPending) ? <Spinner size={14} color="#fff" /> : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" /></svg>
                )}
                <span className="uppercase tracking-[0.2em]">{isNew ? 'Commit to Registry' : 'Update Client Folio'}</span>
              </button>
            )}
          </form.Subscribe>
        </div>
      </div>
    </div>
  )
}

// ── Customer List ─────────────────────────────────────────────────────────────

function CustomerList({ onEdit, onNew }) {
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const qc = useQueryClient()

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['erp', 'crm/customer', page, q],
    queryFn: () => api.list('erp', 'crm/customer', { page, q: q || undefined, per_page: 25 }),
  })

  const rows = data?.data ?? []
  const total = data?.meta?.total ?? rows.length

  const columns = useMemo(() => [
    { accessorKey: 'code', header: 'Ref №', cell: i => <span className="font-mono text-[11px] font-bold bg-[#f4f2ee] px-2 py-1 rounded-md">{i.getValue()}</span> },
    { accessorKey: 'name', header: 'Client Name', cell: i => <span className="font-bold text-[#0f1b2d]">{i.getValue()}</span> },
    { accessorKey: 'group.name', header: 'Group', cell: i => <span className="text-[11px] font-bold text-[#c9a568] uppercase tracking-wider">{i.getValue() || 'General'}</span> },
    { accessorKey: 'email', header: 'Email' },
    { accessorKey: 'city', header: 'Location', cell: i => <span>{i.row.original.city}{i.row.original.country ? `, ${i.row.original.country}` : ''}</span> },
  ], [])

  const table = useReactTable({
    data: rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="flex-1 flex flex-col bg-white overflow-hidden animate-fade-in">
      {/* TOOLBAR */}
      <div className="p-10 pb-6 flex items-end justify-between gap-6 border-b border-[#f4f2ee]">
        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-bold text-[#c9a568] uppercase tracking-[0.3em]">CRM Module</span>
          <h1 className="font-studio-serif text-[36px] font-bold text-[#0f1b2d] tracking-tight leading-none">Customer Registry</h1>
          <p className="text-[14px] text-[#9aacb8] font-studio-serif italic mt-1">Global directory of verified clients and commercial partners.</p>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="relative">
             <input 
               type="text" 
               className="bg-[#faf8f3] border border-[#dde3e7] rounded-md pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-[#c9a568] transition-all w-80 shadow-inner aras-engraved"
               placeholder="Search registry by name or code..."
               value={q}
               onChange={e => { setQ(e.target.value); setPage(1) }}
             />
             <svg className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#9aacb8]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          </div>
          <button 
            onClick={onNew}
            className="px-8 py-3.5 bg-[#6b2c2c] text-white rounded-md text-[12px] font-bold uppercase tracking-[0.2em] hover:bg-[#4d1e1e] transition-all shadow-2xl active:scale-95 shadow-[#6b2c2c]/30"
          >
            New Client
          </button>
        </div>
      </div>

      {/* TABLE */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-[14px] font-studio-sans">
          <thead className="sticky top-0 bg-[#faf8f3] border-b border-[#dde3e7] text-[#9aacb8] uppercase text-[10px] font-bold tracking-[0.2em] z-10">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => (
                  <th key={h.id} className="px-10 py-5">{flexRender(h.column.columnDef.header, h.getContext())}</th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-[#f4f2ee]">
            {isLoading ? (
              <tr><td colSpan={columns.length} className="px-10 py-32 text-center"><Spinner size={32} /></td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={columns.length} className="px-10 py-32 text-center text-[#9aacb8] font-studio-serif italic text-lg">No clients matched the current filter criteria.</td></tr>
            ) : table.getRowModel().rows.map(row => (
              <tr 
                key={row.id} 
                className="hover:bg-[#faf8f3] cursor-pointer transition-colors group"
                onClick={() => onEdit(row.original.id)}
              >
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-10 py-5 text-[#313b3d]">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* FOOTER */}
      <div className="p-6 bg-[#faf8f3] border-t border-[#dde3e7] flex items-center justify-between text-[11px] font-bold text-[#9aacb8] uppercase tracking-widest">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          <span>Sync Active · {total} Client Records</span>
        </div>
        <div className="flex items-center gap-6">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="hover:text-[#6b2c2c] disabled:opacity-20 transition-colors">Previous Page</button>
          <div className="px-3 py-1 bg-white border border-[#dde3e7] rounded-md text-[#0f1b2d]">Folio {page}</div>
          <button disabled={rows.length < 25} onClick={() => setPage(p => p + 1)} className="hover:text-[#6b2c2c] disabled:opacity-20 transition-colors">Next Page</button>
        </div>
      </div>
    </div>
  )
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function CustomerPage({ initialView = 'list', initialId = null }) {
  const [view, setView] = useState(initialView)
  const [editId, setEditId] = useState(initialId)

  useEffect(() => {
    if (initialView) setView(initialView)
    if (initialId) setEditId(initialId)
  }, [initialView, initialId])

  const goList = () => { setView('list'); setEditId(null) }
  const goNew  = () => { setView('new');  setEditId(null) }
  const goEdit = id => { setView('edit'); setEditId(id) }

  return (
    <div className="flex h-screen bg-white text-[#0f1b2d] selection:bg-[#c9a568]/30">
      <div className="flex-1 flex flex-col min-w-0">
        {view === 'list' && <CustomerList onEdit={goEdit} onNew={goNew} />}
        {(view === 'new' || view === 'edit') && <CustomerForm id={view === 'edit' ? editId : null} onDone={goList} />}
      </div>
    </div>
  )
}
