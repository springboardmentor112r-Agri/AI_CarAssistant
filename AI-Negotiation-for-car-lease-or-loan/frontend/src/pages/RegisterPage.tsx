import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { api } from "../services/api"
import { FileText } from "lucide-react"

export default function RegisterPage() {
    const [fullName, setFullName] = useState("")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [error, setError] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [successMessage, setSuccessMessage] = useState("")

    const navigate = useNavigate()

    const handleRegister = async () => {
        if (password !== confirmPassword) {
            setError("Passwords do not match")
            return
        }
        if (password.length < 8) {
            setError("Password must be at least 8 characters")
            return
        }

        try {
            setIsLoading(true)
            setError("")
            await api.auth.register({
                email,
                password,
                full_name: fullName
            })
            setSuccessMessage("Account created. Please sign in.")
            setTimeout(() => navigate("/login"), 2000)
        } catch (err: any) {
            setError(err.response?.data?.detail || "Registration failed")
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
                    <h1 className="text-2xl font-bold text-white mb-2">Create Account</h1>
                    <p className="text-gray-400">Join Contract AI today</p>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Full Name</label>
                        <input
                            type="text"
                            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="John Doe"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
                        <input
                            type="email"
                            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
                        <input
                            type="password"
                            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Confirm Password</label>
                        <input
                            type="password"
                            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="••••••••"
                        />
                    </div>

                    {error && (
                        <div className="text-red-400 text-sm bg-red-400/10 p-3 rounded-lg border border-red-400/20">
                            {error}
                        </div>
                    )}

                    {successMessage && (
                        <div className="text-green-400 text-sm bg-green-400/10 p-3 rounded-lg border border-green-400/20">
                            {successMessage}
                        </div>
                    )}

                    <div
                        onClick={!isLoading ? handleRegister : undefined}
                        className={`w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center cursor-pointer ${isLoading ? 'opacity-75 cursor-not-allowed' : ''}`}
                    >
                        {isLoading ? (
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                <span className="text-sm">Creating account...</span>
                            </div>
                        ) : (
                            "Create Account"
                        )}
                    </div>

                    <div className="pt-4 text-center">
                        <Link to="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                            Already have an account? Sign In
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    )
}
