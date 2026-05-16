import React from 'react';
import { useAras } from '../aras-core/hooks/useAras';
import { useNavigate } from 'react-router-dom';

const NotFound: React.FC = () => {
  const { appName } = useAras();
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] bg-slate-50 text-slate-700 p-8">
      <h1 className="text-9xl font-extrabold text-slate-300">404</h1>
      <p className="text-3xl font-bold mb-4">Page Not Found</p>
      <p className="text-lg text-center mb-8 max-w-md">
        The page you are looking for does not exist or an unexpected error occurred.
      </p>
      <button
        onClick={() => navigate('/')}
        className="px-6 py-3 bg-indigo-600 text-white rounded-xl text-lg font-semibold hover:bg-indigo-700 transition-colors shadow-md"
      >
        Go to Home
      </button>
      {appName && (
        <p className="mt-12 text-sm text-slate-400">
          You are currently in the <span className="font-bold">{appName}</span> application.
        </p>
      )}
    </div>
  );
};

export default NotFound;
