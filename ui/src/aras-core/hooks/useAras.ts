import { useLocation } from 'react-router-dom'
import { useNotify } from '../contexts/NotificationContext'
import { useConfirm } from '../contexts/ConfirmContext'
import api from '../../lib/api'

export const useAras = () => {
  const notify = useNotify()
  const confirm = useConfirm()
  const location = useLocation()
  const appName = location.pathname.split('/').filter(Boolean)[0] ?? null

  return {
    notify,
    confirm,
    api,
    appName,
    formatDate: (date: string) => new Date(date).toLocaleDateString(),
    formatCurrency: (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
  }
}
