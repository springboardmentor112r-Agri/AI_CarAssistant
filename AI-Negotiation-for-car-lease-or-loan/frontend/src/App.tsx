import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { isAccessTokenValid, useAuthStore } from "./store/authStore";
import { useThemeStore } from "./store/themeStore";
import ProtectedRoute from "./components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import ContractReviewPage from "./pages/ContractReviewPage";
import NegotiationChatPage from "./pages/NegotiationChatPage";
import VINReportPage from "./pages/VINReportPage";
import ComparisonPage from "./pages/ComparisonPage";
import AdminPage from "./pages/AdminPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";

/**
 * Root redirect: attempts a silent token refresh on startup.
 *   - Refresh succeeds (cookie valid, ≤7 days old) → /dashboard
 *   - Refresh fails (no cookie or expired)          → LandingPage
 */
function RootRedirect() {
  const { isAuthenticated, accessToken, refreshAccessToken } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (isAccessTokenValid(accessToken)) {
      setChecking(false);
      return;
    }
    refreshAccessToken().finally(() => setChecking(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (checking) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <LandingPage />;
}

export default function App() {
  const { theme } = useThemeStore();

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Root: smart redirect based on auth state */}
        <Route path="/" element={<RootRedirect />} />

        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route
            path="/documents/:doc_id/review"
            element={<ContractReviewPage />}
          />
          <Route path="/chat/:doc_id" element={<NegotiationChatPage />} />
          <Route path="/vin/:vin" element={<VINReportPage />} />
          <Route path="/compare" element={<ComparisonPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
