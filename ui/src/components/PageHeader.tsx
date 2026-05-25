import React from 'react';
import { useUIStore } from '../store/uiStore';

export const PageHeader: React.FC = () => {
  const { pageTitle, pageSubtitle, breadcrumbs } = useUIStore();

  if (!pageTitle) return null;

  return (
    <div className="min-w-0 flex-1 animate-in fade-in slide-in-from-top-4 duration-500">
      {breadcrumbs && (
        <div className="mb-1 text-[10px] md:text-[11px] font-extrabold text-[var(--app-muted)] tracking-wider uppercase opacity-80 truncate leading-none">
          {breadcrumbs}
        </div>
      )}
      <h1 className="m-0 text-3xl md:text-4xl font-extrabold text-[var(--app-text)] leading-tight truncate tracking-tight">
        {pageTitle}
      </h1>
      {pageSubtitle && (
        <p className="mt-1 text-[11px] md:text-xs font-bold text-[var(--app-muted)] max-w-3xl truncate hidden sm:block">
          {pageSubtitle}
        </p>
      )}
    </div>
  );
};
