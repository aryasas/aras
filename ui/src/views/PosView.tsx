import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Loader2, Minus, Plus, Receipt, X } from 'lucide-react'
import api from '../lib/api'
import Combobox from '../aras-core/components/Combobox'
import { useAras } from '../aras-core/hooks/useAras'

interface PosSession {
  id: number
  number?: string
  mode?: 'sales' | 'purchase' | 'both'
  status?: string
}

interface PosItem {
  id: number
  code?: string
  name: string
  price?: number
  default_sale_price?: number
  default_purchase_price?: number
  qty_on_hand?: number
}

interface CartLine {
  item: PosItem
  qty: number
}

interface QuickInvoiceResult {
  invoice_number?: string
  invoice_id?: number
  change_amount?: number
}

const getItemPrice = (item: PosItem) => Number(item.price ?? item.default_sale_price ?? item.default_purchase_price ?? 0)

export default function PosView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { notify, formatCurrency } = useAras()
  const [session, setSession] = useState<PosSession | null>(null)
  const [items, setItems] = useState<PosItem[]>([])
  const [cart, setCart] = useState<CartLine[]>([])
  const [search, setSearch] = useState('')
  const [partyId, setPartyId] = useState<number | null>(null)
  const [paymentModeId, setPaymentModeId] = useState<number | null>(null)
  const [amountPaid, setAmountPaid] = useState('')
  const [posMode, setPosMode] = useState<'sales' | 'purchase'>('sales')
  const [loading, setLoading] = useState(true)
  const [charging, setCharging] = useState(false)
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    if (!id) return
    api.get(`/erp/pot/sessions/${id}`)
      .then(res => {
        const s = res.data as PosSession
        setSession(s)
        setPosMode(s.mode === 'purchase' ? 'purchase' : 'sales')
      })
      .catch(err => notify(err.response?.data?.detail || 'Failed to load session', 'error'))
  }, [id])

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.get(`/erp/pot/sessions/${id}/items`, { params: { mode: posMode } })
      .then(res => setItems(res.data as PosItem[]))
      .catch(err => notify(err.response?.data?.detail || 'Failed to load items', 'error'))
      .finally(() => setLoading(false))
  }, [id, posMode])

  const filteredItems = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return items
    return items.filter(item =>
      item.name.toLowerCase().includes(q) || item.code?.toLowerCase().includes(q)
    )
  }, [items, search])

  const subtotal = useMemo(
    () => cart.reduce((sum, line) => sum + getItemPrice(line.item) * line.qty, 0),
    [cart]
  )
  const paid = Number(amountPaid) || 0
  const change = Math.max(0, paid - subtotal)

  const addItem = (item: PosItem) => {
    setCart(prev => {
      const existing = prev.find(line => line.item.id === item.id)
      if (existing) {
        return prev.map(line => line.item.id === item.id ? { ...line, qty: line.qty + 1 } : line)
      }
      return [...prev, { item, qty: 1 }]
    })
  }

  const changeQty = (itemId: number, delta: number) => {
    setCart(prev => prev
      .map(line => line.item.id === itemId ? { ...line, qty: line.qty + delta } : line)
      .filter(line => line.qty > 0)
    )
  }

  const clearCart = () => {
    setCart([])
    setPartyId(null)
    setAmountPaid('')
  }

  const charge = async () => {
    if (!id || cart.length === 0 || !paymentModeId) return

    setCharging(true)
    try {
      const res = await api.post(`/erp/pot/sessions/${id}/quick_invoice`, {
        party_id: partyId,
        payment_mode_id: paymentModeId,
        amount_paid: paid,
        mode: posMode,
        items: cart.map(line => ({
          item_id: line.item.id,
          qty: line.qty,
          unit_price: getItemPrice(line.item)
        }))
      })
      const result = res.data as QuickInvoiceResult
      notify(`Invoice ${result.invoice_number ?? result.invoice_id} charged. Change: ${formatCurrency(result.change_amount ?? 0)}`, 'success')
      clearCart()
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Charge failed', 'error')
    } finally {
      setCharging(false)
    }
  }

  const closeSession = async () => {
    if (!id) return

    setClosing(true)
    try {
      await api.post(`/erp/pot/sessions/${id}/action/close_session`, { closing_balance: 0 })
      notify('Session closed', 'success')
      navigate('/erp/pot/sessions')
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to close session', 'error')
    } finally {
      setClosing(false)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        <Loader2 size={22} className="animate-spin mr-2" />
        <span className="text-sm font-medium">Loading POS...</span>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-slate-100 -m-6">
      <div className="h-16 px-6 bg-white border-b border-slate-200 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <button
            type="button"
            onClick={() => navigate('/erp/pot/sessions')}
            className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Back"
          >
            <ArrowLeft size={18} />
          </button>
          <div className="min-w-0">
            <h1 className="text-base font-bold text-slate-900 truncate">Session {session?.number ?? `#${id}`}</h1>
            <p className="text-xs text-slate-500">{session?.status ?? 'Open'}</p>
          </div>
          {session?.mode === 'both' ? (
            <div className="flex rounded-lg border border-slate-200 overflow-hidden text-xs font-bold">
              <button type="button" onClick={() => { setPosMode('sales'); setCart([]) }}
                className={`px-3 py-1 transition-colors ${posMode === 'sales' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}>
                Sales
              </button>
              <button type="button" onClick={() => { setPosMode('purchase'); setCart([]) }}
                className={`px-3 py-1 transition-colors ${posMode === 'purchase' ? 'bg-sky-600 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}>
                Purchase
              </button>
            </div>
          ) : (
            <span className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase ${posMode === 'sales' ? 'bg-emerald-50 text-emerald-700' : 'bg-sky-50 text-sky-700'}`}>
              {posMode}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={closeSession}
          disabled={closing}
          className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 disabled:opacity-60 transition-colors"
        >
          {closing ? 'Closing...' : 'Close Session'}
        </button>
      </div>

      <div className="flex-1 grid grid-cols-1 xl:grid-cols-[1fr_440px] min-h-0">
        <div className="p-6 flex flex-col min-h-0 border-r border-slate-200">
          <div className="mb-5">
            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search items..."
              className="w-full px-4 py-3 rounded-2xl border border-slate-200 bg-white text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
            />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 overflow-y-auto pr-1">
            {filteredItems.map(item => (
              <button
                key={item.id}
                type="button"
                onClick={() => addItem(item)}
                className="text-left bg-white border border-slate-200 rounded-2xl p-4 min-h-32 shadow-sm hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="text-sm font-bold text-slate-900 line-clamp-2">{item.name}</div>
                {item.code && <div className="mt-1 text-xs text-slate-400">{item.code}</div>}
                <div className="mt-5 flex items-end justify-between gap-3">
                  <span className="text-base font-bold text-indigo-600">{formatCurrency(getItemPrice(item))}</span>
                  <span className="text-xs text-slate-400">{item.qty_on_hand ?? 0}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <aside className="bg-white flex flex-col min-h-0">
          <div className="h-14 px-6 border-b border-slate-200 flex items-center gap-2 shrink-0">
            <Receipt size={17} className="text-slate-400" />
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Cart</h2>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {cart.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                No items selected.
              </div>
            ) : (
              cart.map(line => (
                <div key={line.item.id} className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-slate-900 truncate">{line.item.name}</div>
                    <div className="text-xs text-slate-500">{formatCurrency(getItemPrice(line.item))}</div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={() => changeQty(line.item.id, -1)}
                      className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50"
                      title="Decrease quantity"
                    >
                      <Minus size={13} />
                    </button>
                    <span className="w-8 text-center text-sm font-bold text-slate-900">{line.qty}</span>
                    <button
                      type="button"
                      onClick={() => changeQty(line.item.id, 1)}
                      className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50"
                      title="Increase quantity"
                    >
                      <Plus size={13} />
                    </button>
                  </div>
                  <div className="w-20 text-right text-sm font-semibold text-slate-900">
                    {formatCurrency(getItemPrice(line.item) * line.qty)}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-6 border-t border-slate-200 space-y-4 shrink-0">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500 font-medium">Subtotal</span>
              <span className="text-lg font-bold text-slate-900">{formatCurrency(subtotal)}</span>
            </div>

            <div className="space-y-3">
              <label className="block">
                <span className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Party</span>
                <Combobox resource="erp/party/parties" value={partyId} onChange={setPartyId} placeholder="Optional party" />
              </label>
              <label className="block">
                <span className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Mode</span>
                <Combobox resource="erp/config/payment-modes" value={paymentModeId} onChange={setPaymentModeId} placeholder="Payment mode" />
              </label>
              <label className="block">
                <span className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Paid</span>
                <input
                  type="number"
                  min="0"
                  value={amountPaid}
                  onChange={(event) => setAmountPaid(event.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                />
              </label>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500 font-medium">Change</span>
              <span className="font-bold text-slate-900">{formatCurrency(change)}</span>
            </div>

            <div className="grid grid-cols-[1fr_auto] gap-2">
              <button
                type="button"
                onClick={charge}
                disabled={charging || cart.length === 0 || !paymentModeId}
                className="h-12 rounded-xl bg-indigo-600 text-white text-sm font-bold uppercase tracking-wider hover:bg-indigo-700 disabled:opacity-60 disabled:hover:bg-indigo-600 transition-colors"
              >
                {charging ? 'Charging...' : 'Charge'}
              </button>
              <button
                type="button"
                onClick={clearCart}
                disabled={cart.length === 0}
                className="h-12 w-12 rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-50 transition-colors flex items-center justify-center"
                title="Clear cart"
              >
                <X size={17} />
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
