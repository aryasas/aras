import React from 'react';
import { useUIStore } from '../../store/uiStore';
import { X } from 'lucide-react';

const SidePanel: React.FC = () => {
  const { panel, closePanel } = useUIStore();

  if (!panel.isOpen) return null;

  return (
    <div className="fixed inset-0 z-[80] flex justify-end bg-[var(--aras-text)]/40 backdrop-blur-sm animate-in fade-in duration-300">
      {/* Backdrop area that closes panel */}
      <div className="flex-1" onClick={closePanel}></div>

      {/* Panel Content */}
      <div
        className={`w-full ${panel.width} bg-[var(--aras-panel)] h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300 ease-out`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5 border-b border-[var(--aras-border)] flex items-center justify-between bg-[var(--aras-panel-soft)]/50 backdrop-blur-sm">
          <h2 className="text-xl font-extrabold tracking-tight text-[var(--aras-text)]">{panel.title}</h2>
          <button
            onClick={closePanel}
            className="p-2 hover:bg-[var(--aras-panel)] rounded-[var(--aras-radius)] text-[var(--aras-muted)] hover:text-[var(--aras-text)] border border-transparent hover:border-[var(--aras-border)] transition-all shadow-sm hover:shadow"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6 bg-[var(--aras-panel)]">
          {panel.content}
        </div>
      </div>
    </div>
  );
};

export default SidePanel;
