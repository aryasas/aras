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
  doc_date?: string
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
const today = () => new Date().toISOString().slice(0, 10)
const normalizeList = <T,>(value: any): T[] => {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.items)) return value.items
  if (Array.isArray(value?.data)) return value.data
  if (Array.isArray(value?.data?.items)) return value.data.items
  return []
}

export default function PosView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { notify, formatCurrency } = useAras()
  const [session, setSession] = useState<PosSession | null>(null)
  const [openSessions, setOpenSessions] = useState<PosSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [creatingSession, setCreatingSession] = useState(false)
  const [items, setItems] = useState<PosItem[]>([])
  const [cart, setCart] = useState<CartLine[]>([])
  const [search, setSearch] = useState('')
  const [partyId, setPartyId] = useState<number | null>(null)
  const [paymentModeId, setPaymentModeId] = useState<number | null>(null)
  const [amountPaid, setAmountPaid] = useState('')
  const [posMode, setPosMode] = useState<'sales' | 'purchase'>('sales')
  const [isCreditMode, setIsCreditMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [charging, setCharging] = useState(false)
  const [closing, setClosing] = useState(false)
  const [receipt, setReceipt] = useState<(QuickInvoiceResult & { items: CartLine[]; paid: number; change: number; isCredit: boolean; mode: 'sales' | 'purchase' }) | null>(null)

  useEffect(() => {
    if (!id) return
    api.get(`/pot/sessions/${id}`)
      .then(res => {
        const s = res.data as PosSession
        setSession(s)
        setPosMode(s.mode === 'purchase' ? 'purchase' : 'sales')
      })
      .catch(err => notify(err.response?.data?.detail || 'Failed to load session', 'error'))
  }, [id])

  useEffect(() => {
    if (id) return
    setSessionsLoading(true)
    api.get('/pot/sessions', {
      params: {
        filters: JSON.stringify([{ field: 'status', op: '=', value: 'Open' }])
      }
    })
      .then(res => setOpenSessions(normalizeList<PosSession>(res.data)))
      .catch(err => notify(err.response?.data?.detail || 'Failed to load sessions', 'error'))
      .finally(() => setSessionsLoading(false))
  }, [id])

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.get(`/pot/sessions/${id}/items`, { params: { mode: posMode } })
      .then(res => setItems(normalizeList<PosItem>(res.data)))
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
    setIsCreditMode(false)
  }

  const createSession = async () => {
    setCreatingSession(true)
    try {
      const res = await api.post('/pot/sessions', {
        status: 'Open',
        mode: 'sales',
        doc_date: today()
      })
      const nextSession = res.data as PosSession
      navigate(`/pot/sessions/${nextSession.id}/pos`)
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to create session', 'error')
    } finally {
      setCreatingSession(false)
    }
  }

  const charge = async () => {
    if (!id || cart.length === 0) return
    if (!isCreditMode && !paymentModeId) return

    setCharging(true)
    try {
      const res = await api.post(`/pot/sessions/${id}/quick_invoice`, {
        party_id: partyId,
        payment_mode_id: isCreditMode ? null : paymentModeId,
        amount_paid: isCreditMode ? 0 : paid,
        mode: posMode,
        items: cart.map(line => ({
          item_id: line.item.id,
          qty: line.qty,
          unit_price: getItemPrice(line.item)
        }))
      })
      const result = res.data as QuickInvoiceResult
      if (isCreditMode) {
        notify(`Invoice ${result.invoice_number ?? result.invoice_id} — credit ${posMode === 'sales' ? 'sale (AR)' : 'purchase (AP)'} created.`, 'success')
      } else {
        notify(`Invoice ${result.invoice_number ?? result.invoice_id} charged. Change: ${formatCurrency(result.change_amount ?? 0)}`, 'success')
      }
      setReceipt({
        ...result,
        items: [...cart],
        paid: isCreditMode ? 0 : paid,
        change: result.change_amount ?? 0,
        isCredit: isCreditMode,
        mode: posMode
      })
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
      await api.post(`/pot/sessions/${id}/action/close_session`, { closing_balance: 0 })
      notify('Session closed', 'success')
      navigate('/pot/sessions')
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to close session', 'error')
    } finally {
      setClosing(false)
    }
  }

  if (!id) {
    return (
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Point of Sale</h1>
            <p className="text-slate-500 mt-1">Open an existing register session or start a new one.</p>
          </div>
          <button
            type="button"
            onClick={createSession}
            disabled={creatingSession}
            className="inline-flex items-center justify-center px-5 py-3 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {creatingSession ? 'Creating...' : 'New Session'}
          </button>
        </div>

        {sessionsLoading ? (
          <div className="h-56 flex items-center justify-center text-slate-400">
            <Loader2 size={22} className="animate-spin mr-2" />
            <span className="text-sm font-medium">Loading sessions...</span>
          </div>
        ) : openSessions.length === 0 ? (
          <div className="min-h-64 rounded-2xl border border-dashed border-slate-300 bg-white flex items-center justify-center p-8">
            <button
              type="button"
              onClick={createSession}
              disabled={creatingSession}
              className="px-5 py-3 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-60 transition-colors"
            >
              {creatingSession ? 'Creating...' : 'New Session'}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {openSessions.map(openSession => (
              <div key={openSession.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="text-base font-bold text-slate-900 truncate">
                      {openSession.number ?? `Session #${openSession.id}`}
                    </h2>
                    <p className="text-sm text-slate-500 mt-1">{openSession.doc_date ?? today()}</p>
                  </div>
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-bold uppercase shrink-0">
                    {openSession.mode ?? 'sales'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => navigate(`/pot/sessions/${openSession.id}/pos`)}
                  className="mt-5 w-full px-4 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors"
                >
                  Open
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    )
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
            onClick={() => navigate('/pot/sessions')}
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
              <button type="button" onClick={() => { setPosMode('sales'); setCart([]); setIsCreditMode(false) }}
                className={`px-3 py-1 transition-colors ${posMode === 'sales' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}>
                Sales
              </button>
              <button type="button" onClick={() => { setPosMode('purchase'); setCart([]); setIsCreditMode(false) }}
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
        <div className="p-6 flex flex-col min-h-0 border-r border-slate-200 print:hidden">
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

          {receipt ? (
            <div className="p-6 border-t border-slate-200 space-y-4 shrink-0 bg-white print:block">
              <div className="text-center mb-6">
                <h3 className="text-xl font-black text-slate-900">{receipt.invoice_number ?? `#${receipt.invoice_id}`}</h3>
                <p className="text-xs text-slate-500 uppercase tracking-wider mt-1">Receipt</p>
              </div>
              <div className="space-y-3">
                {receipt.items.map(line => (
                  <div key={line.item.id} className="flex items-center justify-between text-sm">
                    <div>
                      <div className="font-semibold text-slate-900">{line.item.name}</div>
                      <div className="text-xs text-slate-500">{line.qty} × {formatCurrency(getItemPrice(line.item))}</div>
                    </div>
                    <div className="font-bold text-slate-900">{formatCurrency(getItemPrice(line.item) * line.qty)}</div>
                  </div>
                ))}
              </div>
              <div className="border-t border-slate-200 pt-3 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500 font-medium">Subtotal</span>
                  <span className="text-lg font-bold text-slate-900">{formatCurrency(receipt.items.reduce((s, l) => s + getItemPrice(l.item) * l.qty, 0))}</span>
                </div>
                {receipt.isCredit ? (
                  <div className="mt-4 inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 uppercase tracking-wider">
                    Credit — {receipt.mode === 'sales' ? 'AR' : 'AP'} created
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 font-medium">Paid</span>
                      <span className="font-bold text-slate-900">{formatCurrency(receipt.paid)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 font-medium">Change</span>
                      <span className="font-bold text-slate-900">{formatCurrency(receipt.change)}</span>
                    </div>
                  </>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2 mt-6 pt-4 print:hidden">
                <button type="button" onClick={() => window.print()} className="px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm font-bold hover:bg-slate-50 transition-colors">Print</button>
                <button type="button" onClick={() => { setReceipt(null); clearCart() }} className="px-4 py-3 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-colors">New Transaction</button>
              </div>
            </div>
          ) : (
          <div className="p-6 border-t border-slate-200 space-y-4 shrink-0 print:hidden">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500 font-medium">Subtotal</span>
              <span className="text-lg font-bold text-slate-900">{formatCurrency(subtotal)}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Credit {posMode === 'sales' ? 'Sale' : 'Purchase'}
              </span>
              <button
                type="button"
                onClick={() => {
                  const next = !isCreditMode
                  setIsCreditMode(next)
                  if (next) { setPaymentModeId(null); setAmountPaid('') }
                }}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  isCreditMode
                    ? posMode === 'sales' ? 'bg-amber-500' : 'bg-purple-500'
                    : 'bg-slate-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                  isCreditMode ? 'translate-x-[18px]' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            <div className={`space-y-3 ${isCreditMode ? 'opacity-40 pointer-events-none select-none' : ''}`}>
              <label className="block">
                <span className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Party</span>
                <Combobox
                  resource="party/parties"
                  value={partyId}
                  onChange={(value) => setPartyId(typeof value === 'number' ? value : value ? Number(value) : null)}
                  placeholder="Optional party"
                />
              </label>
              <label className="block">
                <span className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Mode</span>
                <Combobox
                  resource="config/payment-modes"
                  value={paymentModeId}
                  onChange={(value) => setPaymentModeId(typeof value === 'number' ? value : value ? Number(value) : null)}
                  placeholder="Payment mode"
                />
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

            {isCreditMode ? (
              <div className="flex items-center justify-between text-sm">
                <span className={`font-medium ${posMode === 'sales' ? 'text-amber-600' : 'text-purple-600'}`}>
                  {posMode === 'sales' ? 'AR Outstanding' : 'AP Outstanding'}
                </span>
                <span className={`font-bold ${posMode === 'sales' ? 'text-amber-700' : 'text-purple-700'}`}>
                  {formatCurrency(subtotal)}
                </span>
              </div>
            ) : (
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500 font-medium">Change</span>
                <span className="font-bold text-slate-900">{formatCurrency(change)}</span>
              </div>
            )}

            <div className="grid grid-cols-[1fr_auto] gap-2">
              <button
                type="button"
                onClick={charge}
                disabled={charging || cart.length === 0 || (!isCreditMode && !paymentModeId)}
                className={`h-12 rounded-xl text-white text-sm font-bold uppercase tracking-wider disabled:opacity-60 transition-colors ${
                  isCreditMode
                    ? posMode === 'sales'
                      ? 'bg-amber-500 hover:bg-amber-600 disabled:hover:bg-amber-500'
                      : 'bg-purple-600 hover:bg-purple-700 disabled:hover:bg-purple-600'
                    : 'bg-indigo-600 hover:bg-indigo-700 disabled:hover:bg-indigo-600'
                }`}
              >
                {charging
                  ? 'Charging...'
                  : isCreditMode
                    ? posMode === 'sales' ? 'Credit Sale' : 'Credit Purchase'
                    : 'Charge'}
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
          )}
        </aside>
      </div>
    </div>
  )
}
