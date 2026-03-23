import { Link, useNavigate } from "react-router-dom";
import { Car, Sun, Moon, BarChart2 } from "lucide-react";
import { useThemeStore } from "../store/themeStore";
import { useAuthStore } from "../store/authStore";
import { useState } from "react";

export default function Navbar() {
  const { theme, toggleTheme } = useThemeStore();
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const isAdmin = user?.email === import.meta.env.VITE_ADMIN_EMAIL;

  const handleLogout = async () => {
    await logout(); // revokes refresh token server-side, clears cookie
    navigate("/");
  };

  return (
    <nav className="h-16 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-2">
        <Link
          to="/dashboard"
          className="flex items-center gap-2 text-blue-600 dark:text-blue-500 font-bold text-xl tracking-tight"
        >
          <Car className="w-6 h-6" />
          <span>Contract AI</span>
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={toggleTheme}
          className="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white rounded-full transition-colors"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </button>

        {user && (
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200 p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                {user.full_name
                  ? user.full_name.charAt(0).toUpperCase()
                  : user.email.charAt(0).toUpperCase()}
              </div>
              <span className="hidden sm:block">
                {user.full_name || user.email}
              </span>
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-1 overflow-hidden">
                <Link
                  to="/dashboard"
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  Dashboard
                </Link>
                {isAdmin && (
                  <Link
                    to="/admin"
                    onClick={() => setMenuOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <BarChart2 className="w-4 h-4" />
                    LLM Monitor
                  </Link>
                )}
                <div className="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    handleLogout();
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
