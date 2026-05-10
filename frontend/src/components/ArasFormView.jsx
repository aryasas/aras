import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useForm } from '@tanstack/react-form'
import { useEffect, useState, useMemo } from 'react'
import ArasChildTable from './ArasChildTable'
import ArasSearchableSelect from './ArasSearchableSelect'

/**
 * ArasFormView - Definitive "Studio Ledger" Form Editor.
 * Features: Multi-section layout, Engraved inputs, Sticky actions, and Child Table integration.
 */
export default function ArasFormView({ app, resource, id, fields = [], childTables = [], redirectOnSave }) {
  const qc = useQueryClient()
  const isNew = !id
  const [isDirty, setIsDirty] = useState(false)

  // Fetch resource metadata if fields or childTables are missing
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['resource-config', resource],
    queryFn: () => api.resourceConfig(resource),
    enabled: !fields?.length || !childTables?.length,
  })

  const activeFields = fields?.length > 0 ? fields : (config?.fields || [])
  const childTableDefs = childTables?.length > 0 ? childTables : (config?.child_tables || [])

  // Normalize fields into sections if they aren't already
  const sections = useMemo(() => {
    if (activeFields.length > 0 && activeFields[0].fields) {
      return activeFields // Already sectioned
    }
    
    // Group by section attribute if available, else put in general
    const grouped = {}
    activeFields.forEach(f => {
      const s = f.section || 'General Information'
      if (!grouped[s]) grouped[s] = []
      grouped[s].push(f)
    })

    return Object.entries(grouped).map(([label, fs]) => ({
      id: label.toLowerCase().replace(/\s+/g, '-'),
      label,
      fields: fs
    }))
  }, [activeFields])

  const { data: obj, isLoading } = useQuery({
    queryKey: [app, resource, id],
    queryFn: () => api.get(app, resource, id),
    enabled: !isNew,
  })

  const save = useMutation({
    mutationFn: data => isNew
      ? api.create(app, resource, data)
      : api.update(app, resource, id, data),
    onSuccess: () => {
      qc.invalidateQueries([app, resource])
      const dest = redirectOnSave ?? `/admin/${app}/${resource}/`
      window.location.href = dest
    },
  })

  const form = useForm({
    defaultValues: {},
    onSubmit: async ({ value }) => {
      save.mutate(value)
    },
    onValuesChange: () => setIsDirty(true),
  })

  useEffect(() => {
    if (obj) {
      form.reset(obj)
      setIsDirty(false)
    }
  }, [obj, form])

  if (isLoading || configLoading) return (
    <div className="flex flex-col items-center justify-center p-32 bg-[#faf8f3] min-h-screen">
      <div className="w-12 h-12 border-4 border-[#c9a568] border-t-transparent rounded-md animate-spin"></div>
      <span className="mt-4 text-[13px] font-studio-serif italic text-[#9aacb8]">Retrieving Ledger…</span>
    </div>
  )

  const resourceTitle = resource.split('/').pop().replace(/-/g, ' ').replace(/_/g, ' ')
  const formattedTitle = resourceTitle.charAt(0).toUpperCase() + resourceTitle.slice(1)

  return (
    <div className="min-h-screen bg-[#faf8f3] pb-32 animate-fade-in">
      <div className="max-w-5xl mx-auto px-4 sm:px-8 pt-8">
        
        {/* BREADCRUMB / NAV */}
        <div className="mb-6 flex items-center gap-2 text-[11px] font-bold text-[#9aacb8] uppercase tracking-widest">
          <a href="/admin/" className="hover:text-[#0f1b2d] transition-colors">Aras</a>
          <span>/</span>
          <a href={`/admin/${app}/`} className="hover:text-[#0f1b2d] transition-colors">{app}</a>
          <span>/</span>
          <a href={`/admin/${app}/${resource}/`} className="hover:text-[#0f1b2d] transition-colors">{formattedTitle}</a>
        </div>

        <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl overflow-hidden animate-slide-up">
          {/* TOP ACCENT */}
          <div className="h-1.5 w-full bg-[#6b2c2c]"></div>

          {/* HEADER */}
          <div className="bg-[#faf8f3] border-b border-[#dde3e7] px-8 py-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="flex flex-col">
              <span className="text-[10px] font-mono font-bold text-[#c9a568] uppercase tracking-[0.3em] mb-2">
                {isNew ? 'New Entry Request' : `Official Record · ID ${id}`}
              </span>
              <h1 className="font-studio-serif text-[32px] font-bold text-[#0f1b2d] leading-none tracking-tight">
                {isNew ? 'Drafting' : 'Reviewing'} {formattedTitle}
              </h1>
            </div>
            
            <div className="flex items-center gap-3">
              {!isNew && (
                <div className="px-4 py-2 bg-white border border-[#dde3e7] rounded-md shadow-sm flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                  <span className="text-[11px] font-bold text-[#0f1b2d] uppercase tracking-wider">Live System Record</span>
                </div>
              )}
              {isDirty && (
                <div className="px-4 py-2 bg-[#fdf2f2] border border-[#fecaca] rounded-md shadow-sm flex items-center gap-3">
                  <span className="text-[11px] font-bold text-[#6b2c2c] uppercase tracking-wider">Unsaved Changes</span>
                </div>
              )}
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              e.stopPropagation()
              form.handleSubmit()
            }}
            className="divide-y divide-[#eef0f2]"
          >
            {save.isError && (
              <div className="m-8 bg-[#fdf2f2] border border-[#fecaca] p-4 rounded-md text-[#6b2c2c] text-sm flex items-start gap-3">
                <svg className="w-5 h-5 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/></svg>
                <div>
                  <p className="font-bold uppercase tracking-wider text-[11px]">System Validation Error</p>
                  <p className="mt-1 opacity-90">{save.error.message}</p>
                </div>
              </div>
            )}

            {/* SECTIONS & FIELDS */}
            {sections.map((section, idx) => (
              <div key={section.id} className="p-8 md:p-12">
                <div className="flex items-center gap-4 mb-10">
                  <span className="text-[18px] font-studio-serif font-bold text-[#0f1b2d]">{section.label}</span>
                  <div className="h-px flex-1 bg-[#eef0f2]"></div>
                  <span className="text-[10px] font-mono text-[#9aacb8]">0{idx + 1}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-12 gap-y-8">
                  {section.fields.map(field => (
                    <form.Field
                      key={field.name}
                      name={field.name}
                      validators={{
                        onChange: ({ value }) => {
                          if (field.required && !value) return 'Mandatory'
                          return undefined
                        }
                      }}
                      children={(fieldApi) => {
                        const hasError = fieldApi.state.meta.errors.length > 0
                        const isWide = field.type === 'textarea' || field.span === 2 || field.span === 3
                        const colSpan = field.span === 2 ? 'md:col-span-2' : field.span === 3 ? 'md:col-span-3' : field.type === 'textarea' ? 'md:col-span-2 lg:col-span-3' : ''

                        return (
                          <div className={colSpan}>
                            <div className="flex items-center justify-between mb-2.5">
                              <label className="text-[10px] font-bold text-[#9aacb8] uppercase tracking-[0.2em]">
                                {field.label ?? field.name}
                                {field.required && <span className="text-[#6b2c2c] ml-1">*</span>}
                              </label>
                              {hasError && (
                                <span className="text-[#6b2c2c] text-[9px] font-bold uppercase tracking-widest animate-pulse">
                                  {fieldApi.state.meta.errors[0]}
                                </span>
                              )}
                            </div>

                            {field.type === 'textarea' || field.widget === 'textarea' ? (
                              <textarea
                                id={fieldApi.name}
                                value={fieldApi.state.value ?? ''}
                                onBlur={fieldApi.handleBlur}
                                onChange={(e) => fieldApi.handleChange(e.target.value)}
                                rows={4}
                                className={`w-full bg-[#fcfcfb] border ${hasError ? 'border-[#6b2c2c]' : 'border-[#dde3e7]'} rounded-md px-4 py-3 text-[14px] text-[#0f1b2d] font-studio-sans focus:outline-none focus:border-[#c9a568] focus:ring-1 focus:ring-[#c9a568] transition-all resize-none shadow-inner aras-engraved`}
                                placeholder={`Provide ${field.label?.toLowerCase() ?? field.name}…`}
                              />
                            ) : field.type === 'select' || field.widget === 'select' || field.type === 'SelectField' || field.type === 'relation' ? (
                              <ArasSearchableSelect
                                value={fieldApi.state.value}
                                onChange={(val) => fieldApi.handleChange(val)}
                                options={field.choices ?? []}
                                addUrl={field.rel_add_url}
                                placeholder={`Choose ${field.label?.toLowerCase() ?? field.name}…`}
                                className="w-full"
                              />
                            ) : (
                              <input
                                id={fieldApi.name}
                                type={field.widget === 'datetime-local' ? 'datetime-local' : (field.type === 'Integer' || field.type === 'Decimal' ? 'number' : (field.widget ?? 'text'))}
                                value={fieldApi.state.value ?? ''}
                                onBlur={fieldApi.handleBlur}
                                onChange={(e) => fieldApi.handleChange(e.target.value)}
                                className={`w-full bg-[#fcfcfb] border ${hasError ? 'border-[#6b2c2c]' : 'border-[#dde3e7]'} rounded-md px-4 py-3 text-[14px] text-[#0f1b2d] font-studio-sans focus:outline-none focus:border-[#c9a568] focus:ring-1 focus:ring-[#c9a568] transition-all shadow-inner aras-engraved`}
                                placeholder={`Enter ${field.label?.toLowerCase() ?? field.name}…`}
                              />
                            )}
                          </div>
                        )
                      }}
                    />
                  ))}
                </div>
              </div>
            ))}

            {/* RELATIONS / CHILD TABLES (Always at the bottom) */}
            {childTableDefs.length > 0 && (
              <div className="p-8 md:p-12 bg-[#faf8f3] border-t border-[#dde3e7]">
                <div className="flex items-center gap-4 mb-10">
                  <span className="text-[18px] font-studio-serif font-bold text-[#0f1b2d]">Related Records</span>
                  <div className="h-px flex-1 bg-[#dde3e7]"></div>
                  <span className="text-[10px] font-mono text-[#9aacb8]">LEGGER SECTIONS</span>
                </div>

                <div className="space-y-16">
                  {childTableDefs.map(ct => (
                    <form.Field
                      key={ct.name}
                      name={ct.name}
                      children={(fieldApi) => (
                        <ArasChildTable 
                          title={ct.title}
                          columns={ct.columns}
                          data={fieldApi.state.value || []}
                          onChange={(val) => {
                            fieldApi.handleChange(val)
                            setIsDirty(true)
                          }}
                        />
                      )}
                    />
                  ))}
                </div>
              </div>
            )}
          </form>
        </div>

        {/* AUDIT NOTE */}
        <div className="mt-12 text-center">
          <p className="text-[11px] font-studio-serif italic text-[#9aacb8] max-w-lg mx-auto leading-relaxed">
            All modifications are recorded with timestamp and cryptographic signature in the Aras Immutable Ledger. Unauthorized alterations are strictly monitored.
          </p>
        </div>
      </div>

      {/* STICKY ACTION BAR */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-md border-t border-[#dde3e7] p-6 z-50 flex items-center justify-center shadow-[0_-10px_30px_rgba(0,0,0,0.05)]">
        <div className="max-w-5xl w-full flex items-center justify-between px-4 sm:px-8">
          <div className="hidden sm:flex flex-col">
            <span className="text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em]">Current Status</span>
            <span className="text-[11px] font-bold text-[#0f1b2d] uppercase tracking-wider">{isDirty ? 'Draft Modified' : 'Reviewing Original'}</span>
          </div>

          <div className="flex items-center gap-6">
            <a
              href={`/admin/${app}/${resource}/`}
              className="text-[12px] font-bold text-[#9aacb8] hover:text-[#6b2c2c] transition-colors uppercase tracking-[0.2em]"
            >
              Cancel
            </a>
            
            <form.Subscribe
              selector={(state) => [state.canSubmit, state.isSubmitting]}
              children={([canSubmit, isSubmitting]) => (
                <button
                  onClick={() => form.handleSubmit()}
                  disabled={!canSubmit || isSubmitting || save.isPending}
                  className="flex items-center gap-3 px-12 py-4 bg-[#6b2c2c] text-white text-[12px] font-bold rounded-md shadow-2xl hover:bg-[#4d1e1e] hover:-translate-y-0.5 focus:ring-4 focus:ring-[#c9a568]/20 transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed shadow-[#6b2c2c]/30"
                >
                  {isSubmitting || save.isPending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-md animate-spin"></div>
                      <span className="uppercase tracking-[0.2em]">Committing…</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="uppercase tracking-[0.2em]">{isNew ? 'Submit Ledger Entry' : 'Seal & Update Record'}</span>
                    </>
                  )}
                </button>
              )}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
