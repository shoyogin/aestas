import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/authContext'
import AuthProvider from './components/AuthProvider'
import Welcome from './components/Welcome'
import Onboarding from './components/Onboarding'
import LastCycle from './components/LastCycle'
import Blooming from './components/Blooming'
import AppShell from './components/AppShell'
import AppHome from './components/AppHome'
import Track from './components/Track'
import Insights from './components/Insights'
import Friends from './components/Friends'
import Account from './components/Account'
import Circle from './components/Circle'
import SharedCycle from './components/SharedCycle'

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-night-bordeaux">
      <div className="animate-pulse text-powder-blush text-lg" role="status">
        Loading…
      </div>
    </div>
  )
}

/** Requires a session. `needsOnboarding` guards the onboarding-only screens. */
function RequireAuth({ children, allowBeforeOnboarding = true }) {
  const { isAuthenticated, hasCompletedOnboarding } = useAuth()
  if (!isAuthenticated) return <Navigate to="/" replace />
  if (!allowBeforeOnboarding && !hasCompletedOnboarding) {
    return <Navigate to="/onboarding" replace />
  }
  return children
}

function AppRoutes() {
  const { isLoading, isAuthenticated, hasCompletedOnboarding } = useAuth()

  if (isLoading) return <Loading />

  return (
    <Routes>
      <Route
        path="/"
        element={isAuthenticated ? <Navigate to="/app" replace /> : <Welcome />}
      />
      <Route
        path="/onboarding"
        element={
          <RequireAuth>
            {hasCompletedOnboarding ? <Navigate to="/app" replace /> : <Onboarding />}
          </RequireAuth>
        }
      />
      <Route
        path="/onboarding/last-cycle"
        element={
          // Only reachable once a cycle length exists; otherwise step 2 would
          // save a start date for a cycle that has no length.
          <RequireAuth allowBeforeOnboarding={false}>
            <LastCycle />
          </RequireAuth>
        }
      />
      <Route path="/blooming" element={<RequireAuth><Blooming /></RequireAuth>} />
      <Route path="/app" element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route element={<AppHome />}>
          <Route index element={<Track />} />
          <Route path="insights" element={<Insights />} />
          <Route path="friends" element={<Friends />} />
        </Route>
        <Route path="account" element={<Account />} />
      </Route>
      <Route path="/circle" element={<RequireAuth><Circle /></RequireAuth>} />
      <Route path="/circle/:followId" element={<RequireAuth><SharedCycle /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
