import { useState } from 'react'
import { Search, AlertTriangle, CheckCircle, Car } from 'lucide-react'
import { vinApi } from '../api'
import { VINReport } from '../types'
import toast from 'react-hot-toast'
import Spinner from '../components/ui/Spinner'

export default function VINPage() {
  const [vin, setVin] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<VINReport | null>(null)

  const lookup = async () => {
    if (vin.length !== 17) { toast.error('VIN must be exactly 17 characters'); return }
    setLoading(true)
    setReport(null)
    try {
      const data = await vinApi.lookup(vin)
      setReport(data)
    } catch {
      toast.error('VIN not found or lookup failed')
    } finally {
      setLoading(false)
    }
  }

  const v = report?.vehicle
  const recalls = report?.recalls ?? []

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">VIN Lookup</h1>
      <p className="text-slate-500 mb-6">Check vehicle specs and recall history using the free NHTSA database.</p>

      <div className="flex gap-2 mb-8">
        <input
          className="input flex-1 font-mono uppercase"
          placeholder="Enter 17-character VIN..."
          value={vin}
          onChange={(e) => setVin(e.target.value.toUpperCase().slice(0, 17))}
          onKeyDown={(e) => e.key === 'Enter' && lookup()}
          maxLength={17}
        />
        <button onClick={lookup} disabled={loading || vin.length !== 17} className="btn-primary px-5">
          {loading ? <Spinner className="text-white" /> : <Search size={16} />}
          Lookup
        </button>
      </div>

      {report && v && (
        <div className="space-y-5">
          {/* Vehicle info */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Car size={20} className="text-blue-600" />
              </div>
              <div>
                <h2 className="font-bold text-slate-900">{v.year} {v.make} {v.model}</h2>
                <p className="text-sm text-slate-400 font-mono">{v.vin}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2">
              {[
                ['Trim', v.trim],
                ['Body Class', v.body_class],
                ['Fuel Type', v.fuel_type],
              ].map(([label, value]) => value ? (
                <div key={label} className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-sm text-slate-500">{label}</span>
                  <span className="text-sm font-medium text-slate-900">{value}</span>
                </div>
              ) : null)}
            </div>
          </div>

          {/* Recalls */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              {recalls.length === 0 ? (
                <CheckCircle size={18} className="text-green-500" />
              ) : (
                <AlertTriangle size={18} className="text-red-500" />
              )}
              <h3 className="font-semibold text-slate-900">
                Recalls {recalls.length > 0 ? `(${recalls.length} found)` : '— None found'}
              </h3>
            </div>
            {recalls.length === 0 ? (
              <p className="text-sm text-green-700 bg-green-50 rounded-lg px-4 py-3">
                ✅ No recalls found in the NHTSA database for this vehicle.
              </p>
            ) : (
              <div className="space-y-3">
                {recalls.map((r, i) => (
                  <div key={i} className="p-4 bg-red-50 border border-red-100 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-red-800">{r.component}</span>
                      <span className="text-xs text-red-500 font-mono">{r.recall_number}</span>
                    </div>
                    <p className="text-sm text-red-700 mb-2">{r.summary}</p>
                    {r.remedy && (
                      <div className="text-xs text-slate-600 bg-white rounded p-2 border border-red-100">
                        <span className="font-semibold">Remedy: </span>{r.remedy}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}