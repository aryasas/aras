import React, { useState } from 'react';
import { Download, AlertCircle, Check } from 'lucide-react';

interface ImportMappingProps {
  csvHeaders: string[];
  resourceFields: { name: string, label: string }[];
  onConfirm: (mapping: Record<string, string>) => void;
  onCancel: () => void;
}

export const ImportMapping: React.FC<ImportMappingProps> = ({ 
  csvHeaders, 
  resourceFields, 
  onConfirm, 
  onCancel 
}) => {
  const [mapping, setMapping] = useState<Record<string, string>>({});

  const handleMap = (csvHeader: string, modelField: string) => {
    setMapping(prev => {
      const newMap = { ...prev };
      if (modelField === '') {
        delete newMap[csvHeader];
      } else {
        newMap[csvHeader] = modelField;
      }
      return newMap;
    });
  };

  const autoMap = () => {
    const newMap: Record<string, string> = {};
    csvHeaders.forEach(header => {
      const match = resourceFields.find(f => 
        f.name.toLowerCase() === header.toLowerCase() || 
        f.label.toLowerCase() === header.toLowerCase()
      );
      if (match) newMap[header] = match.name;
    });
    setMapping(newMap);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">Map your CSV columns to the database fields.</p>
          <button 
            onClick={autoMap}
            className="text-xs font-bold text-indigo-600 hover:underline"
          >
            Auto-Match Fields
          </button>
        </div>

        <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-auto pr-2">
          {csvHeaders.map(header => (
            <div key={header} className="flex items-center gap-4 bg-white p-3 rounded-2xl border border-slate-200">
              <div className="flex-1">
                <span className="text-xs font-bold text-slate-400 uppercase block mb-1">CSV Column</span>
                <span className="text-sm font-medium text-slate-700">{header}</span>
              </div>
              
              <div className="flex-shrink-0">
                <Download size={16} className="text-slate-300" />
              </div>

              <div className="flex-1">
                <span className="text-xs font-bold text-slate-400 uppercase block mb-1">Target Field</span>
                <select 
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg text-xs p-2 outline-none focus:ring-1 focus:ring-indigo-500"
                  value={mapping[header] || ''}
                  onChange={(e) => handleMap(header, e.target.value)}
                >
                  <option value="">(Ignore Column)</option>
                  {resourceFields.map(f => (
                    <option key={f.name} value={f.name}>{f.label}</option>
                  ))}
                </select>
              </div>
            </div>
          ))}
        </div>

        {Object.keys(mapping).length === 0 && (
          <div className="flex items-center gap-2 p-3 bg-amber-50 text-amber-700 rounded-xl border border-amber-100">
            <AlertCircle size={18} />
            <span className="text-xs font-medium">No fields mapped yet. Rows will be ignored.</span>
          </div>
        )}
      </div>

      <div className="mt-auto p-6 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-3">
        <button 
          onClick={onCancel}
          className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-white rounded-xl transition-all"
        >
          Cancel
        </button>
        <button 
          onClick={() => onConfirm(mapping)}
          disabled={Object.keys(mapping).length === 0}
          className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 disabled:opacity-50"
        >
          <Check size={18} />
          <span>Start Import</span>
        </button>
      </div>
    </div>
  );
};
