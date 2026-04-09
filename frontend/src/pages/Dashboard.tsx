import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileText, MessageSquare, Search, TrendingUp, Plus, AlertTriangle, CheckCircle } from 'lucide-react'
import { contractsApi } from '../api'
import { useAuthStore } from '../store/authStore'
import FairnessScore from '../components/ui/FairnessScore'
import Spinner from '../components/ui/Spinner'

export default function Dashboard() {
  const { user } = useAuthStore()
  const { data, isLoading } = useQuery({
    queryKey: ['contracts'],
    queryFn: contractsApi.list,
  })

  const contracts = data?.contracts ?? []
  const extracted = contracts.filter((c) => c.doc_status === 'extracted')
  const avgScore = extracted.length
    ? extracted.reduce((s, c) => s + (c.fairness_score ?? 0), 0) / extracted.length
    : null

  const stats = [
    { label: 'Contracts Uploaded', value: contracts.length, icon: FileText, color: 'text-blue-600 bg-blue-50' },
    { label: 'Analyzed', value: extracted.length, icon: CheckCircle, color: 'text-green-600 bg-green-50' },
    { label: 'Red Flags Found', value: contracts.filter((c) => c.red_flag_level === 'high').length, icon: AlertTriangle, color: 'text-red-600 bg-red-50' },
    { label: 'Avg Fairness Score', value: avgScore ? `${Math.round(avgScore)}/100` : '—', icon: TrendingUp, color: 'text-purple-600 bg-purple-50' },
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'there'} 👋
        </h1>
        <p className="text-slate-500 mt-1">Here's an overview of your car contract activity.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-5">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${color}`}>
              <Icon size={20} />
            </div>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
            <p className="text-sm text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Link to="/contracts/upload" className="card p-6 hover:border-primary-300 transition-colors group">
          <div className="w-10 h-10 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center mb-3 group-hover:bg-primary-100 transition-colors">
            <Plus size={20} />
          </div>
          <h3 className="font-semibold text-slate-900">Upload Contract</h3>
          <p className="text-sm text-slate-500 mt-1">Upload a lease or loan PDF for AI analysis</p>
        </Link>
        <Link to="/negotiate" className="card p-6 hover:border-primary-300 transition-colors group">
          <div className="w-10 h-10 rounded-lg bg-green-50 text-green-600 flex items-center justify-center mb-3 group-hover:bg-green-100 transition-colors">
            <MessageSquare size={20} />
          </div>
          <h3 className="font-semibold text-slate-900">Start Negotiating</h3>
          <p className="text-sm text-slate-500 mt-1">Get AI-powered negotiation tips and messages</p>
        </Link>
        <Link to="/vin" className="card p-6 hover:border-primary-300 transition-colors group">
          <div className="w-10 h-10 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center mb-3 group-hover:bg-orange-100 transition-colors">
            <Search size={20} />
          </div>
          <h3 className="font-semibold text-slate-900">VIN Lookup</h3>
          <p className="text-sm text-slate-500 mt-1">Check recalls, specs, and vehicle history</p>
        </Link>
      </div>

      {/* Recent Contracts */}
      <div className="card">
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <h2 className="font-semibold text-slate-900">Recent Contracts</h2>
          <Link to="/contracts" className="text-sm text-primary-600 hover:underline">View all</Link>
        </div>
        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : contracts.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <FileText size={40} className="mx-auto mb-3 opacity-40" />
            <p>No contracts yet. Upload your first one!</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {contracts.slice(0, 5).map((c) => (
              <Link key={c.id} to={`/contracts/${c.id}`} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                    <FileText size={16} className="text-slate-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{c.dealer_offer_name || `Contract #${c.id}`}</p>
                    <p className="text-xs text-slate-400">
                      {c.contract_type?.toUpperCase() ?? 'UNKNOWN'} • {new Date(c.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {c.fairness_score && <FairnessScore score={c.fairness_score} size="sm" />}
                  <span className={`badge-${c.doc_status === 'extracted' ? 'green' : c.doc_status === 'failed' ? 'red' : 'yellow'}`}>
                    {c.doc_status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}