import React from 'react';
import { useUIStore } from '../store/uiStore';

export const PageHeader: React.FC = () => {
  const { pageTitle, pageSubtitle, breadcrumbs } = useUIStore();

  if (!pageTitle) return null;

  return (
    <div className="min-w-0 flex-1 animate-in fade-in slide-in-from-top-4 duration-500">
      {breadcrumbs && (
        <div className="mb-0.5 text-[10px] md:text-[11px] font-bold text-[var(--aras-muted)] tracking-wider uppercase opacity-70 truncate leading-none">
          {breadcrumbs}
        </div>
      )}
      <h1 className="m-0 text-lg md:text-2xl font-bold text-[var(--aras-text)] leading-none truncate">
        {pageTitle}
      </h1>
      {pageSubtitle && (
        <p className="mt-1 text-[10px] md:text-xs font-medium text-[var(--aras-muted)] max-w-3xl truncate hidden sm:block">
          {pageSubtitle}
        </p>
      )}
    </div>
  );
};
