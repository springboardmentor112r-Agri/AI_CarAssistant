import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useAuthStore } from "../store/authStore"
import { api } from "../services/api"
import { FileText, Eye, EyeOff, AlertCircle } from "lucide-react"

const isValidEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim())

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [emailError, setEmailError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const handleLogin = async () => {
    setError("")
    setEmailError("")
    if (!email.trim()) { setEmailError("Email is required."); return }
    if (!isValidEmail(email)) { setEmailError("Please enter a valid email address."); return }
    if (!password.trim()) { setError("Password is required."); return }
    setIsLoading(true)
    try {
      const { access_token, user } = await api.auth.login(email.trim(), password)
      login(access_token, user)
      navigate("/dashboard")
    } catch (err: any) {
      const s = err?.response?.status
      if (s === 401 || s === 403) setError("Incorrect email or password. Please try again.")
      else if (s === 422) setError("Please enter a valid email and password.")
      else if (s === 429) setError("Too many attempts. Please wait a moment.")
      else if (!s || err?.code === "ERR_NETWORK") setError("Cannot connect to server.")
      else setError("Login failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="bg-gray-900 rounded-2xl p-8 w-full max-w-md shadow-xl border border-gray-800">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-blue-500/10 rounded-full mb-4">
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Contract AI</h1>
          <p className="text-gray-400 text-sm">Sign in to your account</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") document.getElementById("pwd")?.focus() }}
              placeholder="you@example.com"
              className={`w-full bg-gray-800 border text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:border-transparent transition-all ${emailError ? "border-red-500 focus:ring-red-500" : "border-gray-700 focus:ring-blue-500"}`}
            />
            <div className="h-5 mt-1">
              {emailError && <p className="text-xs text-red-400 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{emailError}</p>}
            </div>
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-medium text-gray-400">Password</label>
              <Link to="/forgot-password" className="text-xs text-blue-400 hover:text-blue-300">Forgot password?</Link>
            </div>
            <div className="relative">
              <input
                id="pwd"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !isLoading) handleLogin() }}
                placeholder="••••••••"
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 pr-11 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              <button type="button" tabIndex={-1} onClick={() => setShowPassword(p => !p)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200">
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="h-12">
            {error && (
              <div className="flex items-center gap-2 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>
          <button type="button" onClick={handleLogin} disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-75 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2">
            {isLoading ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /><span className="text-sm">Signing in...</span></> : "Sign In"}
          </button>
          <div className="pt-2 text-center">
            <Link to="/register" className="text-sm text-gray-400">Don't have an account? <span className="text-blue-400 hover:text-blue-300">Register</span></Link>
          </div>
        </div>
      </div>
    </div>
  )
}
