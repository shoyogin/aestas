import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
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

function App() {
  const { isAuthenticated, isLoading, hasCompletedOnboarding } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-night-bordeaux">
        <div className="animate-pulse text-powder-blush text-lg">Loading…</div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route
        path="/onboarding"
        element={
          isAuthenticated ? (
            hasCompletedOnboarding ? (
              <Navigate to="/app" replace />
            ) : (
              <Onboarding />
            )
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route
        path="/onboarding/last-cycle"
        element={
          isAuthenticated ? (
            <LastCycle />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route
        path="/blooming"
        element={
          isAuthenticated ? (
            <Blooming />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route
        path="/app"
        element={
          isAuthenticated ? (
            <AppShell />
          ) : (
            <Navigate to="/" replace />
          )
        }
      >
        <Route element={<AppHome />}>
          <Route index element={<Track />} />
          <Route path="insights" element={<Insights />} />
          <Route path="friends" element={<Friends />} />
        </Route>
        <Route path="account" element={<Account />} />
      </Route>
      <Route
        path="/circle"
        element={
          isAuthenticated ? (
            <Circle />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route
        path="/circle/:followId"
        element={
          isAuthenticated ? (
            <SharedCycle />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
