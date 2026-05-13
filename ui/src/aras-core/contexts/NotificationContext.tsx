import React, { createContext, useContext, useState, useCallback } from 'react'

type NotificationType = 'success' | 'error' | 'info' | 'warning'

interface Notification {
  id: string
  message: string
  type: NotificationType
}

interface NotificationContextType {
  notifications: Notification[]
  notify: (message: string, type?: NotificationType) => void
  removeNotification: (id: string) => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const notify = useCallback((message: string, type: NotificationType = 'info') => {
    const id = Math.random().toString(36).substr(2, 9)
    setNotifications((prev) => [...prev, { id, message, type }])
    setTimeout(() => removeNotification(id), 5000)
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  return (
    <NotificationContext.Provider value={{ notifications, notify, removeNotification }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {notifications.map((n) => (
          <div 
            key={n.id} 
            className={`px-6 py-4 rounded-2xl shadow-xl text-white font-bold animate-in slide-in-from-right-full ${
              n.type === 'success' ? 'bg-emerald-500' : 
              n.type === 'error' ? 'bg-rose-500' : 
              n.type === 'warning' ? 'bg-amber-500' : 'bg-indigo-500'
            }`}
          >
            {n.message}
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  )
}

export const useNotify = () => {
  const context = useContext(NotificationContext)
  if (!context) throw new Error('useNotify must be used within a NotificationProvider')
  return context.notify
}
