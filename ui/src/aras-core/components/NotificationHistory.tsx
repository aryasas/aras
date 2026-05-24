import React, { useState, useRef, useEffect } from 'react';
import { Bell, Trash2 } from 'lucide-react';
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
      case 'info': return 'bg-[color-mix(in_srgb,var(--aras-accent)_10%,transparent)] text-[var(--aras-accent)]';
      default: return 'bg-[var(--aras-panel-soft)] text-[var(--aras-text)]';
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative flex items-center justify-center w-10 h-10 bg-[var(--aras-panel)] rounded-[var(--aras-radius)] shadow-sm border border-[var(--aras-border)] text-[var(--aras-muted)] hover:text-[var(--aras-accent)] hover:border-[var(--aras-accent)] transition-all"
        title="Notifications"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 inline-flex w-3 h-3 bg-red-500 rounded-full border-2 border-[var(--aras-panel)]"></span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 bg-[var(--aras-panel)] border border-[var(--aras-border)] shadow-xl rounded-[var(--aras-radius-lg)] z-50 p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-bold text-[var(--aras-text)]">Notifications</h4>
            <button
              onClick={clearHistory}
              className="flex items-center gap-1 text-xs text-[var(--aras-muted)] hover:text-[var(--aras-text)] disabled:opacity-50"
              disabled={history.length === 0}
            >
              <Trash2 size={14} /> Clear All
            </button>
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
            {history.length === 0 ? (
              <p className="text-sm text-[var(--aras-muted)] italic">No notifications yet.</p>
            ) : (
              history.slice().reverse().map((notification) => ( // Reverse to show newest first
                <div key={notification.id} className={`p-3 rounded-[var(--aras-radius)] ${getTypeClasses(notification.type)}`}>
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
