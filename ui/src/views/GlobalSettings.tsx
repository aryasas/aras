import { useState, useEffect } from 'react'
import { Globe, Save, RefreshCw, Coins, Languages, Calendar, Cpu, ShieldAlert, Database, Activity } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'
import Combobox from '../aras-core/components/Combobox'

interface Setting {
  id: number;
  key: string;
  value: string;
  description: string;
}

function GlobalSettings() {
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showAlert, showError } = useUIStore();

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await api.post('/sys_settings/query', { filters: [] });
      
      const settingsMap: Record<string, Setting> = {};
      response.data.items.forEach((s: Setting) => {
        settingsMap[s.key] = s;
      });
      setSettings(settingsMap);
    } catch (err) {
      showError('Error', 'Failed to load system settings.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleUpdate = (key: string, value: string) => {
    setSettings(prev => {
      const current = prev[key] || { key, value: '' };
      return {
        ...prev,
        [key]: { ...current, value }
      };
    });
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      // Filter out settings that don't have an ID (shouldn't happen with seeded data, but safe)
      const validSettings = Object.values(settings).filter(s => s.id);
      
      const promises = validSettings.map(s => 
        api.patch(`/sys_settings/${s.id}`, { value: s.value })
      );
      
      if (promises.length === 0) {
        showAlert('Info', 'No settings to update.');
        return;
      }

      await Promise.all(promises);
      showAlert('Success', 'Global settings updated successfully.');
    } catch (err) {
      showError('Error', 'Failed to save settings.');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
        <RefreshCw className="animate-spin mb-4" size={32} />
        <p>Loading global configuration...</p>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto pb-12">
      <div className="flex items-center justify-between mb-8 sticky top-0 bg-slate-50/80 backdrop-blur-md py-4 z-10 border-b border-slate-200/50">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Global Preferences</h1>
          <p className="text-slate-500 mt-1">Configure platform behavior, localization, and system constraints.</p>
        </div>
        <button 
          onClick={saveSettings}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200 disabled:opacity-50"
        >
          {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
          <span>{saving ? 'Saving...' : 'Save Changes'}</span>
        </button>
      </div>

      <div className="space-y-6">
        
        {/* Application Identity Section */}
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-6 text-indigo-600">
            <Cpu size={24} />
            <h2 className="text-xl font-bold text-slate-900">Application Identity</h2>
          </div>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Application Name</label>
              <input 
                type="text"
                value={settings['app_name']?.value || 'Aras Framework'}
                onChange={(e) => handleUpdate('app_name', e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              />
              <p className="text-xs text-slate-500 mt-2">The global display name of the application, used in emails and UI headers.</p>
            </div>
          </div>
        </div>

        {/* Localization Section */}
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-6 text-purple-600">
            <Languages size={24} />
            <h2 className="text-xl font-bold text-slate-900">Language & Localization</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Default System Language</label>
              <Combobox 
                options={[
                  { label: 'English (US)', value: 'en' },
                  { label: 'Bahasa Indonesia', value: 'id' },
                  { label: 'Español', value: 'es' },
                  { label: 'Français', value: 'fr' }
                ]}
                value={settings['default_language']?.value || 'en'}
                onChange={(val) => {
                  handleUpdate('default_language', val)
                  handleUpdate('core.language_default', val)
                }}
              />
              <p className="text-xs text-slate-500 mt-2">New users will inherit this language setting by default.</p>
            </div>

            
            <div className="p-6 bg-slate-50 rounded-2xl border border-slate-100 border-dashed">
              <div className="flex items-start gap-3">
                <Globe className="text-slate-400 mt-1" size={20} />
                <div>
                  <h4 className="text-sm font-bold text-slate-700 mb-1">Multi-Language UI</h4>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Aras uses a centralized translation system for metadata. 
                    You can manage translated labels for resources and fields via the 
                    <span className="font-bold text-indigo-600 ml-1">Translation Registry</span>.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Date & Time Section */}
          <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3 mb-6 text-indigo-600">
              <Calendar size={24} />
              <h2 className="text-xl font-bold text-slate-900">Date & Time</h2>
            </div>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Date Format</label>
                <Combobox 
                  options={[
                    { label: 'YYYY-MM-DD (2026-05-12)', value: 'YYYY-MM-DD' },
                    { label: 'DD/MM/YYYY (12/05/2026)', value: 'DD/MM/YYYY' },
                    { label: 'MM/DD/YYYY (05/12/2026)', value: 'MM/DD/YYYY' },
                    { label: 'DD-MMM-YYYY (12-May-2026)', value: 'DD-MMM-YYYY' }
                  ]}
                  value={settings['core.date_format']?.value || 'YYYY-MM-DD'}
                  onChange={(val) => handleUpdate('core.date_format', val)}
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Time Format</label>
                <Combobox 
                  options={[
                    { label: '24-hour (14:30:05)', value: 'HH:mm:ss' },
                    { label: '12-hour (02:30:05 PM)', value: 'hh:mm:ss A' }
                  ]}
                  value="HH:mm:ss"
                  onChange={() => {}}
                />
              </div>
            </div>

          </div>

          {/* Numbers & Currency Section */}
          <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3 mb-6 text-emerald-600">
              <Coins size={24} />
              <h2 className="text-xl font-bold text-slate-900">Numbers & Currency</h2>
            </div>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Number Format</label>
                <Combobox 
                  options={[
                    { label: '1,234.56 (US/UK)', value: '#,###.##' },
                    { label: '1.234,56 (German/IT)', value: '#.###,##' },
                    { label: '1 234,56 (French/RU)', value: '# ###,##' }
                  ]}
                  value={settings['core.number_format']?.value || '#,###.##'}
                  onChange={(val) => handleUpdate('core.number_format', val)}
                />
              </div>


              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Decimal Precision</label>
                  <input 
                    type="number"
                    min="0"
                    max="6"
                    value={settings['core.decimal_precision']?.value || '2'}
                    onChange={(e) => handleUpdate('core.decimal_precision', e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Currency Symbol</label>
                  <input 
                    type="text"
                    value={settings['core.currency_symbol']?.value || '$'}
                    onChange={(e) => handleUpdate('core.currency_symbol', e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Maintenance Section */}
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-6 text-amber-600">
            <ShieldAlert size={24} />
            <h2 className="text-xl font-bold text-slate-900">System Control</h2>
          </div>
          
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-2xl border border-amber-100">
              <div>
                <label className="block text-sm font-bold text-amber-900 mb-1">Maintenance Mode</label>
                <p className="text-xs text-amber-700">Disable public access. Only administrators will be able to log in.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer"
                  checked={settings['maintenance_mode']?.value === 'true'}
                  onChange={(e) => handleUpdate('maintenance_mode', e.target.checked ? 'true' : 'false')}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Advanced Section for DevTools linking */}
        <div className="bg-slate-900 p-8 rounded-[2rem] text-white">
          <div className="flex items-center gap-3 mb-4 text-emerald-400">
            <Database size={24} />
            <h2 className="text-xl font-bold">Raw Settings Database</h2>
          </div>
          <p className="text-slate-400 text-sm mb-6">
            You can view, add, or delete all raw key-value pairs directly in the generic List View for advanced configuration.
          </p>
          <a 
            href="/dev/table/registry/sys_settings"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-bold transition-all border border-slate-700"
          >
            <Activity size={16} />
            Open Raw Table View
          </a>
        </div>

      </div>
    </div>
  )
}

export default GlobalSettings