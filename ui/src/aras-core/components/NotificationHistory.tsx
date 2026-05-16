import React, { useState, useRef, useEffect } from 'react';
import { Bell, X, Trash2 } from 'lucide-react';
import { useNotificationHistory } from '../contexts/NotificationContext';

const NotificationHistory: React.FC = () => {
  const { history, clearHistory } = useNotificationHistory();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const unreadCount = history.length; // For simplicity, all are "unread" until cleared or dropdown is opened

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleString(); // Or use a more specific format if desired
  };

  const getTypeClasses = (type: string) => {
    switch (type) {
      case 'success': return 'bg-emerald-50 text-emerald-700';
      case 'error': return 'bg-rose-50 text-rose-700';
      case 'warning': return 'bg-amber-50 text-amber-700';
      case 'info': return 'bg-indigo-50 text-indigo-700';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl text-slate-600 hover:bg-slate-50 transition-colors"
        title="Notifications"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 bg-white border border-slate-200 shadow-xl rounded-2xl z-50 p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-bold text-slate-800">Notifications</h4>
            <button
              onClick={clearHistory}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 disabled:opacity-50"
              disabled={history.length === 0}
            >
              <Trash2 size={14} /> Clear All
            </button>
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
            {history.length === 0 ? (
              <p className="text-sm text-slate-400 italic">No notifications yet.</p>
            ) : (
              history.slice().reverse().map((notification) => ( // Reverse to show newest first
                <div key={notification.id} className={`p-3 rounded-lg ${getTypeClasses(notification.type)}`}>
                  <p className="text-sm font-medium">{notification.message}</p>
                  <p className="text-xs text-opacity-75 mt-1">{formatTimestamp(notification.timestamp)}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationHistory;
