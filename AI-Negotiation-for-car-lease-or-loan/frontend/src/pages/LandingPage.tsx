import { Link } from 'react-router-dom'
import { Car, Sun, Moon, FileSearch, AlertTriangle, MessageSquare, BarChart2, Shield } from 'lucide-react'
import { useThemeStore } from '../store/themeStore'

export default function LandingPage() {
    const { theme, toggleTheme } = useThemeStore()

    const scrollToFeatures = () => {
        document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
    }

    return (
        <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-300">

            {/* TOP BAR */}
            <nav className="p-6 flex items-center justify-between border-b border-transparent">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-600 dark:bg-blue-500 p-2 rounded-xl text-white">
                        <Car className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-xl tracking-tight">Contract AI</span>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={toggleTheme}
                        className="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white rounded-full transition-colors"
                        aria-label="Toggle theme"
                    >
                        {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </button>

                    <div className="hidden sm:flex items-center gap-4">
                        <Link
                            to="/login"
                            className="text-sm font-medium hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                            Sign In
                        </Link>
                        <Link
                            to="/register"
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors shadow-sm"
                        >
                            Get Started
                        </Link>
                    </div>
                </div>
            </nav>

            {/* HERO SECTION */}
            <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-20 relative overflow-hidden">
                {/* Decorative background elements */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500/10 dark:bg-blue-500/5 blur-3xl rounded-full pointer-events-none"></div>

                <div className="relative z-10 flex flex-col items-center max-w-4xl mx-auto">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium mb-8 border border-blue-100 dark:border-blue-800/50">
                        ✨ AI-Powered Contract Analysis
                    </div>

                    <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-tight mb-6">
                        Never Sign a Bad <br className="hidden md:block" />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-500 dark:from-blue-400 dark:to-indigo-400">
                            Car Contract Again
                        </span>
                    </h1>

                    <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                        Upload your lease or loan contract. Get instant analysis, red flag detection,
                        and expert negotiation coaching.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                        <Link
                            to="/register"
                            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold rounded-2xl transition-all shadow-lg shadow-blue-600/20 hover:shadow-blue-600/40 hover:-translate-y-0.5 flex items-center justify-center"
                        >
                            Analyse My Contract
                        </Link>
                        <button
                            onClick={scrollToFeatures}
                            className="px-8 py-4 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 text-lg font-semibold rounded-2xl transition-all shadow-sm hover:-translate-y-0.5"
                        >
                            See How It Works
                        </button>
                    </div>
                </div>
            </section>

            {/* FEATURES GRID */}
            <section id="features" className="py-24 px-6 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything You Need to Negotiate</h2>
                        <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">Our AI breaks down complex legal jargon into simple, actionable insights so you can buy with confidence.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: FileSearch, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-900/20",
                                title: "Smart Extraction", desc: "Supports PDF, Word, Excel, images and more"
                            },
                            {
                                icon: AlertTriangle, color: "text-red-500", bg: "bg-red-50 dark:bg-red-900/20",
                                title: "Red Flag Detection", desc: "Instantly spots unfavorable terms and hidden fees"
                            },
                            {
                                icon: MessageSquare, color: "text-indigo-500", bg: "bg-indigo-50 dark:bg-indigo-900/20",
                                title: "AI Negotiation Coach", desc: "Get word-for-word scripts to negotiate better deals"
                            },
                            {
                                icon: Car, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-900/20",
                                title: "VIN Lookup", desc: "Free safety recalls and market pricing data"
                            },
                            {
                                icon: BarChart2, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-900/20",
                                title: "Compare Contracts", desc: "Side by side comparison of multiple offers"
                            },
                            {
                                icon: Shield, color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-900/20",
                                title: "Your Data is Secure", desc: "Documents processed and stored securely"
                            }
                        ].map((feature, idx) => (
              <div key={idx} className="p-8 rounded-3xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50 hover:shadow-xl dark:hover:shadow-gray-900/50 transition-all hover:bg-white dark:hover:bg-gray-800">
                <div className={`w-14 h-14 rounded-2xl ${feature.bg} ${feature.color} flex items-center justify-center mb-6`}>
                  <feature.icon className="w-7 h-7" />
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
                </div>
        </div>
      </section >

        {/* FOOTER */ }
        < footer className = "py-8 border-t border-gray-200 dark:border-gray-800 text-center text-gray-500 dark:text-gray-400 text-sm bg-gray-50 dark:bg-gray-950" >
            <p>© 2026 Contract AI. Built for car buyers.</p>
      </footer >

    </div >
  )
}
