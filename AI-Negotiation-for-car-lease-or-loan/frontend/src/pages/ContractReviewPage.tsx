import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Search, X, Copy, Check, MessageSquare, Car, BarChart2, ArrowLeft } from 'lucide-react'
import { api } from '../services/api'
import { DocumentDetail } from '../types'
import SLAViewer from '../components/SLAViewer'
import Navbar from '../components/Navbar'

export default function ContractReviewPage() {
  const { doc_id } = useParams<{ doc_id: string }>()
  const navigate = useNavigate()

  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let mounted = true
    const fetchDoc = async () => {
      if (!doc_id) return
      try {
        setIsLoading(true)
        const doc = await api.documents.getById(doc_id, true)
        if (mounted) setDocument(doc)
      } catch (err) {
        console.error("Failed to fetch document details", err)
      } finally {
        if (mounted) setIsLoading(false)
      }
    }
    fetchDoc()
    return () => { mounted = false }
  }, [doc_id])

  const handleCopy = async () => {
    if (!document?.raw_extracted_text) return
    try {
      await navigator.clipboard.writeText(document.raw_extracted_text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text', err)
    }
  }

  // Text highlighting logic
  const { highlightedText, matchCount }: { highlightedText: React.ReactNode | string, matchCount: number } = useMemo(() => {
    const text = document?.raw_extracted_text || ''
    if (!searchTerm.trim()) return { highlightedText: text, matchCount: 0 }

    // Case-insensitive regex search
    const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')
    const regex = new RegExp(`(${escapedTerm})`, 'gi')

    const parts = text.split(regex)
    let count = 0

    const elements = parts.map((part, i) => {
      // The split regex puts the matched capture group in odd indices
      if (i % 2 === 1) {
        count++
        return <mark key={i} className="bg-yellow-400 text-black rounded px-0.5">{part}</mark>
      }
      return <span key={i}>{part}</span>
    })

    return { highlightedText: elements, matchCount: count }
  }, [document?.raw_extracted_text, searchTerm])

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden max-w-[1600px] w-full mx-auto">
        {/* LEFT PANEL */}
        <div className="w-full md:w-2/5 flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="p-4 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-10 bg-white dark:bg-gray-900 flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-500" />
            </button>
            <h2 className="font-semibold text-gray-900 dark:text-white">Contract Analysis</h2>
          </div>

          <div className="flex-1 overflow-hidden">
            {doc_id && <SLAViewer doc_id={doc_id} />}
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-gray-950">
          {/* TOOLBAR */}
          <div className="p-3 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3 sticky top-0 z-10 bg-white dark:bg-gray-900">
            <div className="flex-1 relative flex items-center">
              <Search className="w-4 h-4 absolute left-3 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search in contract..."
                className="w-full bg-gray-100 dark:bg-gray-800 border-none rounded-lg py-2 pl-9 pr-8 text-sm focus:ring-2 focus:ring-blue-500/50 text-gray-900 dark:text-white"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {searchTerm && (
              <div className="text-xs text-gray-500 whitespace-nowrap">
                {matchCount} match{matchCount !== 1 ? 'es' : ''}
              </div>
            )}

            <button
              onClick={handleCopy}
              className="group relative flex items-center gap-1.5 px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-green-500" />
                  <span className="text-green-600 dark:text-green-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>

          {/* TEXT VIEWER */}
          <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-950 text-gray-700 dark:text-gray-300 font-mono text-sm leading-relaxed whitespace-pre-wrap">
            {isLoading ? (
              <div className="flex justify-center py-10 animate-pulse text-gray-400">Loading text...</div>
            ) : !document?.raw_extracted_text ? (
              <div className="flex justify-center py-20 text-gray-500 italic">Contract text not available.</div>
            ) : (
              highlightedText
            )}
          </div>

          {/* BOTTOM ACTION BAR */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex flex-wrap sm:flex-nowrap gap-3 items-center">
            <button
              onClick={() => navigate(`/chat/${doc_id}`)}
              className="flex-1 min-w-[200px] flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-sm"
            >
              <MessageSquare className="w-5 h-5" />
              Start Negotiation
            </button>
            <div className="flex-1 sm:flex-none flex w-full sm:w-auto gap-3">
              <button
                disabled={!document?.sla_json?.vin && !document?.vin}
                onClick={() => {
                  const vin = document?.sla_json?.vin || document?.vin
                  if (vin) navigate(`/vin/${vin}`)
                }}
                title={(!document?.sla_json?.vin && !document?.vin) ? "No VIN found in contract" : ""}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 dark:text-gray-300 rounded-xl font-medium transition-colors"
              >
                <Car className="w-5 h-5" />
                <span className="hidden sm:inline">VIN Report</span>
              </button>
              <button
                onClick={() => navigate('/compare')}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-300 rounded-xl font-medium transition-colors"
              >
                <BarChart2 className="w-5 h-5" />
                <span className="hidden sm:inline">Compare</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
