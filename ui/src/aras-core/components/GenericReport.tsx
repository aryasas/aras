import React from 'react';
import { Printer, Download, ArrowLeft } from 'lucide-react';
import { FormattingService } from '../services/FormattingService';

interface GenericReportProps {
  title: string;
  data: any[];
  columns: { field: string; label: string; type?: string }[];
  onBack?: () => void;
}

export const GenericReport: React.FC<GenericReportProps> = ({ title, data = [], columns = [], onBack }) => {
  const handlePrint = () => {
    window.print();
  };

  const handleExportCSV = () => {
    if (!data || !data.length) return;
    const headers = (columns || []).map(c => c.label).join(',');
    const rows = (data || []).map(row => 
      (columns || []).map((c, colIdx) => {
        let val = Array.isArray(row) ? row[colIdx] : row[c.field];
        if (typeof val === 'string') val = `"${val.replace(/"/g, '""')}"`;
        return val ?? '';
      }).join(',')
    );
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${(title || 'report').toLowerCase().replace(/\s+/g, '_')}_report.csv`;
    link.click();
  };

  return (
    <div className="p-8 print:p-0">
      {/* Report Controls (Hidden in Print) */}
      <div className="flex items-center justify-between mb-8 print:hidden">
        <div className="flex items-center gap-4">
          {onBack && (
            <button onClick={onBack} className="p-2 hover:bg-[var(--aras-panel-soft)] rounded-xl transition-colors text-[var(--aras-text)]">
              <ArrowLeft size={20} />
            </button>
          )}
          <h1 className="text-2xl font-bold text-[var(--aras-text)]">{title || 'Untitled Report'}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-4 py-2 border border-[var(--aras-border)] rounded-xl text-sm font-bold text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] transition-all"
          >
            <Download size={18} />
            <span>Export CSV</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-6 py-2 bg-[var(--aras-accent)] text-white rounded-xl text-sm font-bold hover:opacity-90 transition-all shadow-md"
          >
            <Printer size={18} />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Actual Report Content */}
      <div className="space-y-6">
        <div className="text-center space-y-2 mb-10 hidden print:block">
          <h1 className="text-3xl font-black text-slate-900 uppercase tracking-tighter">{title || 'Untitled Report'}</h1>
          <p className="text-sm text-slate-500 font-medium">Generated on {new Date().toLocaleString()}</p>
          <div className="h-1 w-24 bg-slate-900 mx-auto rounded-full" />
        </div>

        <div className="overflow-x-auto border border-[var(--aras-border)] rounded-2xl print:border-none">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--aras-panel-soft)] border-b border-[var(--aras-border)] print:bg-white">
                {(columns || []).map(col => (
                  <th key={col.field} className="px-6 py-4 text-xs font-black text-[var(--aras-muted)] uppercase tracking-widest">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(data || []).map((row, idx) => (
                <tr key={idx} className="border-b border-[var(--aras-border)] last:border-none hover:bg-[var(--aras-panel-soft)]/50 transition-colors">
                  {(columns || []).map((col, colIdx) => {
                    const val = Array.isArray(row) ? row[colIdx] : row[col.field];
                    return (
                      <td key={col.field} className="px-6 py-4 text-sm text-[var(--aras-text)] font-medium">
                        {col.type === 'currency' ? (
                           FormattingService.formatCurrency(Number(val || 0))
                        ) : col.type === 'date' ? (
                           FormattingService.formatDate(val)
                        ) : String(val ?? '-')}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!data || data.length === 0) && (
          <div className="p-20 text-center text-[var(--aras-muted)] font-medium italic">
            No records found for this report.
          </div>
        )}

        <div className="hidden print:block pt-12 text-[10px] text-slate-400 text-center border-t border-slate-200 mt-20">
          Aras Framework — Modular ERP System &copy; {new Date().getFullYear()}
        </div>
      </div>
    </div>
  );
};

export default GenericReport;
