import { useState, useEffect } from 'react'
import { Database, Save, RefreshCw, Cpu, Activity, ShieldAlert } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'

interface Setting {
  id: number;
  key: string;
  value: string;
  description: string;
}

function SysSettings() {
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showAlert, showError } = useUIStore();

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await api.post('/query/sys_settings', {
        filters: [
          // Filter out regional settings which are handled by RegionalSettings
          { field: 'key', op: 'not_ilike', value: 'core.%' }
        ]
      });
      
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
      showAlert('Success', 'System settings updated successfully.');
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
        <p>Loading system configuration...</p>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">System & Database Settings</h1>
          <p className="text-slate-500 mt-1">Configure platform behavior, global preferences, and maintenance mode.</p>
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

      <div className="grid grid-cols-1 gap-6">
        {/* General Application Section */}
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
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Default Language</label>
              <select 
                value={settings['default_language']?.value || 'en'}
                onChange={(e) => handleUpdate('default_language', e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              >
                <option value="en">English</option>
                <option value="id">Bahasa Indonesia</option>
              </select>
            </div>
          </div>
        </div>

        {/* Maintenance & Security Section */}
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-6 text-amber-600">
            <ShieldAlert size={24} />
            <h2 className="text-xl font-bold text-slate-900">Maintenance & Security</h2>
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
            href="/devtools/table/admin/sys_settings"
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

export default SysSettings
