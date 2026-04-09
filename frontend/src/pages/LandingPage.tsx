import { useNavigate } from 'react-router-dom'
import { Car, FileText, Shield, MessageSquare, ChevronRight } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-primary-900 to-slate-900">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center">
            <Car size={20} className="text-white" />
          </div>
          <span className="text-white font-bold text-lg">CarLease AI</span>
        </div>
        <button
          onClick={() => navigate('/login')}
          className="text-slate-300 hover:text-white text-sm font-medium transition-colors"
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center text-center px-4 py-20">
        <div className="inline-flex items-center gap-2 bg-primary-600/20 border border-primary-500/30 rounded-full px-4 py-1.5 mb-6">
          <span className="text-primary-400 text-sm font-medium">AI Powered Contract Analysis</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
          Car Lease Agreement
          <span className="text-primary-400"> Analyzer</span>
        </h1>

        <p className="text-slate-300 text-lg md:text-xl max-w-2xl mb-10 leading-relaxed">
          Upload your car lease or loan contract and get instant AI-powered analysis.
          Understand every clause, spot red flags, and negotiate better deals.
        </p>

        <button
          onClick={() => navigate('/login')}
          className="inline-flex items-center gap-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold px-8 py-4 rounded-xl text-lg transition-colors shadow-lg shadow-primary-900/50"
        >
          Get Started
          <ChevronRight size={22} />
        </button>

        <p className="text-slate-400 text-sm mt-4">
          Free to use • No credit card required
        </p>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 px-8 pb-16 max-w-6xl mx-auto">
        {[
          {
            icon: FileText,
            title: 'Smart OCR',
            desc: 'Upload PDF, scanned documents, or images — we handle all formats',
            color: 'text-blue-400 bg-blue-400/10',
          },
          {
            icon: Shield,
            title: 'Risk Detection',
            desc: 'AI identifies red flags, hidden fees, and unfair clauses instantly',
            color: 'text-red-400 bg-red-400/10',
          },
          {
            icon: Car,
            title: 'VIN Verification',
            desc: 'Verify vehicle details and check recall history using NHTSA data',
            color: 'text-green-400 bg-green-400/10',
          },
          {
            icon: MessageSquare,
            title: 'AI Chatbot',
            desc: 'Ask questions like "Is this interest rate high?" and get instant answers',
            color: 'text-purple-400 bg-purple-400/10',
          },
        ].map(({ icon: Icon, title, desc, color }) => (
          <div key={title} className="bg-white/5 border border-white/10 rounded-xl p-6 text-left">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${color}`}>
              <Icon size={20} />
            </div>
            <h3 className="text-white font-semibold mb-2">{title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div className="px-8 pb-20 max-w-4xl mx-auto text-center">
        <h2 className="text-2xl font-bold text-white mb-10">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: '01', title: 'Upload Document', desc: 'PDF, image, or scanned contract' },
            { step: '02', title: 'OCR Extraction', desc: 'Text extracted from your document' },
            { step: '03', title: 'AI Analysis', desc: 'Contract understood and analyzed' },
            { step: '04', title: 'Get Insights', desc: 'Clear summary with risk highlights' },
          ].map(({ step, title, desc }) => (
            <div key={step} className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold mb-3">
                {step}
              </div>
              <h3 className="text-white font-semibold mb-1">{title}</h3>
              <p className="text-slate-400 text-sm">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-white/10 px-8 py-6 text-center">
        <p className="text-slate-400 text-sm">
          © 2025 CarLease AI — Powered by Google Gemini & NHTSA APIs
        </p>
      </div>
    </div>
  )
}