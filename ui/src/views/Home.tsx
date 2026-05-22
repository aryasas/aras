import { useEffect } from 'react'
import { DashboardView } from './DashboardView'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'

export default function HomeView() {
  const user = useAuthStore((state) => state.user)
  const setPageTitle = useUIStore(state => state.setPageTitle)

  const displayName = user?.full_name || user?.username || 'there'

  useEffect(() => {
    setPageTitle(`Welcome back, ${displayName}`, "Here's what's happening in your workspace today.", "HOME")
    return () => setPageTitle('', '', '')
  }, [displayName, setPageTitle])

  return (
    <>
      <DashboardView />
    </>
  )
}
