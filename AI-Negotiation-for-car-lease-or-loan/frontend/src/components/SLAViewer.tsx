import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'
import { api } from '../services/api'
import { SLAJson } from '../types'

interface SLAViewerProps {
    doc_id: string
}

export default function SLAViewer({ doc_id }: SLAViewerProps) {
    const [slaJson, setSlaJson] = useState<SLAJson | null>(null)
    const [fairnessScore, setFairnessScore] = useState<number | null>(null)
    const [redFlags, setRedFlags] = useState<string[]>([])
    const [openSections, setOpenSections] = useState<Set<string>>(new Set(['PAYMENT TERMS']))
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        let mounted = true
        const fetchData = async () => {
            try {
                setIsLoading(true)
                const doc = await api.documents.getById(doc_id, true)
                if (mounted) {
                    setSlaJson(doc.sla_json || null)
                    setFairnessScore(doc.contract_fairness_score ?? null)
                    setRedFlags(doc.sla_json?.red_flags || [])
                }
            } catch (error) {
                console.error("Failed to fetch SLA data", error)
            } finally {
                if (mounted) setIsLoading(false)
            }
        }
        fetchData()
        return () => { mounted = false }
    }, [doc_id])

    const toggleSection = (section: string) => {
        setOpenSections(prev => {
            const newSet = new Set(prev)
            if (newSet.has(section)) {
                newSet.delete(section)
            } else {
                newSet.add(section)
            }
            return newSet
        })
    }

    const renderField = (label: string, value: any) => (
        <div className="flex justify-between items-center py-2 border-b border-gray-800/50 dark:border-gray-800/50 light:border-gray-200/50 last:border-0" key={label}>
            <span className="text-gray-400 text-xs uppercase tracking-wide">{label.replace(/_/g, ' ')}</span>
            {value === null || value === undefined ? (
                <span className="italic text-gray-600 dark:text-gray-600 light:text-gray-400 text-xs text-right max-w-[50%]">Not found</span>
            ) : (
                <span className="text-white dark:text-white text-gray-900 text-sm font-medium text-right max-w-[50%] truncate">
                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                </span>
            )}
        </div>
    )

    if (isLoading) {
        return <div className="p-6 text-center text-gray-500 animate-pulse">Loading terms...</div>
    }

    // 1. FAIRNESS SCORE RING
    let ringColor = "#ef4444" // red
    let verdictText = "Serious Issues"
    if (fairnessScore !== null) {
        if (fairnessScore >= 80) {
            ringColor = "#22c55e"
            verdictText = "Fair Contract"
        } else if (fairnessScore >= 50) {
            ringColor = "#eab308"
            verdictText = "Some Concerns"
        }
    }

    const scoreValue = fairnessScore !== null ? fairnessScore : 0
    const strokeDashoffset = 251.2 * (1 - scoreValue / 100)

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 overflow-y-auto">
            {/* FAIRNESS SCORE RING */}
            <div className="p-6 flex flex-col items-center">
                <div className="relative w-32 h-32 mb-4">
                    <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-xl">
                        <circle
                            cx="50" cy="50" r="40"
                            className="stroke-gray-200 dark:stroke-gray-700"
                            strokeWidth="8"
                            fill="none"
                        />
                        {fairnessScore !== null && (
                            <circle
                                cx="50" cy="50" r="40"
                                stroke={ringColor}
                                strokeDasharray="251.2"
                                strokeDashoffset={strokeDashoffset}
                                strokeWidth="8"
                                strokeLinecap="round"
                                transform="rotate(-90 50 50)"
                                fill="none"
                                className="transition-all duration-1000 ease-out"
                            />
                        )}
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        {fairnessScore !== null ? (
                            <>
                                <div className="font-bold text-3xl text-gray-900 dark:text-white leading-none">{fairnessScore}</div>
                                <div className="text-xs text-gray-500 font-medium">/100</div>
                            </>
                        ) : (
                            <div className="font-bold text-xl text-gray-500">N/A</div>
                        )}
                    </div>
                </div>

                <div className="text-gray-500 dark:text-gray-400 text-sm font-medium tracking-wide uppercase mb-1">
                    Fairness Score
                </div>
                {fairnessScore !== null && (
                    <div className="font-semibold text-lg" style={{ color: ringColor }}>
                        {verdictText}
                    </div>
                )}
            </div>

            {/* RED FLAGS */}
            {redFlags && redFlags.length > 0 && (
                <div className="px-4 mb-6">
                    <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-500/50 rounded-xl p-4 shadow-sm">
                        <div className="flex items-center gap-2 mb-3">
                            <AlertTriangle className="w-5 h-5 text-red-500" />
                            <div className="font-bold text-red-700 dark:text-red-400">
                                {redFlags.length} Issue{redFlags.length !== 1 ? 's' : ''} Found
                            </div>
                        </div>
                        <ul className="space-y-2">
                            {redFlags.map((flag, idx) => (
                                <li key={idx} className="flex gap-2 text-sm text-red-800 dark:text-red-300 items-start">
                                    <span className="text-red-500 mt-0.5">•</span>
                                    <span>{flag}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* ACCORDION SECTIONS */}
            <div className="flex-1 px-4 pb-6 space-y-4">
                {[
                    {
                        title: "PAYMENT TERMS",
                        fields: ['apr', 'lease_term', 'monthly_payment', 'down_payment', 'residual_value', 'buyout_price', 'loan_term', 'loan_amount']
                    },
                    {
                        title: "MILEAGE & USAGE",
                        fields: ['mileage_allowance', 'mileage_overage_charge']
                    },
                    {
                        title: "PENALTIES & COVERAGE",
                        fields: ['early_termination_fee', 'late_fee', 'gap_coverage', 'prepayment_penalty', 'balloon_payment']
                    },
                    {
                        title: "OTHER TERMS",
                        fields: ['maintenance_responsibility', 'warranty', 'acquisition_fee', 'disposition_fee', 'vin']
                    }
                ].map(section => (
                    <div key={section.title} className="bg-gray-50 dark:bg-gray-800/50 rounded-xl overflow-hidden border border-gray-100 dark:border-gray-800 transition-all">
                        <button
                            onClick={() => toggleSection(section.title)}
                            className="w-full flex items-center justify-between p-4 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/80 transition-colors"
                        >
                            <span className="font-semibold text-gray-900 dark:text-white text-sm tracking-wide">{section.title}</span>
                            {openSections.has(section.title) ? (
                                <ChevronUp className="w-4 h-4 text-gray-500" />
                            ) : (
                                <ChevronDown className="w-4 h-4 text-gray-500" />
                            )}
                        </button>
                        {openSections.has(section.title) && (
                            <div className="p-4 pt-2 border-t border-gray-100 dark:border-gray-800 bg-white/50 dark:bg-transparent">
                                {section.fields.map(field => renderField(field, slaJson?.[field]))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}
