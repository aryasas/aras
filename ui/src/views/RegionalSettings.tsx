import { useState, useEffect } from 'react'
import { Globe, Save, RefreshCw, Coins, Languages, Calendar } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'

interface Setting {
  id: number;
  key: string;
  value: string;
  description: string;
}

function RegionalSettings() {
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showAlert, showError } = useUIStore();

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await api.post('/query/sys_settings', {
        filters: [
          { field: 'key', op: 'ilike', value: 'core.' }
        ]
      });
      
      const settingsMap: Record<string, Setting> = {};
      response.data.items.forEach((s: Setting) => {
        settingsMap[s.key] = s;
      });
      setSettings(settingsMap);
    } catch (err) {
      showError('Error', 'Failed to load regional settings.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleUpdate = (key: string, value: string) => {
    setSettings(prev => ({
      ...prev,
      [key]: { ...prev[key], value }
    }));
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const promises = Object.values(settings).map(s => 
        api.patch(`/admin/sys_settings/${s.id}`, { value: s.value })
      );
      await Promise.all(promises);
      showAlert('Success', 'Regional settings updated successfully.');
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
        <p>Loading regional configuration...</p>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Regional Settings</h1>
          <p className="text-slate-500 mt-1">Configure global formats for dates, numbers, and currency.</p>
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
              <select 
                value={settings['core.date_format']?.value || 'YYYY-MM-DD'}
                onChange={(e) => handleUpdate('core.date_format', e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              >
                <option value="YYYY-MM-DD">YYYY-MM-DD (2026-05-12)</option>
                <option value="DD/MM/YYYY">DD/MM/YYYY (12/05/2026)</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY (05/12/2026)</option>
                <option value="DD-MMM-YYYY">DD-MMM-YYYY (12-May-2026)</option>
              </select>
              <p className="text-xs text-slate-500 mt-2">Used for all date displays across the system.</p>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Time Format</label>
              <select 
                defaultValue="HH:mm:ss"
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              >
                <option value="HH:mm:ss">24-hour (14:30:05)</option>
                <option value="hh:mm:ss A">12-hour (02:30:05 PM)</option>
              </select>
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
              <select 
                value={settings['core.number_format']?.value || '#,###.##'}
                onChange={(e) => handleUpdate('core.number_format', e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              >
                <option value="#,###.##">1,234.56 (US/UK)</option>
                <option value="#.###,##">1.234,56 (German/IT)</option>
                <option value="# ###,##">1 234,56 (French/RU)</option>
              </select>
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

        {/* Localization Section */}
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm md:col-span-2">
          <div className="flex items-center gap-3 mb-6 text-purple-600">
            <Languages size={24} />
            <h2 className="text-xl font-bold text-slate-900">Language & Localization</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Default System Language</label>
              <select 
                value={settings['core.language_default']?.value || 'en'}
                onChange={(e) => handleUpdate('core.language_default', e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              >
                <option value="en">English (US)</option>
                <option value="id">Bahasa Indonesia</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
              </select>
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
      </div>
    </div>
  )
}

export default RegionalSettings
