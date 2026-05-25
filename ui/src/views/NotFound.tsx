// claude-opus-4-7
import React from 'react';
import { useAras } from '../aras-core/hooks/useAras';
import { useNavigate } from 'react-router-dom';

const NotFound: React.FC = () => {
  const { appName } = useAras();
  const navigate = useNavigate();

  return (
    <div className="arc arc-dotgrid flex flex-col items-center justify-center min-h-[calc(100vh-200px)] p-8">
      <div className="arc-card px-10 py-12 flex flex-col items-center gap-5 max-w-md w-full text-center">
        <div className="arc-id"><b>404</b>/<b>not-found</b></div>
        <div className="arc-mono text-[88px] leading-none font-medium text-[var(--accent)]">404</div>
        <h1 className="text-[18px] font-semibold text-[var(--text)] tracking-tight">Page not found</h1>
        <p className="arc-dim text-[13px] leading-relaxed">
          The route you requested does not exist. It may have been moved, renamed, or never existed.
        </p>
        {/* Action: primary on the LEFT */}
        <div className="flex w-full items-center gap-2 pt-2">
          <button onClick={() => navigate('/')} className="arc-btn primary">Go home</button>
          <span className="flex-1" />
          {appName && <span className="arc-chip">{appName}</span>}
        </div>
      </div>
    </div>
  );
};

export default NotFound;
