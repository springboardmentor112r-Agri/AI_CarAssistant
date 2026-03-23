import { useState } from "react"
import { Link } from "react-router-dom"
import {
    FileText, AlertCircle, CheckCircle,
    ArrowLeft
} from "lucide-react"
import { api } from "../services/api"

const isValidEmail = (email: string) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("")
    const [emailError, setEmailError] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [isSent, setIsSent] = useState(false)
    const [error, setError] = useState("")

    const handleSubmit = async () => {
        // Validate email first
        if (!email.trim()) {
            setEmailError("Email is required.")
            return
        }
        if (!isValidEmail(email)) {
            setEmailError("Please enter a valid email address.")
            return
        }

        try {
            setIsLoading(true)
            setError("")
            await api.auth.forgotPassword(email.trim())
            setIsSent(true)
        } catch {
            setError("Something went wrong. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center
                    justify-center bg-gray-950 px-4">
            <div className="bg-gray-900 rounded-2xl p-8
                      w-full max-w-md shadow-xl
                      border border-gray-800">

                {/* Logo */}
                <div className="flex flex-col items-center mb-8">
                    <div className="p-3 bg-blue-500/10 rounded-full mb-4">
                        <FileText className="w-8 h-8 text-blue-500" />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        Forgot Password
                    </h1>
                    <p className="text-gray-400 text-sm text-center">
                        Enter your email and we'll send you
                        a reset link.
                    </p>
                </div>

                {isSent ? (
                    // ── SUCCESS STATE ──────────────────────────
                    <div className="space-y-6">
                        <div className="flex flex-col items-center
                            text-center py-4">
                            <div className="w-16 h-16 rounded-full
                              bg-green-500/10 flex items-center
                              justify-center mb-4">
                                <CheckCircle className="w-8 h-8 text-green-500" />
                            </div>
                            <h2 className="text-white font-semibold
                             text-lg mb-2">
                                Check your email
                            </h2>
                            <p className="text-gray-400 text-sm
                            leading-relaxed">
                                If an account exists for{" "}
                                <span className="text-white font-medium">
                                    {email}
                                </span>
                                , you will receive a password reset
                                link within a few minutes.
                            </p>
                            <p className="text-gray-500 text-xs mt-3">
                                The link expires in 30 minutes.
                            </p>
                        </div>

                        <div className="space-y-3">
                            {/* Resend option */}
                            <button
                                onClick={() => {
                                    setIsSent(false)
                                    setEmail("")
                                }}
                                className="w-full py-2.5 rounded-lg
                           border border-gray-700
                           text-gray-400 hover:text-white
                           hover:border-gray-500
                           transition-colors text-sm"
                            >
                                Try a different email
                            </button>

                            <Link
                                to="/login"
                                className="w-full py-2.5 rounded-lg
                           bg-blue-600 hover:bg-blue-700
                           text-white font-medium
                           transition-colors text-sm
                           flex items-center justify-center"
                            >
                                Back to Sign In
                            </Link>
                        </div>
                    </div>

                ) : (
                    // ── FORM STATE ────────────────────────────
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium
                                 text-gray-400 mb-1">
                                Email Address
                            </label>
                            <input
                                type="email"
                                autoFocus
                                className={`w-full bg-gray-800 border
                            text-white rounded-lg px-4 py-2.5
                            focus:outline-none focus:ring-2
                            focus:border-transparent transition-all
                  ${emailError
                                        ? 'border-red-500 focus:ring-red-500'
                                        : 'border-gray-700 focus:ring-blue-500'
                                    }`}
                                value={email}
                                onChange={(e) => {
                                    setEmail(e.target.value)
                                    if (emailError) setEmailError("")
                                    if (error) setError("")
                                }}
                                onBlur={() => {
                                    if (email && !isValidEmail(email)) {
                                        setEmailError(
                                            "Please enter a valid email address."
                                        )
                                    }
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !isLoading) {
                                        handleSubmit()
                                    }
                                }}
                                placeholder="you@example.com"
                            />
                            {emailError && (
                                <p className="text-xs text-red-400 mt-1.5">
                                    {emailError}
                                </p>
                            )}
                        </div>

                        {error && (
                            <div className="flex items-center gap-2
                              text-sm text-red-400
                              bg-red-400/10 p-3 rounded-lg
                              border border-red-400/20">
                                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}

                        <button
                            onClick={!isLoading ? handleSubmit : undefined}
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
                                "Send Reset Link"
                            )}
                        </button>

                        <Link
                            to="/login"
                            className="flex items-center justify-center
                         gap-2 text-sm text-gray-400
                         hover:text-white transition-colors pt-2"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back to Sign In
                        </Link>
                    </div>
                )}
            </div>
        </div>
    )
}
