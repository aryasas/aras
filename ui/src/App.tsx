import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useParams } from 'react-router-dom'
import { lazy, Suspense, useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import { useUIStore } from './store/uiStore'
import { CommandPalette } from './aras-core/components/CommandPalette'
import GlobalDialog from './aras-core/components/GlobalDialog'
import SidePanel from './aras-core/components/SidePanel'
import { FormattingService } from './aras-core/services/FormattingService'
import { VocabularyProvider } from './context/VocabularyContext'
import { connectArasWebSocket, disconnectArasWebSocket } from './lib/ws'
import api, { isPublicPath } from './lib/api'
import CookieConsent from './components/CookieConsent'

const Login = lazy(() => import('./views/Login'))
const OrganizationPicker = lazy(() => import('./views/OrganizationPicker'))
const ForgotPassword = lazy(() => import('./views/ForgotPassword'))
const ResetPassword = lazy(() => import('./views/ResetPassword'))
const MainLayout = lazy(() => import('./layouts/TopMenuLayout'))
const HomeView = lazy(() => import('./views/Home'))
const SettingsPageView = lazy(() => import('./views/settings/SettingsPage'))
const AccessControlView = lazy(() => import('./views/RBACManager'))
const MasterDataPageView = lazy(() => import('./views/master-data/MasterDataPage'))
const DashboardSettingsView = lazy(() => import('./views/DashboardSettings'))
const ProfileView = lazy(() => import('./views/Profile'))
const DynamicView = lazy(() => import('./views/DynamicView'))
const ReportCenterView = lazy(() => import('./views/ReportCenter'))
const TemplateBuilderView = lazy(() => import('./views/TemplateBuilder'))
const AppManagerView = lazy(() => import('./views/AppManager'))
const AuditLogsView = lazy(() => import('./views/AuditLogs'))
const LicenseStatusView = lazy(() => import('./views/LicenseStatus'))
const WebPageView = lazy(() => import('./views/WebPageView'))
const ContactView = lazy(() => import('./views/ContactView'))
const PublicLanding = lazy(() => import('./views/PublicLanding'))
const CustomerSignup = lazy(() => import('./views/CustomerSignup'))
const CustomerPortal = lazy(() => import('./views/CustomerPortal'))
const CustomerPortalSetup = lazy(() => import('./views/CustomerPortalSetup'))
const ControlPanelDashboard = lazy(() => import('./views/control-panel/ControlPanelDashboard'))
const ControlPanelTenantDetail = lazy(() => import('./views/control-panel/TenantDetail'))
const LicensesPanel = lazy(() => import('./views/control-panel/LicensesPanel'))
const SaaSPlans = lazy(() => import('./views/saas/Plans'))
const HealthIntegrityView = lazy(() => import('./views/HealthIntegrity'))
const BackgroundTasksView = lazy(() => import('./views/BackgroundTasks'))
const ActivityHeatmapView = lazy(() => import('./views/ActivityHeatmap'))
const FileManagerView = lazy(() => import('./views/FileManager'))
const SeedManagerView = lazy(() => import('./views/SeedManager'))
const ArchivedView = lazy(() => import('./views/ArchivedView'))
const PosView = lazy(() => import('./views/PosView'))
const SmartDispatcher = lazy(() => import('./views/SmartDispatcher'))
const HelpUserView = lazy(() => import('./views/HelpUser'))
const HelpDevView = lazy(() => import('./views/HelpDev'))
const NotFound = lazy(() => import('./views/NotFound'))

const getArasRole = () => {
  const injectedRole = (globalThis as any).__ARAS_ROLE__
  return String(injectedRole || import.meta.env.VITE_ARAS_ROLE || 'tenant')
}

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

const ControlPanelRoute = ({ children }: { children: React.ReactNode }) => {
  if (getArasRole() !== 'control-panel') return <NotFound />
  return <>{children}</>
}

const TenantRoute = ({ children }: { children: React.ReactNode }) => {
  if (getArasRole() === 'control-panel') return <NotFound />
  return <>{children}</>
}

const LegacyTenantDetailRedirect = () => {
  const { id = '' } = useParams()
  return <Navigate to={`/control-panel/tenants/${id}`} replace />
}

function AppContent() {
  const { showAlert, showError } = useUIStore();
  const { themeMode, cornerMode, density, fontScale, accentColor } = useUIStore();
  const token = useAuthStore((state) => state.token);
  const setUser = useAuthStore((state) => state.setUser);
  const setOrganizations = useAuthStore((state) => state.setOrganizations);
  const setCapabilities = useAuthStore((state) => state.setCapabilities);
  const location = useLocation()
  const publicRoute = isPublicPath(location.pathname)

  useEffect(() => {
    const root = document.documentElement
    const vars = {
      '--accent': accentColor,
      '--aras-accent': accentColor,
      '--aras-accent-strong': `color-mix(in srgb, ${accentColor}, black 14%)`,
      '--aras-accent-glow': `color-mix(in srgb, ${accentColor}, transparent 78%)`,
      '--aras-radius': cornerMode === 'square' ? '0px' : '8px',
      '--aras-radius-lg': cornerMode === 'square' ? '0px' : '14px',
      '--aras-density': density === 'compact' ? '0.85' : density === 'comfy' ? '1.1' : '1',
      '--aras-font-scale': String(fontScale / 100),
    }
    Object.entries(vars).forEach(([key, value]) => root.style.setProperty(key, value))
    root.classList.toggle('dark', themeMode === 'dark')
    root.setAttribute('data-theme', themeMode)
  }, [accentColor, cornerMode, density, fontScale, themeMode]);

  useEffect(() => {
    if (!token || publicRoute) {
      disconnectArasWebSocket()
      return
    }
    connectArasWebSocket()
    return () => disconnectArasWebSocket()
  }, [publicRoute, token]);

  useEffect(() => {
    if (token && !publicRoute) {
      FormattingService.init();
    }
  }, [publicRoute, token]);

  useEffect(() => {
    if (!token || publicRoute) return

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
  }, [publicRoute, token, setUser, setOrganizations, setCapabilities]);

  useEffect(() => {
    // Override window.alert
    window.alert = (message?: string) => {
      showAlert('Alert', message || '');
    };

    // Global Error Handler for unhandled rejections
    const handleError = (event: PromiseRejectionEvent) => {
      const message = event.reason?.response?.data?.message || event.reason?.message || 'An unexpected error occurred';
      showError('Error', message);
    };

    window.addEventListener('unhandledrejection', handleError);
    return () => window.removeEventListener('unhandledrejection', handleError);
  }, [showAlert, showError]);

  return (
    <VocabularyProvider enabled={!publicRoute}>
      <CookieConsent />
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
        <Route path="/welcome" element={<PublicLanding />} />
        <Route path="/signup" element={<CustomerSignup />} />
        <Route path="/portal" element={<CustomerPortal />} />
        <Route path="/portal/setup" element={<CustomerPortalSetup />} />

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
          <Route path="settings" element={<Navigate to="/admin/settings" replace />} />
          <Route path="admin/settings" element={<SettingsPageView />}>
            <Route path="dashboard" element={<DashboardSettingsView />} />
            <Route path="preferences" element={<Navigate to="/admin/settings?ns=core" replace />} />
            <Route path="audit" element={<AuditLogsView />} />
            <Route path="access" element={<AccessControlView />} />
            <Route path="master-data" element={<MasterDataPageView />} />
            <Route path="files" element={<FileManagerView />} />
            <Route path="seeder" element={<SeedManagerView />} />
            <Route path="license" element={<TenantRoute><LicenseStatusView /></TenantRoute>} />
            <Route path="health" element={<HealthIntegrityView />} />
            <Route path="tasks" element={<BackgroundTasksView />} />
            <Route path="activity-heatmap" element={<ActivityHeatmapView />} />
          </Route>
          <Route path="admin/master-data" element={<Navigate to="/admin/settings/master-data" replace />} />
          <Route path="settings/dashboard" element={<Navigate to="/admin/settings/dashboard" replace />} />
          <Route path="settings/global" element={<Navigate to="/admin/settings?ns=core" replace />} />
          <Route path="settings/audit" element={<Navigate to="/admin/settings/audit" replace />} />
          <Route path="settings/rbac" element={<Navigate to="/admin/settings/access" replace />} />
          <Route path="admin/license" element={<Navigate to="/admin/settings/license" replace />} />
          <Route path="preview/:slug" element={<WebPageView />} />
          <Route path="settings/user-access" element={<Navigate to="/admin/settings/access" replace />} />
          <Route path="dev" element={<Navigate to="/admin/dev" replace />} />
          <Route path="dev/template-builder" element={<TemplateBuilderView />} />
          <Route path="dev/health" element={<Navigate to="/admin/settings/health" replace />} />
          <Route path="dev/routes" element={<Navigate to="/admin/dev/routes-debug" replace />} />
          <Route path="dev/handoff-runs" element={<Navigate to="/admin/dev/handoff" replace />} />
          <Route path="dev/tasks" element={<Navigate to="/admin/settings/tasks" replace />} />
          <Route path="dev/activity-heatmap" element={<Navigate to="/admin/settings/activity-heatmap" replace />} />
          <Route path="settings/files" element={<Navigate to="/admin/settings/files" replace />} />
          <Route path="admin/seeder" element={<Navigate to="/admin/settings/seeder" replace />} />
          <Route path="admin/tenants" element={<Navigate to="/control-panel/tenants" replace />} />
          <Route path="saas-admin" element={<Navigate to="/control-panel" replace />} />
          <Route path="saas-admin/tenants/:id" element={<LegacyTenantDetailRedirect />} />
          <Route path="saas-admin/plans" element={<Navigate to="/control-panel/plans" replace />} />
          <Route path="control-panel" element={<ControlPanelRoute><ControlPanelDashboard /></ControlPanelRoute>} />
          <Route path="control-panel/tenants" element={<ControlPanelRoute><ControlPanelDashboard /></ControlPanelRoute>} />
          <Route path="control-panel/tenants/:id" element={<ControlPanelRoute><ControlPanelTenantDetail /></ControlPanelRoute>} />
          <Route path="control-panel/licenses" element={<ControlPanelRoute><LicensesPanel /></ControlPanelRoute>} />
          <Route path="control-panel/plans" element={<ControlPanelRoute><SaaSPlans /></ControlPanelRoute>} />
          <Route path="dev/help" element={<HelpDevView />} />
          <Route path="help" element={<HelpUserView />} />
          <Route path="dev/table/:app/:model" element={<DynamicView />} />
          <Route path="dev/table/:app/:model/:id" element={<DynamicView />} />
          <Route path="dev/:resource" element={<DynamicView />} />
          <Route path="dev/:resource/:id" element={<DynamicView />} />
          <Route path="apps" element={<AppManagerView />} />
          <Route path="profile" element={<ProfileView />} />
          <Route path="reports" element={<ReportCenterView />} />
          <Route path="archive/*" element={<ArchivedView />} />
          <Route path="pot/pos" element={<PosView />} />
          <Route path="pot/sessions/:id/pos" element={<PosView />} />

          <Route path="admin/:segment1/*" element={<SmartDispatcher />} />
          <Route path=":segment1/*" element={<SmartDispatcher />} />

          {/* Catch all for authenticated area */}
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* Global Catch all */}
        <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
    </VocabularyProvider>
  )
}

// gpt-5.4
function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
