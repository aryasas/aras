import React, { useState } from 'react'

export default function PosActionPage({ action, terminal, session, order_count, current_user }) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    opening_balance: 0,
    cash_counted: 0,
    notes: ''
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    const form = e.target
    const formData = new FormData(form)
    
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      
      if (response.redirected) {
        window.location.href = response.url
      } else {
        const result = await response.json()
        if (result.ok || result.success) {
          window.location.href = result.redirect || '/admin/erp/pos/'
        } else {
          alert(result.error || 'Action failed')
        }
      }
    } catch (err) {
      console.error('Action error:', err)
      alert('Network error')
    } finally {
      setLoading(false)
    }
  }

  const isOpening = action === 'open'

  return (
    <div className="max-w-xl mx-auto py-12 animate-fade-in">
      <div className="bg-white border border-[#dde3e7] rounded-md shadow-sm overflow-hidden">
        <div className={`h-1 w-full ${isOpening ? 'bg-aras-accent' : 'bg-red-500'}`}></div>
        
        <div className="p-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-studio-serif font-bold text-aras-primary tracking-tight">
              {isOpening ? 'Open POS Session' : 'Close POS Session'}
            </h2>
            <a href="/admin/erp/pos/" className="text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest hover:text-aras-accent transition-colors">
              Cancel
            </a>
          </div>

          <div className="mb-8 p-6 bg-[#faf8f3] border border-[#dde3e7] rounded flex items-center gap-6">
            <div className={`w-12 h-12 flex items-center justify-center rounded-md border ${isOpening ? 'bg-aras-accent/5 border-aras-accent/20 text-aras-accent' : 'bg-red-50 border-red-100 text-red-500'}`}>
               <i className="fa fa-desktop text-xl"></i>
            </div>
            <div>
              <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em] mb-1">Terminal</span>
              <h3 className="text-lg font-studio-serif font-bold text-aras-primary">
                {isOpening ? terminal?.name : session?.terminal_name}
              </h3>
              <p className="text-[11px] text-[#9aacb8] font-mono">
                {isOpening ? terminal?.code : session?.terminal_code}
              </p>
            </div>
          </div>

          {!isOpening && (
             <div className="mb-8 grid grid-cols-2 gap-4">
                <div className="p-4 border border-[#f4f2ee] rounded">
                   <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-1">Opening Float</span>
                   <span className="text-md font-bold text-aras-primary">Rp {session?.opening_balance?.toLocaleString()}</span>
                </div>
                <div className="p-4 border border-[#f4f2ee] rounded">
                   <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-1">Total Orders</span>
                   <span className="text-md font-bold text-aras-primary">{order_count}</span>
                </div>
             </div>
          )}

          <form 
            onSubmit={handleSubmit} 
            action={isOpening ? `/admin/erp/pos/open/${terminal?.id}` : `/admin/erp/pos/session/${session?.id}/close`}
            className="space-y-6"
          >
            {isOpening ? (
              <div>
                <label className="block text-[10px] font-bold text-aras-primary uppercase tracking-[0.2em] mb-3">Opening Float (Cash)</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9aacb8] font-bold text-sm">Rp</span>
                  <input 
                    type="number" 
                    name="opening_balance"
                    defaultValue="0"
                    step="1000"
                    min="0"
                    className="w-full pl-12 pr-4 py-4 bg-white border border-[#dde3e7] rounded text-xl font-bold text-aras-primary outline-none focus:ring-2 focus:ring-aras-accent/20 transition-all"
                    required
                  />
                </div>
                <p className="mt-2 text-[11px] text-[#9aacb8] italic">Amount of cash in drawer at start of shift.</p>
              </div>
            ) : (
              <>
                <div>
                  <label className="block text-[10px] font-bold text-aras-primary uppercase tracking-[0.2em] mb-3">Counted Cash (Real)</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9aacb8] font-bold text-sm">Rp</span>
                    <input 
                      type="number" 
                      name="cash_counted"
                      defaultValue="0"
                      step="1000"
                      min="0"
                      className="w-full pl-12 pr-4 py-4 bg-white border border-[#dde3e7] rounded text-xl font-bold text-aras-primary outline-none focus:ring-2 focus:ring-red-500/20 transition-all"
                      required
                    />
                  </div>
                  <p className="mt-2 text-[11px] text-[#9aacb8] italic">Physically count the cash in your drawer.</p>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-aras-primary uppercase tracking-[0.2em] mb-3">Closing Notes</label>
                  <textarea 
                    name="notes"
                    rows="3"
                    className="w-full px-4 py-3 bg-[#faf8f3] border border-[#dde3e7] rounded text-sm text-aras-primary outline-none focus:ring-1 focus:ring-aras-accent transition-all"
                    placeholder="Optional notes about this shift..."
                  ></textarea>
                </div>
              </>
            )}

            <div className="pt-6 border-t border-[#f4f2ee] flex items-center justify-between">
              <div className="flex items-center gap-3">
                 <div className="w-8 h-8 bg-[#faf8f3] rounded-full flex items-center justify-center text-[#9aacb8]">
                    <i className="fa fa-user text-xs"></i>
                 </div>
                 <span className="text-[11px] font-bold text-aras-primary">{current_user?.username}</span>
              </div>
              <button 
                type="submit"
                disabled={loading}
                className={`px-8 py-3 text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded shadow-sm transition-all flex items-center ${isOpening ? 'bg-aras-accent hover:bg-aras-accent/90' : 'bg-red-500 hover:bg-red-600'}`}
              >
                {loading ? <i className="fa fa-spinner fa-spin mr-2"></i> : <i className={`fa ${isOpening ? 'fa-play' : 'fa-power-off'} mr-2`}></i>}
                {isOpening ? 'Open Session' : 'Close Session'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
