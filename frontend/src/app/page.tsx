import Link from "next/link";
import {
  Car, FileText, Shield, CheckCircle, Search, MessageSquare,
  TrendingUp, Star, ArrowRight, Zap, Users, Award
} from "lucide-react";

const features = [
  {
    icon: FileText,
    color: "from-blue-500 to-cyan-400",
    bg: "bg-blue-500/10",
    iconColor: "text-blue-400",
    title: "Contract SLA Extraction",
    desc: "AI automatically extracts APR, lease term, monthly payments, residual value, mileage allowances, and all critical clauses from your PDF.",
  },
  {
    icon: Shield,
    color: "from-red-500 to-orange-400",
    bg: "bg-red-500/10",
    iconColor: "text-red-400",
    title: "Red Flag Detection",
    desc: "Instantly spot hidden penalties, unfair early termination clauses, excessive overage charges, and problematic buyout conditions.",
  },
  {
    icon: CheckCircle,
    color: "from-green-500 to-emerald-400",
    bg: "bg-green-500/10",
    iconColor: "text-green-400",
    title: "Contract Fairness Score",
    desc: "Get a 1–100 fairness score comparing your contract against real market benchmarks and industry standards.",
  },
  {
    icon: Search,
    color: "from-indigo-500 to-purple-400",
    bg: "bg-indigo-500/10",
    iconColor: "text-indigo-400",
    title: "VIN-Based Vehicle Insights",
    desc: "Enter your VIN to fetch manufacturer details, recall history, odometer checks, and registration data from public databases.",
  },
  {
    icon: TrendingUp,
    color: "from-yellow-500 to-amber-400",
    bg: "bg-yellow-500/10",
    iconColor: "text-yellow-400",
    title: "Fair Market Price Estimation",
    desc: "See what your vehicle is actually worth using NHTSA data and market listings. Know if you're being offered a fair deal.",
  },
  {
    icon: MessageSquare,
    color: "from-pink-500 to-rose-400",
    bg: "bg-pink-500/10",
    iconColor: "text-pink-400",
    title: "AI Negotiation Assistant",
    desc: "Chat with our AI to get dealer questions, negotiation scripts, and personalized strategies based on your contract's specific terms.",
  },
];

const steps = [
  { num: "01", title: "Upload Your Contract", desc: "Drag and drop your lease or loan PDF. We support all major car manufacturers and leasing companies." },
  { num: "02", title: "AI Extracts & Analyzes", desc: "Our LLM instantly extracts every key clause, scores fairness, and flags risks — in under 30 seconds." },
  { num: "03", title: "Negotiate with Confidence", desc: "Use your personalized report and AI chat to push back on dealers and secure the best possible deal." },
];

