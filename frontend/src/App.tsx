import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import ProtectedRoute from './components/ui/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'
import ContractsPage from './pages/ContractsPage'
import ContractDetailPage from './pages/ContractDetailPage'
import UploadPage from './pages/UploadPage'
import NegotiatePage from './pages/NegotiatePage'
import VINPage from './pages/VINPage'
import ComparePage from './pages/ComparePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthPage />} />

        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/contracts/upload" element={<UploadPage />} />
          <Route path="/contracts/:id" element={<ContractDetailPage />} />
          <Route path="/negotiate" element={<NegotiatePage />} />
          <Route path="/vin" element={<VINPage />} />
          <Route path="/compare" element={<ComparePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}