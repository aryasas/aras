import React, { useState } from 'react'
import { api } from '../lib/api'

export default function AppSettingsPage(config) {
  const { 
    appSlug, appTitle, cards, 
    section, sectionLabel, sectionIcon, 
    settings = [], isDynamic, isGeneral, 
    valueTypes, settingsHome, appRow 
  } = config

  // If no section is provided, we are on the Home (grid) view
  if (!section) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map((card, i) => (
            <a 
              key={i} 
              href={card.url}
              className="group block bg-white border border-aras-primary/10 p-6 hover:border-aras-accent hover:shadow-xl transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 flex items-center justify-center text-2xl ${card.framework ? 'text-aras-accent' : 'text-aras-primary/40 group-hover:text-aras-accent'} transition-colors`}>
                  <i className={`fa ${card.icon}`}></i>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-studio-serif font-bold text-aras-primary">{card.label}</h3>
                    {card.framework && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-aras-accent/10 text-aras-accent font-bold uppercase tracking-wider">Framework</span>
                    )}
                  </div>
                  <p className="text-xs text-aras-primary/50 leading-relaxed line-clamp-2">
                    {card.description || `Configure ${card.label} settings for ${appTitle}.`}
                  </p>
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>
    )
  }

  // Section View
  return (
    <div className="flex flex-col lg:flex-row gap-8">
      <div className="flex-1 space-y-6">
        <div className="bg-white border border-aras-primary/10 overflow-hidden">
          <div className="p-6 border-b border-aras-primary/5 flex items-center justify-between bg-aras-primary/[0.02]">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 flex items-center justify-center text-xl text-aras-accent bg-white shadow-sm border border-aras-primary/5">
                <i className={`fa ${sectionIcon}`}></i>
              </div>
              <div>
                <h2 className="font-studio-serif font-bold text-aras-primary">{sectionLabel}</h2>
                <div className="text-[10px] text-aras-primary/40 flex items-center gap-1 uppercase tracking-wider font-bold">
                  <a href={`/admin/${appSlug}/`} className="hover:text-aras-accent">{appTitle}</a>
                  <i className="fa fa-angle-right"></i>
                  <a href={settingsHome} className="hover:text-aras-accent">Settings</a>
                  <i className="fa fa-angle-right"></i>
                  <span>{sectionLabel}</span>
                </div>
              </div>
            </div>
            <a href={settingsHome} className="px-4 py-2 text-xs font-bold border border-aras-primary/10 hover:bg-aras-primary/5 transition-colors flex items-center gap-2">
              <i className="fa fa-arrow-left"></i> Back
            </a>
          </div>

          <div className="p-8">
            <form method="POST" action="">
              <input type="hidden" name="csrf_token" value={config.csrf_token} />
              <input type="hidden" name="_action" value="save" />

              {isGeneral ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                    <label className="text-xs font-bold text-aras-primary/60 uppercase tracking-wider">App Title</label>
                    <div className="md:col-span-2">
                      <input 
                        type="text" 
                        name="app_title" 
                        defaultValue={appRow.title}
                        className="w-full bg-aras-primary/5 border border-aras-primary/10 px-4 py-2 text-sm focus:outline-none focus:border-aras-accent"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                    <label className="text-xs font-bold text-aras-primary/60 uppercase tracking-wider">
                      Icon
                      <span className="block text-[10px] font-normal normal-case opacity-60">FontAwesome class</span>
                    </label>
                    <div className="md:col-span-2">
                      <div className="flex gap-2">
                        <div className="w-10 h-10 flex items-center justify-center bg-aras-primary/5 border border-aras-primary/10">
                          <i className={`fa ${appRow.icon || 'fa-cubes'}`}></i>
                        </div>
                        <input 
                          type="text" 
                          name="app_icon" 
                          defaultValue={appRow.icon}
                          placeholder="fa-cubes"
                          className="flex-1 bg-aras-primary/5 border border-aras-primary/10 px-4 py-2 text-sm focus:outline-none focus:border-aras-accent"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <label className="text-xs font-bold text-aras-primary/60 uppercase tracking-wider pt-2">Description</label>
                    <div className="md:col-span-2">
                      <textarea 
                        name="app_description" 
                        defaultValue={appRow.description}
                        rows="3"
                        className="w-full bg-aras-primary/5 border border-aras-primary/10 px-4 py-2 text-sm focus:outline-none focus:border-aras-accent"
                      ></textarea>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                    <label className="text-xs font-bold text-aras-primary/60 uppercase tracking-wider">
                      Menu Order
                      <span className="block text-[10px] font-normal normal-case opacity-60">Lower = first</span>
                    </label>
                    <div className="md:col-span-2">
                      <input 
                        type="number" 
                        name="app_menu_order" 
                        defaultValue={appRow.menu_order}
                        className="w-24 bg-aras-primary/5 border border-aras-primary/10 px-4 py-2 text-sm focus:outline-none focus:border-aras-accent"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                    <label className="text-xs font-bold text-aras-primary/60 uppercase tracking-wider">Status</label>
                    <div className="md:col-span-2 flex items-center gap-3">
                      <span className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${appRow.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {appRow.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <span className="text-[10px] text-aras-primary/40 italic">
                        Manage via <a href="/admin/settings#panel-apps" className="underline hover:text-aras-accent">App Manager</a>
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-8">
                  {settings.length > 0 ? (
                    settings.map((s, i) => (
                      <div key={i} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="pt-1">
                          <label className="text-xs font-bold text-aras-primary uppercase tracking-wider mb-0.5 block" htmlFor={`setting_${s.key}`}>
                            {s.label || s.key}
                          </label>
                          <div className="flex items-center gap-2 opacity-40">
                            <code className="text-[10px] bg-aras-primary/10 px-1 rounded">{s.key}</code>
                            <span className="text-[10px] uppercase font-bold tracking-tighter">{s.value_type}</span>
                          </div>
                          {s.help_text && (
                            <p className="mt-2 text-[11px] text-aras-primary/60 leading-relaxed italic border-l-2 border-aras-primary/10 pl-2">
                              {s.help_text}
                            </p>
                          )}
                        </div>
                        <div className="md:col-span-2">
                          {s.value_type === 'boolean' ? (
                            <label className="inline-flex items-center gap-3 cursor-pointer group pt-1">
                              <div className="relative">
                                <input 
                                  type="checkbox" 
                                  id={`setting_${s.key}`} 
                                  name={`setting_${s.key}`} 
                                  value="true" 
                                  defaultChecked={s.value === true || s.value === 'true'}
                                  className="sr-only peer"
                                />
                                <div className="w-10 h-5 bg-aras-primary/10 peer-focus:ring-2 peer-focus:ring-aras-accent/20 rounded-none transition-all duration-300 peer-checked:bg-aras-accent"></div>
                                <div className="absolute left-1 top-1 bg-white w-3 h-3 transition-all duration-300 peer-checked:translate-x-5"></div>
                              </div>
                              <span className="text-xs font-bold text-aras-primary/40 group-hover:text-aras-primary transition-colors uppercase tracking-wider">Enabled</span>
                            </label>
                          ) : s.value_type === 'text' || s.value_type === 'json' ? (
                            <textarea 
                              id={`setting_${s.key}`} 
                              name={`setting_${s.key}`} 
                              defaultValue={s.value}
                              rows="4"
                              className="w-full bg-aras-primary/5 border border-aras-primary/10 px-4 py-3 text-sm focus:outline-none focus:border-aras-accent font-mono"
                            ></textarea>
                          ) : (
                            <input 
                              type={s.value_type === 'integer' || s.value_type === 'float' ? 'number' : 'text'}
                              step={s.value_type === 'float' ? 'any' : undefined}
                              id={`setting_${s.key}`} 
                              name={`setting_${s.key}`} 
                              defaultValue={s.value}
                              className="w-full bg-aras-primary/5 border border-aras-primary/10 px-4 py-2 text-sm focus:outline-none focus:border-aras-accent"
                            />
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="py-12 text-center">
                      <i className="fa fa-info-circle text-2xl text-aras-primary/20 mb-3"></i>
                      <p className="text-sm text-aras-primary/40 italic">No settings defined for this section.</p>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-12 pt-8 border-t border-aras-primary/5 flex justify-end">
                <button type="submit" className="px-8 py-3 bg-aras-primary text-white text-xs font-bold uppercase tracking-[0.2em] hover:bg-aras-accent transition-all duration-300 flex items-center gap-3">
                  <i className="fa fa-save"></i> Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>

        {isDynamic && settings.length > 0 && (
          <div className="bg-white border border-aras-primary/10">
            <div className="p-6 border-b border-aras-primary/5 bg-aras-primary/[0.02]">
              <h3 className="font-studio-serif font-bold text-aras-primary text-sm">Manage Custom Settings</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-aras-primary/5 text-aras-primary/40 uppercase tracking-wider font-bold">
                    <th className="px-6 py-4">Key</th>
                    <th className="px-6 py-4">Type</th>
                    <th className="px-6 py-4">Value</th>
                    <th className="px-6 py-4 w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-aras-primary/5">
                  {settings.map((s, i) => (
                    <tr key={i} className="hover:bg-aras-primary/[0.01] transition-colors">
                      <td className="px-6 py-4 font-mono text-aras-accent">{s.key}</td>
                      <td className="px-6 py-4 opacity-60 uppercase font-bold tracking-tighter">{s.value_type}</td>
                      <td className="px-6 py-4">
                        <span className="line-clamp-1 opacity-40 italic">{String(s.value || '—')}</span>
                      </td>
                      <td className="px-6 py-4">
                        <form method="POST" action="" onSubmit={(e) => { if (!confirm(`Delete ${s.key}?`)) e.preventDefault(); }}>
                          <input type="hidden" name="csrf_token" value={config.csrf_token} />
                          <input type="hidden" name="_action" value="delete" />
                          <input type="hidden" name="delete_key" value={s.key} />
                          <button type="submit" className="text-red-400 hover:text-red-600 transition-colors">
                            <i className="fa fa-trash"></i>
                          </button>
                        </form>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {isDynamic && (
        <aside className="w-full lg:w-80 space-y-6">
          <div className="bg-white border border-aras-primary/10 p-6 sticky top-8">
            <h3 className="font-studio-serif font-bold text-aras-primary mb-4 flex items-center gap-2">
              <i className="fa fa-plus-circle text-aras-accent"></i>
              Add Custom Setting
            </h3>
            <form method="POST" action="" className="space-y-4">
              <input type="hidden" name="csrf_token" value={config.csrf_token} />
              <input type="hidden" name="_action" value="add" />
              
              <div>
                <label className="text-[10px] font-bold text-aras-primary/40 uppercase tracking-wider block mb-1">Key</label>
                <input 
                  type="text" 
                  name="new_key" 
                  required 
                  placeholder="e.g. retention_days"
                  className="w-full bg-aras-primary/5 border border-aras-primary/10 px-3 py-2 text-xs focus:outline-none focus:border-aras-accent"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-aras-primary/40 uppercase tracking-wider block mb-1">Label</label>
                <input 
                  type="text" 
                  name="new_label" 
                  placeholder="Display Label"
                  className="w-full bg-aras-primary/5 border border-aras-primary/10 px-3 py-2 text-xs focus:outline-none focus:border-aras-accent"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-aras-primary/40 uppercase tracking-wider block mb-1">Type</label>
                <select 
                  name="new_type"
                  className="w-full bg-aras-primary/5 border border-aras-primary/10 px-3 py-2 text-xs focus:outline-none focus:border-aras-accent appearance-none cursor-pointer"
                >
                  {valueTypes.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              <button type="submit" className="w-full py-2 bg-aras-accent/10 text-aras-accent text-[10px] font-bold uppercase tracking-wider hover:bg-aras-accent hover:text-white transition-all duration-300">
                Add Setting
              </button>
            </form>
          </div>
        </aside>
      )}
    </div>
  )
}
