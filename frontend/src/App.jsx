import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Welcome from './components/Welcome'
import Onboarding from './components/Onboarding'
import LastCycle from './components/LastCycle'
import Blooming from './components/Blooming'
import Main from './components/Main'

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
            <Main />
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
