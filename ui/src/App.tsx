import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense, useEffect } from 'react'
import api from './lib/api'
import { useAuthStore } from './store/authStore'
import { useUIStore } from './store/uiStore'
import { CommandPalette } from './aras-core/components/CommandPalette'
import GlobalDialog from './aras-core/components/GlobalDialog'
import SidePanel from './aras-core/components/SidePanel'
import { FormattingService } from './aras-core/services/FormattingService'
import { VocabularyProvider } from './context/VocabularyContext'

const Login = lazy(() => import('./views/Login'))
const OrganizationPicker = lazy(() => import('./views/OrganizationPicker'))
const ForgotPassword = lazy(() => import('./views/ForgotPassword'))
const ResetPassword = lazy(() => import('./views/ResetPassword'))
const MainLayout = lazy(() => import('./layouts/MainLayout'))
const HomeView = lazy(() => import('./views/Home'))
const SettingsView = lazy(() => import('./views/Settings'))
const DashboardSettingsView = lazy(() => import('./views/DashboardSettings'))
const ProfileView = lazy(() => import('./views/Profile'))
const DynamicView = lazy(() => import('./views/DynamicView'))
const ReportCenterView = lazy(() => import('./views/ReportCenter'))
const DevToolsView = lazy(() => import('./views/DevTools'))
const TemplateBuilderView = lazy(() => import('./views/TemplateBuilder'))
const AppManagerView = lazy(() => import('./views/AppManager'))
const TenantAdmin = lazy(() => import('./views/TenantAdmin'))
const AuditLogsView = lazy(() => import('./views/AuditLogs'))
const RBACManagerView = lazy(() => import('./views/RBACManager'))
const ErpUserAccess = lazy(() => import('./views/ErpUserAccess'))
const GlobalSettingsView = lazy(() => import('./views/GlobalSettings'))
const LicenseStatusView = lazy(() => import('./views/LicenseStatus'))
const WebPageView = lazy(() => import('./views/WebPageView'))
const ContactView = lazy(() => import('./views/ContactView'))
const InspectRoutesView = lazy(() => import('./views/InspectRoutes'))
const HealthIntegrityView = lazy(() => import('./views/HealthIntegrity'))
const ArchivedView = lazy(() => import('./views/ArchivedView'))
const PosView = lazy(() => import('./views/PosView'))
const SmartDispatcher = lazy(() => import('./views/SmartDispatcher'))
const HelpUserView = lazy(() => import('./views/HelpUser'))
const HelpDevView = lazy(() => import('./views/HelpDev'))
const NotFound = lazy(() => import('./views/NotFound'))

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = useAuthStore((state) => state.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

const OrganizationGuard = ({ children }: { children: React.ReactNode }) => {
  const organizations = useAuthStore((state) => state.organizations)
  const activeOrgId = useAuthStore((state) => state.activeOrgId)

  if (organizations.length > 0 && activeOrgId === null) {
    return <Navigate to="/organization" replace />
  }

  return <>{children}</>
}

function App() {
  const { showAlert, showConfirm, showError } = useUIStore();
  const token = useAuthStore((state) => state.token);
  const setUser = useAuthStore((state) => state.setUser);
  const setOrganizations = useAuthStore((state) => state.setOrganizations);
  const setCapabilities = useAuthStore((state) => state.setCapabilities);

  useEffect(() => {
    if (token) {
      FormattingService.init();
    }
  }, [token]);

  useEffect(() => {
    if (!token) return

    const fetchCurrentUser = async () => {
      try {
        const response = await api.get('/auth/me')
        setUser(response.data)
        setOrganizations(response.data.organizations || [])
      } catch (error) {
        console.error('Failed to fetch current user', error)
      }
    }

    const fetchCapabilities = async () => {
      try {
        const response = await api.get('/admin/apps/capabilities')
        setCapabilities(response.data.active_apps || [], response.data.optional_features || {})
      } catch {
        // non-admin users may get 403; ignore
      }
    }

    fetchCurrentUser()
    fetchCapabilities()
  }, [token, setUser, setOrganizations, setCapabilities]);

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
      <VocabularyProvider>
      <CommandPalette />
      <GlobalDialog />
      <SidePanel />
      <Suspense fallback={<div className="flex h-screen items-center justify-center text-[var(--app-muted)] text-sm">Loading...</div>}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/organization"
          element={
            <ProtectedRoute>
              <OrganizationPicker />
            </ProtectedRoute>
          }
        />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/p/:slug" element={<WebPageView />} />
        <Route path="/contact" element={<ContactView />} />

        {/* Authenticated Routes with MainLayout */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <OrganizationGuard>
                <MainLayout />
              </OrganizationGuard>
            </ProtectedRoute>
          }
        >
          <Route index element={<HomeView />} />
          <Route path="dashboard" element={<HomeView />} />
          <Route path="settings" element={<SettingsView />} />
          <Route path="settings/dashboard" element={<DashboardSettingsView />} />
          <Route path="settings/global" element={<GlobalSettingsView />} />
          <Route path="settings/audit" element={<AuditLogsView />} />
          <Route path="settings/rbac" element={<RBACManagerView />} />
          <Route path="admin/license" element={<LicenseStatusView />} />
          <Route path="preview/:slug" element={<WebPageView />} />
          <Route path="config/user-access" element={<ErpUserAccess />} />
          <Route path="dev" element={<DevToolsView />} />
          <Route path="dev/template-builder" element={<TemplateBuilderView />} />
          <Route path="dev/health" element={<HealthIntegrityView />} />
          <Route path="dev/routes" element={<InspectRoutesView />} />
          <Route path="admin/tenants" element={<TenantAdmin />} />
          <Route path="dev/help" element={<HelpDevView />} />
          <Route path="help" element={<HelpUserView />} />
          <Route path="dev/table/:app/:model" element={<DynamicView />} />
          <Route path="dev/table/:app/:model/:id" element={<DynamicView />} />
          <Route path="apps" element={<AppManagerView />} />
          <Route path="profile" element={<ProfileView />} />
          <Route path="reports" element={<ReportCenterView />} />
          <Route path="archive/*" element={<ArchivedView />} />
          <Route path="pot/pos" element={<PosView />} />
          <Route path="pot/sessions/:id/pos" element={<PosView />} />
          
          <Route path=":segment1/*" element={<SmartDispatcher />} />

          {/* Catch all for authenticated area */}
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* Global Catch all */}
        <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
      </VocabularyProvider>
    </Router>
  )
}

export default App
