import { Routes, Route, Navigate, BrowserRouter } from 'react-router-dom'
import { useChatStore } from './store/chatStore'
import Chat from './pages/Chat'
import Admin from './pages/Admin'
import Login from './pages/Login'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useChatStore((s) => s.token)
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const token = useChatStore((s) => s.token)
  if (token) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <Admin />
            </ProtectedRoute>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
