import React, { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { AlertTriangle, CheckCircle, Info, ChevronLeft, Search } from 'lucide-react'

interface Recall {
    component: string
    recall_date: string
    summary: string
    consequence: string
    remedy: string
    campaign_number: string
    severity: 'HIGH' | 'MEDIUM' | 'LOW'
}

interface Complaint {
    component: string
    count: number
}

interface VINReport {
    vin: string
    supported: boolean
    message: string | null
    vehicle_info: any
    recalls: Recall[]
    complaints: {
        total: number
        top_components: Complaint[]
    }
    market_pricing: any
    red_flags: string[]
}

const VINReportPage: React.FC = () => {
    const { vin: vinParam, doc_id: docIdParam } = useParams<{ vin?: string, doc_id?: string }>()
    const [searchParams] = useSearchParams()
    const docId = docIdParam || searchParams.get('doc_id')
    const navigate = useNavigate()

    const [report, setReport] = useState<VINReport | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [manualVin, setManualVin] = useState('')
    const [showManualInput, setShowManualInput] = useState(false)

    const fetchReport = async () => {
        setIsLoading(true)
        setError(null)
        try {
            let data
            if (vinParam) {
                data = await api.vin.lookup(vinParam, docId || undefined)
            } else if (docId) {
                data = await api.vin.fromDocument(docId)
                if (!data.supported && data.manual_entry_allowed) {
                    setShowManualInput(true)
                }
            } else {
                setError('No VIN or Document ID provided')
                setIsLoading(false)
                return
            }
            setReport(data)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch VIN report')
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchReport()
    }, [vinParam, docId])

    const handleLookup = async () => {
        if (!manualVin.trim()) return
        navigate(`/vin/${manualVin.trim()}${docId ? `?doc_id=${docId}` : ''}`)
    }

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                <p className="text-gray-400">Decoding VIN and analyzing market data...</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto p-6 min-h-screen bg-gray-950 text-white">
                <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-xl flex items-start gap-4 mb-6">
                    <AlertTriangle className="text-red-500 shrink-0 mt-1" />
                    <div>
                        <h3 className="font-bold text-red-100">Error</h3>
                        <p className="text-red-200/80">{error}</p>
                    </div>
                </div>
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                >
                    <ChevronLeft size={20} /> Back
                </button>
            </div>
        )
    }

    if (report && !report.supported) {
        return (
            <div className="max-w-4xl mx-auto p-6 min-h-screen bg-gray-950 text-white">
                <div className="bg-amber-900/20 border border-amber-500/50 p-6 rounded-xl flex items-start gap-4 mb-8">
                    <Info className="text-amber-500 shrink-0 mt-1" size={24} />
                    <div>
                        <h3 className="font-bold text-amber-100 text-lg">VIN Not Supported</h3>
                        <p className="text-amber-200/80 mt-1">{report.message}</p>
                    </div>
                </div>

                {showManualInput && (
                    <div className="bg-gray-900 border border-gray-800 p-8 rounded-2xl shadow-2xl">
                        <h3 className="text-xl font-bold mb-4">Enter VIN Manually</h3>
                        <div className="flex gap-4">
                            <input
                                type="text"
                                value={manualVin}
                                onChange={(e) => setManualVin(e.target.value.toUpperCase())}
                                placeholder="E.g. 1FA6P8CF5G5100001"
                                className="flex-1 bg-gray-800 border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                            <button
                                onClick={handleLookup}
                                className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-bold flex items-center gap-2 transition-colors"
                            >
                                <Search size={20} /> Look Up
                            </button>
                        </div>
                    </div>
                )}

                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mt-8"
                >
                    <ChevronLeft size={20} /> Back
                </button>
            </div>
        )
    }

    if (!report) return null

    return (
        <div className="max-w-5xl mx-auto p-6 min-h-screen bg-gray-950 text-white pb-20">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                >
                    <ChevronLeft size={20} /> Back to Contract Review
                </button>
                <div className="bg-blue-900/30 text-blue-400 px-4 py-1.5 rounded-full border border-blue-500/30 font-mono text-sm">
                    VIN: {report.vin}
                </div>
            </div>

            {/* Red Flags Column */}
            {report.red_flags.length > 0 && (
                <div className="mb-8 bg-red-950/20 border border-red-500/40 p-5 rounded-2xl">
                    <div className="flex items-center gap-3 mb-4">
                        <AlertTriangle className="text-red-500" />
                        <h2 className="text-xl font-bold text-red-100">Attention: Critical Red Flags</h2>
                    </div>
                    <div className="flex flex-wrap gap-3">
                        {report.red_flags.map((flag, idx) => (
                            <span key={idx} className="bg-red-500/20 text-red-200 border border-red-500/30 px-3 py-1.5 rounded-lg text-sm">
                                {flag}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Vehicle Info & Pricing */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Vehicle Info */}
                    <section className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                        <div className="p-6 border-b border-gray-800 bg-gray-800/30">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <Info size={20} className="text-blue-400" />
                                {report.vehicle_info.year} {report.vehicle_info.make} {report.vehicle_info.model}
                            </h2>
                            <p className="text-gray-400 text-sm mt-1">{report.vehicle_info.trim || 'Standard Trim'}</p>
                        </div>
                        <div className="p-6 grid grid-cols-2 md:grid-cols-3 gap-6">
                            {[
                                { label: 'Body Class', val: report.vehicle_info.body_class },
                                { label: 'Engine', val: report.vehicle_info.engine_displacement },
                                { label: 'Drive Type', val: report.vehicle_info.drive_type },
                                { label: 'Fuel Type', val: report.vehicle_info.fuel_type },
                                { label: 'Manufacturer', val: report.vehicle_info.manufacturer },
                                { label: 'Plant Country', val: report.vehicle_info.plant_country },
                            ].map((item, i) => (
                                <div key={i}>
                                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{item.label}</p>
                                    <p className="font-medium text-gray-200">{item.val || 'N/A'}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Market Pricing */}
                    <section className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-xl">
                        <div className="p-6 border-b border-gray-800 flex justify-between items-end">
                            <div>
                                <h2 className="text-xl font-bold">Market Price Estimate</h2>
                                <p className="text-gray-400 text-sm mt-1">Based on current US market data</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xs text-gray-500 uppercase tracking-wider">Est. MSRP</p>
                                <p className="text-2xl font-black text-blue-400">{report.market_pricing.msrp_estimate || 'N/A'}</p>
                            </div>
                        </div>

                        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Private Party */}
                            <div className="bg-emerald-950/20 border border-emerald-500/20 p-5 rounded-xl">
                                <p className="text-emerald-400 text-sm font-bold mb-2 uppercase tracking-tighter">Private Party</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.private_party_low}</span>
                                    <span className="text-gray-500">—</span>
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.private_party_high}</span>
                                </div>
                                <p className="text-xs text-emerald-500/60 mt-2 italic">Best value if buying direct</p>
                            </div>

                            {/* Dealer Retail */}
                            <div className="bg-blue-950/20 border border-blue-500/20 p-5 rounded-xl">
                                <p className="text-blue-400 text-sm font-bold mb-2 uppercase tracking-tighter">Dealer Retail</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.dealer_retail_low}</span>
                                    <span className="text-gray-500">—</span>
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.dealer_retail_high}</span>
                                </div>
                                <p className="text-xs text-blue-500/60 mt-2 italic">Standard pricing at dealerships</p>
                            </div>

                            {/* Lease Estimate */}
                            <div className="bg-purple-950/20 border border-purple-500/20 p-5 rounded-xl">
                                <p className="text-purple-400 text-sm font-bold mb-2 uppercase tracking-tighter">Monthly Lease</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.fair_monthly_lease_low}</span>
                                    <span className="text-gray-500">—</span>
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.fair_monthly_lease_high}</span>
                                </div>
                                <p className="text-xs text-purple-500/60 mt-2 italic">Fair monthly lease payment range</p>
                            </div>

                            {/* Loan Estimate */}
                            <div className="bg-amber-950/20 border border-amber-500/20 p-5 rounded-xl">
                                <p className="text-amber-400 text-sm font-bold mb-2 uppercase tracking-tighter">Monthly Loan</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.fair_monthly_loan_low}</span>
                                    <span className="text-gray-500">—</span>
                                    <span className="text-2xl font-bold text-white">{report.market_pricing.fair_monthly_loan_high}</span>
                                </div>
                                <p className="text-xs text-amber-500/60 mt-2 italic">Fair monthly loan payment range</p>
                            </div>
                        </div>

                        <div className="px-6 py-4 bg-gray-800/50 flex items-start gap-4">
                            <AlertTriangle className="text-gray-500 shrink-0 mt-0.5" size={16} />
                            <p className="text-[12px] text-gray-400 leading-tight">
                                {report.market_pricing.data_note}
                            </p>
                        </div>
                    </section>
                </div>

                {/* Right Column: Safety & Complaints */}
                <div className="space-y-8">
                    {/* Recalls */}
                    <section className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                        <div className="p-5 border-b border-gray-800 flex justify-between items-center">
                            <h2 className="text-lg font-bold">Safety Recalls</h2>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${report.recalls.length > 0 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                                {report.recalls.length}
                            </span>
                        </div>
                        <div className="max-h-[400px] overflow-y-auto">
                            {report.recalls.length === 0 ? (
                                <div className="p-10 text-center">
                                    <CheckCircle className="text-green-500 mx-auto mb-3" size={32} />
                                    <p className="text-gray-400 font-medium">No active recalls found</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-800">
                                    {report.recalls.map((recall, i) => (
                                        <div key={i} className="p-5">
                                            <div className="flex justify-between items-start mb-2">
                                                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-black ${recall.severity === 'HIGH' ? 'bg-red-500 text-white' :
                                                        recall.severity === 'MEDIUM' ? 'bg-amber-500 text-black' :
                                                            'bg-gray-700 text-gray-300'
                                                    }`}>
                                                    {recall.severity} SEVERITY
                                                </span>
                                                <p className="text-[10px] text-gray-500">{recall.recall_date}</p>
                                            </div>
                                            <h4 className="font-bold text-gray-200 text-sm mb-2">{recall.component}</h4>
                                            <p className="text-xs text-gray-400 line-clamp-3 hover:line-clamp-none cursor-pointer">
                                                {recall.summary}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Complaints */}
                    <section className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                        <div className="p-5 border-b border-gray-800 flex justify-between items-center">
                            <h2 className="text-lg font-bold">Owner Complaints</h2>
                            <span className="text-xs text-gray-400">Total: {report.complaints.total}</span>
                        </div>
                        <div className="p-5">
                            {report.complaints.total === 0 ? (
                                <div className="text-center py-6">
                                    <CheckCircle className="text-green-500 mx-auto mb-3" size={32} />
                                    <p className="text-gray-400">No complaints reported</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {report.complaints.top_components.map((comp, i) => (
                                        <div key={i}>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="text-gray-300 truncate pr-4">{comp.component}</span>
                                                <span className="text-gray-500 font-mono">{comp.count}</span>
                                            </div>
                                            <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                                                <div
                                                    className="bg-blue-500 h-full rounded-full"
                                                    style={{ width: `${Math.min(100, (comp.count / report.complaints.total) * 150)}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    ))}
                                    <p className="text-[10px] text-gray-500 mt-4 italic text-center">
                                        Data provided via NHTSA public records
                                    </p>
                                </div>
                            )}
                        </div>
                    </section>
                </div>
            </div>
        </div>
    )
}

export default VINReportPage
