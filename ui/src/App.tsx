import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './views/Login'
import ForgotPassword from './views/ForgotPassword'
import ResetPassword from './views/ResetPassword'
import MainLayout from './layouts/MainLayout'
import HomeView from './views/Home'
import SettingsView from './views/Settings'
import ProfileView from './views/Profile'
import DynamicView from './views/DynamicView'

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = useAuthStore((state) => state.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  return (
    <Router>
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
          <Route path="profile" element={<ProfileView />} />
          <Route path=":app/:model" element={<DynamicView />} />
...

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
