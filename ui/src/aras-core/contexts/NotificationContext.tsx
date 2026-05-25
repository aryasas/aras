import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

type NotificationType = 'success' | 'error' | 'info' | 'warning'

export interface Notification { // Exported for NotificationHistory component
  id: string
  message: string
  type: NotificationType
  timestamp: number // Add timestamp for sorting/filtering
}

interface NotificationContextType {
  notifications: Notification[]
  history: Notification[] // Added history
  notify: (message: string, type?: NotificationType) => void
  removeNotification: (id: string) => void
  clearHistory: () => void; // Added clearHistory
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

const LOCAL_STORAGE_KEY = 'aras.notifications';
const HISTORY_LIMIT = 50;

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [history, setHistory] = useState<Notification[]>(() => {
    try {
      const storedHistory = localStorage.getItem(LOCAL_STORAGE_KEY);
      return storedHistory ? JSON.parse(storedHistory) : [];
    } catch (error) {
      console.error("Failed to parse notifications from localStorage", error);
      return [];
    }
  });

  // Persist history to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(history.slice(-HISTORY_LIMIT))); // Keep only last 50
    } catch (error) {
      console.error("Failed to save notifications to localStorage", error);
    }
  }, [history]);


  const notify = useCallback((message: string, type: NotificationType = 'info') => {
    const id = Math.random().toString(36).substr(2, 9)
    const newNotification: Notification = { id, message, type, timestamp: Date.now() };

    setNotifications((prev) => [...prev, newNotification])
    setHistory((prev) => [...prev, newNotification].slice(-HISTORY_LIMIT)); // Add to history, limit size

    setTimeout(() => removeNotification(id), 5000)
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  return (
    <NotificationContext.Provider value={{ notifications, history, notify, removeNotification, clearHistory }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {notifications.map((n) => (
          <div 
            key={n.id} 
            className={`px-6 py-4 rounded-[var(--app-radius-lg)] shadow-[var(--shadow-premium)] text-white font-extrabold animate-in slide-in-from-right-full ${
              n.type === 'success' ? 'bg-emerald-500 shadow-emerald-500/20' : 
              n.type === 'error' ? 'bg-rose-500 shadow-rose-500/20' : 
              n.type === 'warning' ? 'bg-amber-500 shadow-amber-500/20' : 'bg-[var(--app-primary-action)] shadow-[var(--app-accent-glow)]'
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

export const useNotificationHistory = () => {
  const context = useContext(NotificationContext)
  if (!context) throw new Error('useNotificationHistory must be used within a NotificationProvider')
  return { history: context.history, clearHistory: context.clearHistory }
}

