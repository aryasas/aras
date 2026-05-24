import React, { useState, useEffect } from 'react';
import api from '../../lib/api';
import { X, Printer } from 'lucide-react';
import { useAras } from '../hooks/useAras';

interface PrintPreviewProps {
  resource: string;
  id: number | string;
  onClose: () => void;
}

interface PrintData {
  doc_type: string;
  doc_number: string;
  date: string;
  party_name: string;
  lines: Array<{ description: string; qty: number; unit_price: number; subtotal: number }>;
  charges: Array<{ description: string; amount: number }>;
  subtotal: number;
  total_charge: number;
  total_amount: number;
  org_name: string;
}

export const PrintPreview: React.FC<PrintPreviewProps> = ({ resource, id, onClose }) => {
  const [printData, setPrintData] = useState<PrintData | null>(null);
  const [loading, setLoading] = useState(true);
  const { notify } = useAras();

  useEffect(() => {
    const fetchPrintData = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/accounting/${resource}/${id}/print`);
        setPrintData(res.data);
      } catch (err: any) {
        notify(err.response?.data?.detail || 'Failed to fetch print data', 'error');
        onClose(); // Close on error
      } finally {
        setLoading(false);
      }
    };
    fetchPrintData();
  }, [resource, id, onClose, notify]);

  const handlePrint = () => {
    // Hide buttons and set margins for printing
    const style = document.createElement('style');
    style.innerHTML = `
      @media print {
        body > *:not(.print-container) { display: none !important; }
        .print-container {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          margin: 0;
          padding: 0;
          overflow: visible;
          background-color: white;
          z-index: 9999;
        }
        .print-container .no-print { display: none !important; }
        @page { margin: 1cm; }
      }
    `;
    document.head.appendChild(style);
    
    window.print();

    // Clean up
    style.remove();
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <div className="bg-[var(--aras-panel)] rounded-[var(--aras-radius-lg)] shadow-2xl p-8 max-w-2xl w-full text-center text-[var(--aras-muted)]">
          Loading print preview...
        </div>
      </div>
    );
  }

  if (!printData) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-[var(--aras-panel)] rounded-[var(--aras-radius-lg)] shadow-2xl p-8 max-w-3xl w-full h-[90vh] flex flex-col print-container">
        {/* Header - No Print */}
        <div className="flex justify-between items-center pb-4 border-b border-[var(--aras-border)] no-print">
          <h2 className="text-xl font-bold text-[var(--aras-text)]">Print Preview: {printData.doc_number}</h2>
          <div className="flex gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] text-sm font-bold hover:brightness-110 transition-all"
            >
              <Printer size={18} /> Print
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius)] text-[var(--aras-muted)] transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Printable Content */}
        <div className="flex-1 overflow-y-auto p-4 print-content">
          <div className="min-h-full bg-[var(--aras-panel)] text-[var(--aras-text)] font-sans text-sm">
            {/* Top Section */}
            <div className="flex justify-between items-start mb-8">
              <div className="text-xl font-bold">{printData.org_name}</div>
              <div className="text-right">
                <p className="text-lg font-bold uppercase">{printData.doc_type}</p>
                <p className="text-sm">No: {printData.doc_number}</p>
              </div>
            </div>

            <div className="flex justify-between mb-8">
              <div>
                <p className="font-semibold">To:</p>
                <p>{printData.party_name}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">Date:</p>
                <p>{printData.date ? new Date(printData.date).toLocaleDateString() : 'N/A'}</p>
              </div>
            </div>

            {/* Lines Table */}
            <h3 className="text-md font-bold mb-3">Items:</h3>
            <table className="w-full border-collapse mb-8">
              <thead>
                <tr className="bg-slate-100">
                  <th className="border p-2 text-left">Description</th>
                  <th className="border p-2 text-right w-20">Qty</th>
                  <th className="border p-2 text-right w-24">Unit Price</th>
                  <th className="border p-2 text-right w-24">Amount</th>
                </tr>
              </thead>
              <tbody>
                {printData.lines.map((line, index) => (
                  <tr key={index}>
                    <td className="border p-2">{line.description}</td>
                    <td className="border p-2 text-right">{line.qty}</td>
                    <td className="border p-2 text-right">{line.unit_price.toFixed(2)}</td>
                    <td className="border p-2 text-right">{(line.subtotal).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Charges */}
            {printData.charges.length > 0 && (
              <>
                <h3 className="text-md font-bold mb-3">Charges:</h3>
                <table className="w-full border-collapse mb-8">
                  <thead>
                    <tr className="bg-[var(--aras-panel-soft)]">
                      <th className="border p-2 text-left">Description</th>
                      <th className="border p-2 text-right w-24">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {printData.charges.map((charge, index) => (
                      <tr key={index}>
                        <td className="border p-2">{charge.description}</td>
                        <td className="border p-2 text-right">{charge.amount.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {/* Totals */}
            <div className="flex justify-end">
              <div className="w-64">
                <div className="flex justify-between border-b border-[var(--aras-border)] py-1">
                  <span>Subtotal:</span>
                  <span className="font-semibold">{printData.subtotal.toFixed(2)}</span>
                </div>
                {printData.total_charge > 0 && (
                  <div className="flex justify-between border-b border-[var(--aras-border)] py-1">
                    <span>Charges:</span>
                    <span className="font-semibold">{printData.total_charge.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between border-b border-[var(--aras-border)] py-1 text-lg font-bold">
                  <span>Total Amount:</span>
                  <span>{printData.total_amount.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
