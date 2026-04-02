import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import { useAuth } from './hooks/useAuth.js'

export default function App() {
  const { token } = useAuth()

  return (
    <Routes>
      <Route path="/login"     element={!token ? <LoginPage />     : <Navigate to="/dashboard" />} />
      <Route path="/dashboard" element={ token  ? <DashboardPage /> : <Navigate to="/login" />}     />
      <Route path="*"          element={<Navigate to={token ? '/dashboard' : '/login'} />}           />
    </Routes>
  )
}
