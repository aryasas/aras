import { useNotify } from '../contexts/NotificationContext'
import { useConfirm } from '../contexts/ConfirmContext'
import api from '../../lib/api'

export const useAras = () => {
  const notify = useNotify()
  const confirm = useConfirm()

  return {
    notify,
    confirm,
    api,
    // Add other helpers here
    formatDate: (date: string) => new Date(date).toLocaleDateString(),
    formatCurrency: (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
  }
}
