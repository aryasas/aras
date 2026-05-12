import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { useUIStore } from './store/uiStore'
import Login from './views/Login'
import ForgotPassword from './views/ForgotPassword'
import ResetPassword from './views/ResetPassword'
import MainLayout from './layouts/MainLayout'
import HomeView from './views/Home'
import SettingsView from './views/Settings'
import ProfileView from './views/Profile'
import DynamicView from './views/DynamicView'
import DevToolsView from './views/DevTools'
import AppManagerView from './views/AppManager'
import AuditLogsView from './views/AuditLogs'
import RBACManagerView from './views/RBACManager'
import GlobalSettingsView from './views/GlobalSettings'
import InspectRoutesView from './views/InspectRoutes'
import GlobalDialog from './aras-core/components/GlobalDialog'
import { useEffect } from 'react'
import { FormattingService } from './aras-core/services/FormattingService'

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = useAuthStore((state) => state.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  const { showAlert, showConfirm, showError } = useUIStore();
  const token = useAuthStore((state) => state.token);

  useEffect(() => {
    if (token) {
      FormattingService.init();
    }
  }, [token]);

  useEffect(() => {
    // Override window.alert
    window.alert = (message?: string) => {
      showAlert('Alert', message || '');
    };

    // Override window.confirm
    // Note: window.confirm is synchronous, but our dialog is asynchronous.
    // This override will always return false and use the callback instead.
    // For real usage, developers should use showConfirm from useUIStore directly.
    window.confirm = (message?: string) => {
      showConfirm('Confirm', message || '', () => {});
      return false; 
    };

    // Global Error Handler for unhandled rejections
    const handleError = (event: PromiseRejectionEvent) => {
      const message = event.reason?.response?.data?.message || event.reason?.message || 'An unexpected error occurred';
      showError('Error', message);
    };

    window.addEventListener('unhandledrejection', handleError);
    return () => window.removeEventListener('unhandledrejection', handleError);
  }, [showAlert, showConfirm, showError]);

  return (
    <Router>
      <GlobalDialog />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Authenticated Routes with MainLayout */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<HomeView />} />
          <Route path="settings" element={<SettingsView />} />
          <Route path="settings/global" element={<GlobalSettingsView />} />
          <Route path="settings/audit" element={<AuditLogsView />} />
          <Route path="settings/rbac" element={<RBACManagerView />} />
          <Route path="devtools" element={<DevToolsView />} />
          <Route path="devtools/routes" element={<InspectRoutesView />} />
          <Route path="api/v1/dev/inspect/routes" element={<InspectRoutesView />} />
          <Route path="devtools/table/:app/:model" element={<DynamicView />} />
          <Route path="devtools/table/:app/:model/:id" element={<DynamicView />} />
          <Route path="apps" element={<AppManagerView />} />
          <Route path="profile" element={<ProfileView />} />
          <Route path=":app/:model" element={<DynamicView />} />
          <Route path=":app/:model/:id" element={<DynamicView />} />

          {/* Catch all for authenticated area */}
          <Route path="*" element={<div className="p-12 text-center text-slate-400 bg-white rounded-3xl border border-dashed border-slate-200">View not implemented yet.</div>} />
        </Route>

        {/* Global Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
