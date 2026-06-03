// claude-sonnet-4-6
import { formatCurrency } from './formatters'

export const MODULE_LABELS: Record<string, string> = {
  pos: 'POS',
  stock: 'Stok',
  receivable: 'Hutang Piutang',
  accounting: 'Accounting',
}

export function formatPrice(price: number, currency?: string): string {
  if (price === 0) return 'Gratis'
  return formatCurrency(price, currency)
}
