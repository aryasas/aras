// claude-sonnet-4-6
export const MODULE_LABELS: Record<string, string> = {
  pos: 'POS',
  stock: 'Stok',
  receivable: 'Hutang Piutang',
  accounting: 'Accounting',
}

export function formatPrice(price: number): string {
  if (price === 0) return 'Gratis'
  return `Rp ${price.toLocaleString('id-ID')}/bulan`
}
