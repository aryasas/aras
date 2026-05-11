import React, { useState, useMemo, useEffect } from 'react'

export default function PosSessionPage({ config }) {
  const { 
    session, 
    products: initialProducts, 
    customers, 
    suppliers, 
    currency_symbol, 
    tax_rate: TAX_RATE, 
    tax_inclusive: TAX_INCLUSIVE,
    selling_pricelist_id: SELLING_PRICELIST_ID,
    purchase_pricelist_id: PURCHASE_PRICELIST_ID,
    csrf_token: CSRF
  } = config

  const [mode, setMode] = useState('in')
  const [customerSearch, setCustomerSearch] = useState('')
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false)
  const [supplierSearch, setSupplierSearch] = useState('')
  const [showSupplierDropdown, setShowSupplierDropdown] = useState(false)
  const [productSearch, setProductSearch] = useState('')
  const [cart, setCart] = useState([])
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [paymentStep, setPaymentStep] = useState('payment')
  const [payments, setPayments] = useState([])
  const [newMethod, setNewMethod] = useState('cash')
  const [newAmount, setNewAmount] = useState(0)
  const [lastInvoiceId, setLastInvoiceId] = useState(null)

  const taxRatePercent = useMemo(() => TAX_RATE * 100, [TAX_RATE])

  const filteredCustomers = useMemo(() => {
    if (!customerSearch) return customers
    return customers.filter(c => c.name.toLowerCase().includes(customerSearch.toLowerCase()))
  }, [customerSearch, customers])

  const filteredSuppliers = useMemo(() => {
    if (!supplierSearch) return suppliers
    return suppliers.filter(s => s.name.toLowerCase().includes(supplierSearch.toLowerCase()))
  }, [supplierSearch, suppliers])

  const filteredProducts = useMemo(() => {
    if (!productSearch) return initialProducts
    return initialProducts.filter(p => p.name.toLowerCase().includes(productSearch.toLowerCase()))
  }, [productSearch, initialProducts])

  const grandTotal = useMemo(() => 
    cart.reduce((s, i) => s + i.price * i.qty, 0), 
  [cart])

  const taxTotal = useMemo(() => {
    if (!TAX_INCLUSIVE || TAX_RATE <= 0) return 0
    return grandTotal - grandTotal / (1 + TAX_RATE)
  }, [grandTotal, TAX_INCLUSIVE, TAX_RATE])

  const netSubtotal = useMemo(() => grandTotal - taxTotal, [grandTotal, taxTotal])

  const totalPaid = useMemo(() => payments.reduce((s, p) => s + p.amount, 0), [payments])
  const remaining = useMemo(() => grandTotal - totalPaid, [grandTotal, totalPaid])
  const hasCredit = useMemo(() => payments.some(p => p.method === 'credit'), [payments])

  const fetchPrice = async (productId, qty, mode) => {
    const plId = mode === 'in' ? SELLING_PRICELIST_ID : PURCHASE_PRICELIST_ID
    const priceType = mode === 'in' ? 'sales' : 'purchase'
    if (!plId) return null
    try {
      const r = await fetch(`/api/erp/acc/product_lookup/product_price?product_id=${productId}&price_type_id=${plId}&qty=${qty}&price_type=${priceType}`)
      const d = await r.json()
      return (d.ok && d.unit_price != null) ? d.unit_price : null
    } catch { return null }
  }

  const addToCart = async (prod) => {
    const basePrice = mode === 'in' ? prod.sales_price : prod.purchase_price
    const existingIndex = cart.findIndex(i => i.id === prod.id)
    
    let newCart = [...cart]
    if (existingIndex > -1) {
      newCart[existingIndex].qty++
      const p = await fetchPrice(prod.id, newCart[existingIndex].qty, mode)
      if (p !== null) newCart[existingIndex].price = p
    } else {
      const item = { ...prod, qty: 1, price: basePrice }
      newCart.push(item)
      const p = await fetchPrice(prod.id, 1, mode)
      if (p !== null) {
        newCart[newCart.length - 1].price = p
      }
    }
    setCart(newCart)
  }

  const updateQty = async (item, delta) => {
    let newCart = cart.map(i => i.id === item.id ? { ...i, qty: i.qty + delta } : i).filter(i => i.qty > 0)
    
    const updatedItem = newCart.find(i => i.id === item.id)
    if (updatedItem) {
      const p = await fetchPrice(updatedItem.id, updatedItem.qty, mode)
      if (p !== null) {
        updatedItem.price = p
      }
    }
    setCart(newCart)
  }

  const addPayment = () => {
    if (!newAmount || newAmount <= 0) return
    setPayments([...payments, { method: newMethod, amount: parseFloat(newAmount) }])
    setNewAmount(Math.max(0, remaining - newAmount))
  }

  const removePayment = (index) => {
    const newPayments = [...payments]
    newPayments.splice(index, 1)
    setPayments(newPayments)
  }

  const confirmPayment = async () => {
    if (payments.length === 0) return

    const custMatch = customers.find(c => c.name === customerSearch)
    const selectedCustId = custMatch ? custMatch.id : null
    const suppMatch = suppliers.find(s => s.name === supplierSearch)
    const selectedSuppId = suppMatch ? suppMatch.id : null

    const lines = cart.map(i => {
      const lineTotal = i.price * i.qty
      const lineTax = TAX_INCLUSIVE && TAX_RATE > 0
        ? lineTotal - lineTotal / (1 + TAX_RATE) : 0
      return {
        product_id: i.id, qty: i.qty, uom_id: i.uom_id || null,
        unit_price: i.price, subtotal: lineTotal, tax_amt: lineTax,
      }
    })

    const creditBalance = Math.max(0, grandTotal - totalPaid)
    const payloadsToSend = payments.filter(p => p.method !== 'credit')
    if (creditBalance > 0.001) {
      payloadsToSend.push({ method: 'credit', amount: creditBalance })
    }

    try {
      const res = await fetch(`/api/erp/pos/session/${session.id}/order/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        body: JSON.stringify({ lines, payments: payloadsToSend, customer_id: selectedCustId, supplier_id: selectedSuppId, ui_mode: mode })
      })
      const data = await res.json()
      if (data.ok) {
        setLastInvoiceId(data.invoice_id)
        setPaymentStep('success')
      } else {
        alert('Error: ' + data.error)
      }
    } catch (e) {
      alert('Network Error: ' + e.message)
    }
  }

  const newTransaction = () => {
    setCart([])
    setCustomerSearch('')
    setSupplierSearch('')
    setPayments([])
    setShowPaymentModal(false)
    setPaymentStep('payment')
  }

  return (
    <div className="flex h-[calc(100vh-100px)] bg-aras-bg overflow-hidden animate-fade-in -m-8">
      {/* LEFT SIDEBAR: CART */}
      <div className="w-96 flex flex-col bg-white border-r border-[#dde3e7] shadow-sm">
        <div className="p-6 border-b border-[#dde3e7] flex items-center justify-between">
           <a href="/admin/erp/pos/" className="w-8 h-8 flex items-center justify-center rounded-full bg-[#faf8f3] text-[#9aacb8] hover:text-aras-accent transition-colors">
              <i className="fa fa-arrow-left text-xs"></i>
           </a>
           <div className="flex bg-[#faf8f3] p-1 rounded-full border border-[#dde3e7] relative w-32 h-10">
              <div 
                className={`absolute top-1 bottom-1 w-[60px] bg-aras-accent rounded-full transition-all duration-300 ${mode === 'in' ? 'left-1' : 'left-[65px]'}`}
              ></div>
              <button 
                onClick={() => setMode('in')}
                className={`flex-1 relative z-10 text-[10px] font-bold uppercase tracking-widest transition-colors ${mode === 'in' ? 'text-white' : 'text-[#9aacb8]'}`}
              >
                IN
              </button>
              <button 
                onClick={() => setMode('out')}
                className={`flex-1 relative z-10 text-[10px] font-bold uppercase tracking-widest transition-colors ${mode === 'out' ? 'text-white' : 'text-[#9aacb8]'}`}
              >
                OUT
              </button>
           </div>
        </div>

        {/* CUSTOMER/SUPPLIER SELECTOR */}
        <div className="p-6 border-b border-[#f4f2ee] relative">
           <div className="text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-2">
              {mode === 'in' ? 'Customer' : 'Supplier'}
           </div>
           <div className="relative">
              <input 
                type="text" 
                value={mode === 'in' ? customerSearch : supplierSearch}
                onChange={e => mode === 'in' ? setCustomerSearch(e.target.value) : setSupplierSearch(e.target.value)}
                onFocus={() => mode === 'in' ? setShowCustomerDropdown(true) : setShowSupplierDropdown(true)}
                placeholder={`Select ${mode === 'in' ? 'Customer' : 'Supplier'}...`}
                className="w-full px-4 py-3 bg-[#faf8f3] border border-[#dde3e7] rounded text-sm focus:ring-1 focus:ring-aras-accent outline-none"
              />
              {(mode === 'in' ? showCustomerDropdown : showSupplierDropdown) && (
                <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-white border border-[#dde3e7] shadow-xl max-h-60 overflow-y-auto">
                   {(mode === 'in' ? filteredCustomers : filteredSuppliers).map(item => (
                     <button 
                      key={item.id}
                      onClick={() => {
                        if (mode === 'in') {
                          setCustomerSearch(item.name)
                          setShowCustomerDropdown(false)
                        } else {
                          setSupplierSearch(item.name)
                          setShowSupplierDropdown(false)
                        }
                      }}
                      className="w-full text-left px-4 py-3 hover:bg-[#faf8f3] text-sm border-b border-[#f4f2ee] last:border-0"
                     >
                        {item.name}
                     </button>
                   ))}
                </div>
              )}
           </div>
        </div>

        {/* CART ITEMS */}
        <div className="flex-1 overflow-y-auto p-0 divide-y divide-[#f4f2ee]">
           {cart.map(item => (
             <div key={item.id} className="p-6 hover:bg-[#faf8f3]/50 transition-colors group">
                <div className="flex justify-between items-start mb-4">
                   <div className="flex-1">
                      <h4 className="text-sm font-bold text-aras-primary mb-1">{item.name}</h4>
                      <div className="text-[11px] text-[#9aacb8] font-mono">
                        {currency_symbol} {item.price.toLocaleString()}
                        {TAX_INCLUSIVE && <span className="ml-2 text-[9px] uppercase tracking-tighter opacity-50">(incl. tax)</span>}
                      </div>
                   </div>
                   <div className="text-sm font-bold text-aras-primary">
                      {currency_symbol} {(item.price * item.qty).toLocaleString()}
                   </div>
                </div>
                <div className="flex items-center gap-3">
                   <button 
                    onClick={() => updateQty(item, -1)}
                    className="w-8 h-8 flex items-center justify-center border border-[#dde3e7] rounded hover:bg-white text-[#9aacb8] hover:text-red-500 transition-colors"
                   >
                     <i className="fa fa-minus text-[10px]"></i>
                   </button>
                   <span className="w-8 text-center font-bold text-aras-primary">{item.qty}</span>
                   <button 
                    onClick={() => updateQty(item, 1)}
                    className="w-8 h-8 flex items-center justify-center border border-[#dde3e7] rounded hover:bg-white text-[#9aacb8] hover:text-aras-accent transition-colors"
                   >
                     <i className="fa fa-plus text-[10px]"></i>
                   </button>
                </div>
             </div>
           ))}
           {cart.length === 0 && (
             <div className="p-12 text-center">
                <div className="w-16 h-16 bg-[#faf8f3] rounded-full flex items-center justify-center text-[#dde3e7] mx-auto mb-4">
                   <i className="fa fa-shopping-basket text-3xl"></i>
                </div>
                <p className="text-[#9aacb8] font-studio-serif italic text-sm">Basket is empty</p>
             </div>
           )}
        </div>

        {/* CART FOOTER */}
        <div className="p-8 border-t border-[#dde3e7] bg-[#faf8f3]">
           {TAX_INCLUSIVE && taxTotal > 0 && (
              <div className="mb-4 space-y-1">
                 <div className="flex justify-between text-[11px] text-[#9aacb8]">
                    <span>Net Subtotal</span>
                    <span>{currency_symbol} {netSubtotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                 </div>
                 <div className="flex justify-between text-[11px] text-[#9aacb8]">
                    <span>Tax ({taxRatePercent}%)</span>
                    <span>{currency_symbol} {taxTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                 </div>
              </div>
           )}
           <div className="flex justify-between items-baseline mb-8">
              <span className="text-[10px] font-bold text-aras-primary uppercase tracking-[0.2em]">Total</span>
              <span className="text-3xl font-studio-serif font-bold text-aras-primary tracking-tighter">
                {currency_symbol} {grandTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
           </div>
           <button 
            onClick={() => {
              if (cart.length === 0) return
              const partner = mode === 'in' ? customerSearch : supplierSearch
              if (!partner) {
                alert(`Please select a ${mode === 'in' ? 'customer' : 'supplier'}`)
                return
              }
              setPayments([])
              setNewAmount(grandTotal)
              setPaymentStep('payment')
              setShowPaymentModal(true)
            }}
            disabled={cart.length === 0}
            className="w-full py-4 bg-aras-accent text-white font-bold uppercase tracking-[0.2em] rounded shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:translate-y-0 disabled:shadow-none"
           >
             <i className="fa fa-bolt mr-2"></i> {mode === 'in' ? 'Charge' : 'Pay'}
           </button>
        </div>
      </div>

      {/* RIGHT MAIN: PRODUCTS */}
      <div className="flex-1 flex flex-col bg-[#faf8f3] p-12">
        <div className="flex items-center justify-between mb-12">
           <div className="relative w-96">
              <i className="fa fa-search absolute left-4 top-1/2 -translate-y-1/2 text-aras-accent"></i>
              <input 
                type="text" 
                placeholder="Search products..." 
                value={productSearch}
                onChange={e => setProductSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-white border border-[#dde3e7] rounded-md shadow-sm outline-none focus:ring-2 focus:ring-aras-accent/10"
              />
           </div>
           <div className="text-2xl font-studio-serif font-bold text-aras-primary tracking-tight">
              Aras<span className="text-aras-accent">POS</span>
           </div>
        </div>

        <div className="flex-1 overflow-y-auto grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6 gap-6">
           {filteredProducts.map(prod => (
             <button 
              key={prod.id}
              onClick={() => addToCart(prod)}
              className="group bg-white border border-[#dde3e7] p-6 rounded-md shadow-sm hover:border-aras-accent hover:-translate-y-1 transition-all flex flex-col items-center text-center"
             >
                <div className="w-full aspect-square bg-[#f4f2ee] rounded mb-6 flex items-center justify-center text-[#dde3e7] overflow-hidden relative">
                   <div className="absolute inset-0 bg-gradient-to-br from-aras-accent/20 to-aras-accent/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                   <i className="fa fa-cube text-4xl opacity-20"></i>
                </div>
                <h5 className="text-[13px] font-bold text-aras-primary mb-2 line-clamp-2">{prod.name}</h5>
                <div className="mt-auto text-aras-accent font-bold">
                   {currency_symbol} {(mode === 'in' ? prod.sales_price : prod.purchase_price).toLocaleString()}
                </div>
             </button>
           ))}
        </div>
      </div>

      {/* PAYMENT MODAL */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-aras-primary/20 backdrop-blur-sm animate-fade-in">
           <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col md:flex-row min-h-[500px]">
              {paymentStep === 'payment' ? (
                <>
                  <div className="w-full md:w-1/2 p-10 border-r border-[#f4f2ee]">
                     <h3 className="text-xl font-studio-serif font-bold text-aras-primary mb-8 border-b border-[#f4f2ee] pb-4">Order Summary</h3>
                     <div className="space-y-4 mb-8 max-h-60 overflow-y-auto pr-4">
                        {cart.map(item => (
                          <div key={item.id} className="flex justify-between text-sm">
                             <span className="text-[#9aacb8]">{item.qty}x {item.name}</span>
                             <span className="font-bold text-aras-primary">{currency_symbol} {(item.price * item.qty).toLocaleString()}</span>
                          </div>
                        ))}
                     </div>
                     <div className="pt-6 border-t border-[#f4f2ee] space-y-3">
                        <div className="flex justify-between text-xl font-studio-serif font-bold text-aras-primary">
                           <span>Total</span>
                           <span className="text-aras-accent">{currency_symbol} {grandTotal.toLocaleString()}</span>
                        </div>
                        {payments.length > 0 && (
                          <div className="space-y-2 mt-6 pt-6 border-t border-[#f4f2ee]">
                             <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-2">Payments Applied</span>
                             {payments.map((p, i) => (
                               <div key={i} className="flex justify-between items-center text-sm py-1 bg-[#faf8f3] px-3 rounded border border-[#dde3e7]">
                                  <span className="uppercase text-[10px] font-bold">{p.method}</span>
                                  <div className="flex items-center gap-3">
                                     <span className="font-mono">{currency_symbol} {p.amount.toLocaleString()}</span>
                                     <button onClick={() => removePayment(i)} className="text-red-400 hover:text-red-600"><i className="fa fa-times"></i></button>
                                  </div>
                               </div>
                             ))}
                             <div className={`mt-4 pt-4 border-t border-[#dde3e7] flex justify-between font-bold ${remaining <= 0.001 ? 'text-green-600' : 'text-aras-accent'}`}>
                                <span>Remaining</span>
                                <span>{currency_symbol} {Math.max(0, remaining).toLocaleString()}</span>
                             </div>
                          </div>
                        )}
                     </div>
                  </div>
                  <div className="w-full md:w-1/2 p-10 bg-[#faf8f3]">
                     <h3 className="text-xl font-studio-serif font-bold text-aras-primary mb-8 border-b border-[#dde3e7] pb-4">Add Payment</h3>
                     <div className="grid grid-cols-2 gap-3 mb-8">
                        {['cash', 'qris', 'transfer', 'card', 'credit'].map(m => (
                          <button 
                            key={m}
                            onClick={() => {
                              setNewMethod(m)
                              setNewAmount(Math.max(0, remaining))
                            }}
                            className={`p-4 border rounded-md text-center transition-all ${newMethod === m ? 'bg-aras-accent border-aras-accent text-white shadow-md' : 'bg-white border-[#dde3e7] text-[#9aacb8] hover:border-aras-accent'}`}
                          >
                             <div className="text-[10px] font-bold uppercase tracking-widest">{m}</div>
                          </button>
                        ))}
                     </div>
                     <div className="mb-8">
                        <label className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-3">Payment Amount</label>
                        <div className="relative">
                           <span className="absolute left-4 top-1/2 -translate-y-1/2 font-mono text-xl text-[#9aacb8]">{currency_symbol}</span>
                           <input 
                            type="number" 
                            value={newAmount}
                            onChange={e => setNewAmount(e.target.value)}
                            className="w-full pl-12 pr-4 py-4 bg-white border border-[#dde3e7] rounded text-2xl font-bold text-aras-primary outline-none focus:ring-2 focus:ring-aras-accent/20"
                           />
                        </div>
                     </div>
                     <button 
                      onClick={addPayment}
                      className="w-full py-4 bg-white border border-aras-accent text-aras-accent font-bold uppercase tracking-widest rounded mb-8 hover:bg-aras-accent/5"
                     >
                        Add {newMethod.toUpperCase()}
                     </button>
                     <div className="pt-8 border-t border-[#dde3e7]">
                        <button 
                          onClick={confirmPayment}
                          disabled={payments.length === 0 || (remaining > 0.001 && !hasCredit)}
                          className="w-full py-5 bg-aras-accent text-white font-bold uppercase tracking-[0.2em] rounded shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all disabled:opacity-50 disabled:translate-y-0"
                        >
                          Confirm & Post
                        </button>
                        <button 
                          onClick={() => setShowPaymentModal(false)}
                          className="w-full mt-4 text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest hover:text-aras-primary"
                        >
                          Cancel
                        </button>
                     </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 p-20 flex flex-col items-center justify-center text-center space-y-8 animate-fade-in">
                   <div className="w-24 h-24 bg-green-50 text-green-500 rounded-full flex items-center justify-center border-4 border-green-100 shadow-inner">
                      <i className="fa fa-check text-4xl"></i>
                   </div>
                   <div>
                      <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">Transaction Successful!</h3>
                      <p className="text-[#9aacb8] font-studio-serif italic">The order has been recorded and inventory updated.</p>
                   </div>
                   <div className="grid grid-cols-2 gap-4 w-full max-w-md">
                      <button className="py-4 bg-[#faf8f3] border border-[#dde3e7] rounded text-[11px] font-bold uppercase tracking-widest hover:border-aras-accent transition-colors">
                        <i className="fa fa-print mr-2 text-aras-accent"></i> Print Receipt
                      </button>
                      <button className="py-4 bg-[#faf8f3] border border-[#dde3e7] rounded text-[11px] font-bold uppercase tracking-widest hover:border-aras-accent transition-colors">
                        <i className="fa fa-file-pdf-o mr-2 text-aras-accent"></i> Export PDF
                      </button>
                   </div>
                   <button 
                    onClick={newTransaction}
                    className="w-full max-w-md py-5 bg-aras-accent text-white font-bold uppercase tracking-[0.2em] rounded shadow-xl"
                   >
                      Next Transaction
                   </button>
                </div>
              )}
           </div>
        </div>
      )}
    </div>
  )
}