const stats = [
  { value: "10K+", label: "Contracts Analyzed" },
  { value: "98%", label: "Extraction Accuracy" },
  { value: "$2,400", label: "Avg. Savings Found" },
  { value: "< 30s", label: "Analysis Time" },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-dark-gradient text-white">

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        {/* Background glow orbs */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-72 h-72 bg-purple-600/20 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-indigo-500/30 text-indigo-300 text-sm font-medium mb-8 animate-fade-in">
            <Zap className="w-4 h-4 text-yellow-400" />
            AI-Powered Contract Intelligence
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight tracking-tight mb-6 animate-slide-up">
            Never Sign a Bad{" "}
            <span className="gradient-text-blue">Car Lease</span>{" "}
            <br className="hidden md:block" />
            Again
          </h1>

          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 animate-slide-up delay-100">
            Upload your car lease or loan contract and our AI will extract every key term, detect hidden fees, score contract fairness, and coach you to negotiate a better deal.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up delay-200">
            <Link
              href="/signup"
              className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-2xl shadow-2xl hover:shadow-indigo-500/40 transition-all duration-300 hover:-translate-y-1"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/login"
              className="flex items-center gap-2 px-8 py-4 glass border border-white/15 hover:border-indigo-400/40 text-slate-300 hover:text-white font-semibold rounded-2xl transition-all duration-300 hover:-translate-y-1"
            >
              Sign In
            </Link>
          </div>

          {/* Stats bar */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 animate-slide-up delay-300">
            {stats.map((s) => (
              <div key={s.label} className="glass border border-white/10 rounded-2xl p-5 card-hover">
                <p className="text-3xl font-extrabold gradient-text-blue">{s.value}</p>
                <p className="text-sm text-slate-400 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-extrabold mb-4">
              Everything You Need to{" "}
              <span className="gradient-text-blue">Protect Yourself</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-xl mx-auto">
              From AI-powered contract analysis to live negotiation coaching — we've built every tool you need.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="glass border border-white/10 rounded-2xl p-6 card-hover group">
                <div className={`w-12 h-12 rounded-xl ${f.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  <f.icon className={`w-6 h-6 ${f.iconColor}`} />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-extrabold mb-4">
              How It <span className="gradient-text-blue">Works</span>
            </h2>
            <p className="text-slate-400 text-lg">Three simple steps to total contract clarity.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Connector line */}
            <div className="hidden md:block absolute top-12 left-1/3 right-1/3 h-0.5 bg-gradient-to-r from-indigo-500/50 to-purple-500/50" />

            {steps.map((step, i) => (
              <div key={step.num} className="flex flex-col items-center text-center animate-slide-up" style={{ animationDelay: `${i * 150}ms` }}>
                <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center mb-6 shadow-2xl shadow-indigo-500/30 animate-float" style={{ animationDelay: `${i * 500}ms` }}>
                  <span className="text-3xl font-extrabold text-white">{step.num}</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{step.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed max-w-xs">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-20 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold mb-3">Trusted by Car Buyers</h2>
            <div className="flex items-center justify-center gap-1 text-yellow-400 mb-3">
              {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
            </div>
            <p className="text-slate-400">4.9/5 from 2,400+ reviews</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { name: "Priya R.", quote: "Found a $1,800 hidden penalty I would have completely missed. AutoNegotiator paid for itself 100x over." },
              { name: "Marcus T.", quote: "The AI chatbot helped me write a negotiation email to my dealer. Got $2,100 off the final price!" },
              { name: "Sofia L.", quote: "I uploaded 3 competing offers and the comparison dashboard made it crystal clear which was the best deal." },
            ].map((review) => (
              <div key={review.name} className="glass border border-white/10 rounded-2xl p-6 card-hover">
                <div className="flex items-center gap-1 text-yellow-400 mb-4">
                  {[...Array(5)].map((_, i) => <Star key={i} className="w-4 h-4 fill-current" />)}
                </div>
                <p className="text-slate-300 text-sm leading-relaxed mb-4">"{review.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                    {review.name.charAt(0)}
                  </div>
                  <p className="text-white font-medium text-sm">{review.name}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="glass border border-indigo-500/30 rounded-3xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/10 to-purple-600/10 pointer-events-none" />
            <div className="relative z-10">
              <Award className="w-14 h-14 text-indigo-400 mx-auto mb-4 animate-float" />
              <h2 className="text-4xl font-extrabold mb-4">Ready to Review Your Contract?</h2>
              <p className="text-slate-400 text-lg mb-8">
                Join thousands of car buyers who saved money using AI-powered contract intelligence.
              </p>
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 px-10 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-lg rounded-2xl shadow-2xl hover:shadow-indigo-500/40 transition-all duration-300 hover:-translate-y-1"
              >
                Start for Free
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <Car className="w-4 h-4" />
            <span className="font-semibold text-slate-400">AutoNegotiator AI</span>
          </div>
          <p>© {new Date().getFullYear()} AutoNegotiator AI. Not financial or legal advice.</p>
          <div className="flex gap-4">
            <Link href="/login" className="hover:text-slate-300 transition-colors">Login</Link>
            <Link href="/signup" className="hover:text-slate-300 transition-colors">Sign Up</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
