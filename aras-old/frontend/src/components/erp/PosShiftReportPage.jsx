import React from 'react'

export default function PosShiftReportPage({ data }) {
  const { 
    session, 
    total_sales, 
    total_tax, 
    total_discount, 
    expected_cash, 
    cash_difference,
    payment_summary = {},
    top_products = [],
    hourly_sales = []
  } = data

  return (
    <div className="space-y-8 pb-24 animate-fade-in print:p-0">
      
      {/* HEADER */}
      <div className="flex items-center justify-between border-b border-[#dde3e7] pb-6 print:hidden">
        <div>
           <div className="flex items-center gap-3 mb-1">
              <a href="/admin/erp/pos/" className="w-8 h-8 flex items-center justify-center rounded-full bg-[#faf8f3] text-[#9aacb8] hover:text-aras-accent transition-colors">
                <i className="fa fa-arrow-left text-xs"></i>
              </a>
              <h1 className="text-2xl font-studio-serif font-bold text-aras-primary tracking-tight">
                Shift Report: <span className="text-[#9aacb8] font-normal">{session?.shift_number || session?.id}</span>
              </h1>
           </div>
           <p className="text-[11px] text-[#9aacb8] font-studio-serif italic ml-11">
             Terminal: {session?.terminal_name} • Cashier: {session?.cashier_name}
           </p>
        </div>
        <div className="flex gap-2">
           <button 
            onClick={() => window.print()}
            className="px-6 py-2 border border-[#dde3e7] text-aras-primary text-[11px] font-bold uppercase tracking-widest rounded hover:bg-[#faf8f3] transition-colors"
           >
             <i className="fa fa-print mr-2"></i> Print
           </button>
           <a 
            href="/admin/erp/pos/"
            className="px-6 py-2 bg-aras-accent text-white text-[11px] font-bold uppercase tracking-widest rounded hover:bg-aras-accent/90 transition-colors"
           >
             <i className="fa fa-home mr-2"></i> POS Home
           </a>
        </div>
      </div>

      {/* SUMMARY CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white border border-[#dde3e7] p-6 rounded shadow-sm">
           <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em] mb-4">Total Sales</span>
           <div className="flex items-baseline gap-2">
              <span className="text-3xl font-studio-serif font-bold text-green-600 tracking-tighter">
                Rp {total_sales?.toLocaleString()}
              </span>
           </div>
           <p className="text-[10px] text-[#9aacb8] mt-2 font-bold uppercase tracking-widest">{data.order_count} Orders</p>
        </div>
        <div className="bg-white border border-[#dde3e7] p-6 rounded shadow-sm">
           <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em] mb-4">Tax Collected</span>
           <div className="flex items-baseline gap-2">
              <span className="text-3xl font-studio-serif font-bold text-blue-600 tracking-tighter">
                Rp {total_tax?.toLocaleString()}
              </span>
           </div>
        </div>
        <div className="bg-white border border-[#dde3e7] p-6 rounded shadow-sm">
           <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em] mb-4">Discounts</span>
           <div className="flex items-baseline gap-2">
              <span className="text-3xl font-studio-serif font-bold text-yellow-600 tracking-tighter">
                Rp {total_discount?.toLocaleString()}
              </span>
           </div>
        </div>
        <div className="bg-white border border-[#dde3e7] p-6 rounded shadow-sm">
           <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em] mb-4">Expected Cash</span>
           <div className="flex items-baseline gap-2">
              <span className="text-3xl font-studio-serif font-bold text-aras-primary tracking-tighter">
                Rp {expected_cash?.toLocaleString()}
              </span>
           </div>
           <p className={`text-[10px] mt-2 font-bold uppercase tracking-widest ${cash_difference >= 0 ? 'text-green-600' : 'text-red-500'}`}>
             Diff: {cash_difference >= 0 ? '+' : ''}{cash_difference?.toLocaleString()}
           </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* PAYMENT BREAKDOWN */}
        <div className="bg-white border border-[#dde3e7] rounded shadow-sm overflow-hidden">
           <div className="px-6 py-4 bg-[#faf8f3] border-b border-[#dde3e7] flex items-center justify-between">
              <h3 className="text-[12px] font-bold text-aras-primary uppercase tracking-[0.1em]">Payment Breakdown</h3>
              <i className="fa fa-credit-card text-[#9aacb8]"></i>
           </div>
           <table className="w-full text-sm">
              <thead className="bg-[#f4f2ee] text-[10px] font-bold text-[#9aacb8] uppercase">
                 <tr>
                    <th className="px-6 py-3 text-left">Method</th>
                    <th className="px-6 py-3 text-right">Amount</th>
                 </tr>
              </thead>
              <tbody className="divide-y divide-[#f4f2ee]">
                 {Object.entries(payment_summary).map(([method, amt]) => (
                   <tr key={method}>
                      <td className="px-6 py-3 text-aras-primary capitalize">{method}</td>
                      <td className="px-6 py-3 text-right font-mono text-aras-primary font-bold">Rp {amt.toLocaleString()}</td>
                   </tr>
                 ))}
                 {Object.keys(payment_summary).length === 0 && (
                   <tr>
                      <td colSpan="2" className="px-6 py-10 text-center text-[#9aacb8] italic">No payments recorded</td>
                   </tr>
                 )}
              </tbody>
              <tfoot className="bg-[#faf8f3] border-t border-[#dde3e7] font-bold">
                 <tr>
                    <td className="px-6 py-3 text-aras-primary">Total</td>
                    <td className="px-6 py-3 text-right font-mono text-aras-primary">Rp {total_sales?.toLocaleString()}</td>
                 </tr>
              </tfoot>
           </table>
        </div>

        {/* TOP PRODUCTS */}
        <div className="bg-white border border-[#dde3e7] rounded shadow-sm overflow-hidden">
           <div className="px-6 py-4 bg-[#faf8f3] border-b border-[#dde3e7] flex items-center justify-between">
              <h3 className="text-[12px] font-bold text-aras-primary uppercase tracking-[0.1em]">Best Selling Products</h3>
              <i className="fa fa-star text-[#9aacb8]"></i>
           </div>
           <div className="p-0">
              <table className="w-full text-sm">
                 <thead className="bg-[#f4f2ee] text-[10px] font-bold text-[#9aacb8] uppercase">
                    <tr>
                       <th className="px-6 py-3 text-left">Product</th>
                       <th className="px-6 py-3 text-center">Qty</th>
                       <th className="px-6 py-3 text-right">Total</th>
                    </tr>
                 </thead>
                 <tbody className="divide-y divide-[#f4f2ee]">
                    {top_products.map((p, i) => (
                      <tr key={i}>
                         <td className="px-6 py-3 text-aras-primary font-studio-serif">{p.name}</td>
                         <td className="px-6 py-3 text-center text-[#9aacb8] font-bold">{p.qty}</td>
                         <td className="px-6 py-3 text-right font-mono text-aras-primary">Rp {p.total?.toLocaleString()}</td>
                      </tr>
                    ))}
                    {top_products.length === 0 && (
                      <tr>
                         <td colSpan="3" className="px-6 py-10 text-center text-[#9aacb8] italic">No data available</td>
                      </tr>
                    )}
                 </tbody>
              </table>
           </div>
        </div>
      </div>

    </div>
  )
}
