/**
 * ProtectedRoute
 *
 * On every page load (or browser refresh) the in-memory access token is gone.
 * We call refreshAccessToken() which hits POST /auth/refresh with the
 * HTTP-only cookie. If the cookie is still valid the server responds with a
 * new access token and the user is let through. If the cookie is expired or
 * absent, the user is redirected to the landing page to log in again.
 */
import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { isAccessTokenValid, useAuthStore } from "../store/authStore";

export default function ProtectedRoute() {
  const { isAuthenticated, accessToken, refreshAccessToken } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (isAccessTokenValid(accessToken)) {
      // Token already in memory — no network call needed
      setChecking(false);
      return;
    }
    // Token lost on page refresh — recover silently via HTTP-only cookie
    refreshAccessToken().finally(() => setChecking(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (checking) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/" replace />;
  return <Outlet />;
}
