import React from 'react';
import { useUIStore } from '../store/uiStore';

export const PageHeader: React.FC = () => {
  const { pageTitle, pageSubtitle, breadcrumbs } = useUIStore();

  if (!pageTitle) return null;

  return (
    <div className="mb-8 flex items-end justify-between gap-6 max-sm:flex-col max-sm:items-start animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="min-w-0 flex-1">
        {breadcrumbs && (
          <div className="mb-2 text-[12px] text-[var(--aras-muted)] tracking-wider uppercase opacity-70 truncate">
            {breadcrumbs}
          </div>
        )}
        <h1 className="m-0 text-[36px] leading-none tracking-[-0.045em] font-normal text-[var(--aras-text)] max-sm:text-2xl truncate">
          {pageTitle}
        </h1>
        {pageSubtitle && (
          <p className="mt-2 text-[13px] text-[var(--aras-muted)] max-w-3xl">
            {pageSubtitle}
          </p>
        )}
      </div>
    </div>
  );
};
