import { useState, useEffect } from "react"
import { useNavigate, useSearchParams, Link } from "react-router-dom"
import {
    FileText, Eye, EyeOff, AlertCircle,
    CheckCircle, XCircle
} from "lucide-react"
import { api } from "../services/api"

export default function ResetPasswordPage() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const token = searchParams.get("token") || ""

    const [password, setPassword] = useState("")
    const [confirm, setConfirm] = useState("")
    const [showPass, setShowPass] = useState(false)
    const [showConfirm, setShowConfirm] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [isSuccess, setIsSuccess] = useState(false)
    const [error, setError] = useState("")

    // Token validation states
    const [tokenStatus, setTokenStatus] = useState<
        'checking' | 'valid' | 'invalid'
    >('checking')

    // ── Validate token on mount ──────────────────────
    useEffect(() => {
        if (!token) {
            setTokenStatus('invalid')
            return
        }
        const checkToken = async () => {
            try {
                await api.auth.checkResetToken(token)
                setTokenStatus('valid')
            } catch {
                setTokenStatus('invalid')
            }
        }
        checkToken()
    }, [token])

    // ── Password strength checker ────────────────────
    const getPasswordStrength = (p: string) => {
        if (p.length === 0) return null
        if (p.length < 8) return {
            label: 'Too short', color: 'text-red-400',
            bar: 'bg-red-500', width: 'w-1/4'
        }
        const hasUpper = /[A-Z]/.test(p)
        const hasNumber = /[0-9]/.test(p)
        const hasSpecial = /[^A-Za-z0-9]/.test(p)
        const score = [hasUpper, hasNumber, hasSpecial]
            .filter(Boolean).length

        if (score === 0) return {
            label: 'Weak', color: 'text-orange-400',
            bar: 'bg-orange-500', width: 'w-2/4'
        }
        if (score === 1) return {
            label: 'Fair', color: 'text-yellow-400',
            bar: 'bg-yellow-500', width: 'w-3/4'
        }
        return {
            label: 'Strong', color: 'text-green-400',
            bar: 'bg-green-500', width: 'w-full'
        }
    }

    const strength = getPasswordStrength(password)

    // ── Submit handler ───────────────────────────────
    const handleReset = async () => {
        if (!password) {
            setError("Password is required.")
            return
        }
        if (password.length < 8) {
            setError("Password must be at least 8 characters.")
            return
        }
        if (password !== confirm) {
            setError("Passwords do not match.")
            return
        }

        try {
            setIsLoading(true)
            setError("")
            await api.auth.resetPassword(token, password)
            setIsSuccess(true)
            // Redirect to login after 3 seconds
            setTimeout(() => navigate("/login"), 3000)
        } catch (err: any) {
            const detail = err.response?.data?.detail || ""
            setError(detail || "Reset failed. Please request a new link.")
        } finally {
            setIsLoading(false)
        }
    }

    // ── CHECKING TOKEN ───────────────────────────────
    if (tokenStatus === 'checking') {
        return (
            <div className="min-h-screen flex items-center
                      justify-center bg-gray-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-2 border-blue-500/30
                          border-t-blue-500 rounded-full
                          animate-spin" />
                    <p className="text-gray-400 text-sm">
                        Validating reset link...
                    </p>
                </div>
            </div>
        )
    }

    // ── INVALID TOKEN ────────────────────────────────
    if (tokenStatus === 'invalid') {
        return (
            <div className="min-h-screen flex items-center
                      justify-center bg-gray-950 px-4">
                <div className="bg-gray-900 rounded-2xl p-8
                        w-full max-w-md shadow-xl
                        border border-gray-800
                        text-center">
                    <div className="w-16 h-16 rounded-full
                          bg-red-500/10 flex items-center
                          justify-center mx-auto mb-4">
                        <XCircle className="w-8 h-8 text-red-500" />
                    </div>
                    <h1 className="text-xl font-bold text-white mb-2">
                        Link Expired
                    </h1>
                    <p className="text-gray-400 text-sm mb-6
                        leading-relaxed">
                        This password reset link has expired or
                        already been used. Reset links are valid
                        for 30 minutes.
                    </p>
                    <Link
                        to="/forgot-password"
                        className="inline-block w-full py-2.5
                       bg-blue-600 hover:bg-blue-700
                       text-white font-medium rounded-lg
                       transition-colors text-sm"
                    >
                        Request New Link
                    </Link>
                    <Link
                        to="/login"
                        className="block mt-3 text-sm text-gray-400
                       hover:text-white transition-colors"
                    >
                        Back to Sign In
                    </Link>
                </div>
            </div>
        )
    }

    // ── SUCCESS ──────────────────────────────────────
    if (isSuccess) {
        return (
            <div className="min-h-screen flex items-center
                      justify-center bg-gray-950 px-4">
                <div className="bg-gray-900 rounded-2xl p-8
                        w-full max-w-md shadow-xl
                        border border-gray-800
                        text-center">
                    <div className="w-16 h-16 rounded-full
                          bg-green-500/10 flex items-center
                          justify-center mx-auto mb-4">
                        <CheckCircle className="w-8 h-8 text-green-500" />
                    </div>
                    <h1 className="text-xl font-bold text-white mb-2">
                        Password Reset!
                    </h1>
                    <p className="text-gray-400 text-sm mb-2">
                        Your password has been updated successfully.
                    </p>
                    <p className="text-gray-500 text-xs mb-6">
                        Redirecting to sign in...
                    </p>
                    <Link
                        to="/login"
                        className="inline-block w-full py-2.5
                       bg-blue-600 hover:bg-blue-700
                       text-white font-medium rounded-lg
                       transition-colors text-sm"
                    >
                        Sign In Now
                    </Link>
                </div>
            </div>
        )
    }

    // ── RESET FORM ───────────────────────────────────
    return (
        <div className="min-h-screen flex items-center
                    justify-center bg-gray-950 px-4">
            <div className="bg-gray-900 rounded-2xl p-8
                      w-full max-w-md shadow-xl
                      border border-gray-800">

                <div className="flex flex-col items-center mb-8">
                    <div className="p-3 bg-blue-500/10 rounded-full mb-4">
                        <FileText className="w-8 h-8 text-blue-500" />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        New Password
                    </h1>
                    <p className="text-gray-400 text-sm">
                        Choose a strong password
                    </p>
                </div>

                <div className="space-y-4">

                    {/* New password */}
                    <div>
                        <label className="block text-sm font-medium
                               text-gray-400 mb-1">
                            New Password
                        </label>
                        <div className="relative">
                            <input
                                type={showPass ? "text" : "password"}
                                autoFocus
                                className="w-full bg-gray-800 border
                           border-gray-700 text-white
                           rounded-lg px-4 py-2.5 pr-11
                           focus:outline-none focus:ring-2
                           focus:ring-blue-500
                           focus:border-transparent
                           transition-all"
                                value={password}
                                onChange={(e) => {
                                    setPassword(e.target.value)
                                    if (error) setError("")
                                }}
                                placeholder="Min. 8 characters"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPass(p => !p)}
                                className="absolute right-3 top-1/2
                           -translate-y-1/2 text-gray-400
                           hover:text-gray-200 transition-colors"
                                tabIndex={-1}
                            >
                                {showPass
                                    ? <EyeOff className="w-4 h-4" />
                                    : <Eye className="w-4 h-4" />
                                }
                            </button>
                        </div>
                        {/* Strength indicator */}
                        {strength && (
                            <div className="mt-2 space-y-1">
                                <div className="h-1 bg-gray-700 rounded-full
                                overflow-hidden">
                                    <div className={`h-full rounded-full
                                   transition-all duration-300
                                   ${strength.bar}
                                   ${strength.width}`} />
                                </div>
                                <p className={`text-xs ${strength.color}`}>
                                    {strength.label}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Confirm password */}
                    <div>
                        <label className="block text-sm font-medium
                               text-gray-400 mb-1">
                            Confirm Password
                        </label>
                        <div className="relative">
                            <input
                                type={showConfirm ? "text" : "password"}
                                className={`w-full bg-gray-800 border
                            text-white rounded-lg px-4
                            py-2.5 pr-11 focus:outline-none
                            focus:ring-2 focus:border-transparent
                            transition-all
                  ${confirm && password !== confirm
                                        ? 'border-red-500 focus:ring-red-500'
                                        : 'border-gray-700 focus:ring-blue-500'
                                    }`}
                                value={confirm}
                                onChange={(e) => {
                                    setConfirm(e.target.value)
                                    if (error) setError("")
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !isLoading) {
                                        handleReset()
                                    }
                                }}
                                placeholder="Repeat password"
                            />
                            <button
                                type="button"
                                onClick={() => setShowConfirm(p => !p)}
                                className="absolute right-3 top-1/2
                           -translate-y-1/2 text-gray-400
                           hover:text-gray-200 transition-colors"
                                tabIndex={-1}
                            >
                                {showConfirm
                                    ? <EyeOff className="w-4 h-4" />
                                    : <Eye className="w-4 h-4" />
                                }
                            </button>
                        </div>
                        {confirm && password !== confirm && (
                            <p className="text-xs text-red-400 mt-1.5">
                                Passwords do not match.
                            </p>
                        )}
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="flex items-center gap-2
                            text-sm text-red-400
                            bg-red-400/10 p-3 rounded-lg
                            border border-red-400/20">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Submit */}
                    <button
                        onClick={!isLoading ? handleReset : undefined}
                        disabled={isLoading}
                        className="w-full bg-blue-600 hover:bg-blue-700
                       disabled:opacity-75
                       disabled:cursor-not-allowed
                       text-white font-medium py-2.5
                       rounded-lg transition-colors
                       flex items-center justify-center"
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2
                              border-white/30 border-t-white
                              rounded-full animate-spin" />
                        ) : (
                            "Reset Password"
                        )}
                    </button>

                    <Link
                        to="/login"
                        className="block text-center text-sm
                       text-gray-400 hover:text-white
                       transition-colors pt-1"
                    >
                        Back to Sign In
                    </Link>

                </div>
            </div>
        </div>
    )
}
