import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense, useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import { useUIStore } from './store/uiStore'
import { CommandPalette } from './aras-core/components/CommandPalette'
import GlobalDialog from './aras-core/components/GlobalDialog'
import SidePanel from './aras-core/components/SidePanel'
import { FormattingService } from './aras-core/services/FormattingService'

const Login = lazy(() => import('./views/Login'))
const ForgotPassword = lazy(() => import('./views/ForgotPassword'))
const ResetPassword = lazy(() => import('./views/ResetPassword'))
const MainLayout = lazy(() => import('./layouts/MainLayout'))
const HomeView = lazy(() => import('./views/Home'))
const SettingsView = lazy(() => import('./views/Settings'))
const ProfileView = lazy(() => import('./views/Profile'))
const DynamicView = lazy(() => import('./views/DynamicView'))
const DevToolsView = lazy(() => import('./views/DevTools'))
const AppManagerView = lazy(() => import('./views/AppManager'))
const AuditLogsView = lazy(() => import('./views/AuditLogs'))
const RBACManagerView = lazy(() => import('./views/RBACManager'))
const GlobalSettingsView = lazy(() => import('./views/GlobalSettings'))
const InspectRoutesView = lazy(() => import('./views/InspectRoutes'))
const HealthIntegrityView = lazy(() => import('./views/HealthIntegrity'))

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
      <CommandPalette />
      <GlobalDialog />
      <SidePanel />
      <Suspense fallback={<div className="flex h-screen items-center justify-center text-slate-400 text-sm">Loading…</div>}>
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
          <Route path="dashboard" element={<HomeView />} />
          <Route path="settings" element={<SettingsView />} />
          <Route path="settings/global" element={<GlobalSettingsView />} />
          <Route path="settings/audit" element={<AuditLogsView />} />
          <Route path="settings/rbac" element={<RBACManagerView />} />
          <Route path="dev" element={<DevToolsView />} />
          <Route path="dev/health" element={<HealthIntegrityView />} />
          <Route path="dev/routes" element={<InspectRoutesView />} />
          <Route path="dev/table/:app/:model" element={<DynamicView />} />
          <Route path="dev/table/:app/:model/:id" element={<DynamicView />} />
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
      </Suspense>
    </Router>
  )
}

export default App
