import React from 'react';
import { useUIStore } from '../../store/uiStore';
import { X } from 'lucide-react';

const SidePanel: React.FC = () => {
  const { panel, closePanel } = useUIStore();

  if (!panel.isOpen) return null;

  return (
    <div className="fixed inset-0 z-[80] flex justify-end bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-300">
      {/* Backdrop area that closes panel */}
      <div className="flex-1" onClick={closePanel}></div>
      
      {/* Panel Content */}
      <div 
        className={`w-full ${panel.width} bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300 ease-out`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h2 className="text-xl font-bold text-slate-900">{panel.title}</h2>
          <button 
            onClick={closePanel}
            className="p-2 hover:bg-white rounded-xl text-slate-400 hover:text-slate-600 border border-transparent hover:border-slate-200 transition-all"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-auto p-6 bg-white">
          {panel.content}
        </div>
      </div>
    </div>
  );
};

export default SidePanel;
