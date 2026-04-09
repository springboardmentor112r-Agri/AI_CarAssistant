import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle } from 'lucide-react'
import { contractsApi } from '../api'
import toast from 'react-hot-toast'
import Spinner from '../components/ui/Spinner'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [offerName, setOfferName] = useState('')
  const [uploading, setUploading] = useState(false)
  const navigate = useNavigate()

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  })

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const contract = await contractsApi.upload(file, offerName || file.name)
      toast.success('Contract uploaded! AI analysis starting...')
      navigate(`/contracts/${contract.id}`)
    } catch {
      toast.error('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Upload Contract</h1>
      <p className="text-slate-500 mb-8">
        Upload your car lease or loan contract for AI analysis.
        We accept all common formats.
      </p>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors mb-6 ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-slate-300 hover:border-primary-400 hover:bg-slate-50'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <CheckCircle size={28} className="text-green-500" />
            <div className="text-left">
              <p className="font-medium text-slate-900">{file.name}</p>
              <p className="text-sm text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null) }}
              className="ml-2 p-1 text-slate-400 hover:text-red-500 rounded"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <>
            <Upload size={40} className="mx-auto mb-3 text-slate-300" />
            <p className="font-medium text-slate-600">
              {isDragActive ? 'Drop it here!' : 'Drag & drop your contract'}
            </p>
            <p className="text-sm text-slate-400 mt-1">
              or click to browse
            </p>
          </>
        )}
      </div>

      {/* Accepted formats */}
      <div className="grid grid-cols-4 gap-2 mb-6">
        {[
          { ext: 'PDF', desc: 'Digital PDF', color: 'bg-red-50 text-red-700 border-red-200' },
          { ext: 'Scanned', desc: 'Scanned PDF', color: 'bg-orange-50 text-orange-700 border-orange-200' },
          { ext: 'Image', desc: 'JPG / PNG', color: 'bg-blue-50 text-blue-700 border-blue-200' },
          { ext: 'TXT', desc: 'Plain Text', color: 'bg-green-50 text-green-700 border-green-200' },
        ].map(({ ext, desc, color }) => (
          <div key={ext} className={`border rounded-lg p-3 text-center ${color}`}>
            <p className="font-bold text-sm">{ext}</p>
            <p className="text-xs mt-0.5">{desc}</p>
          </div>
        ))}
      </div>

      {/* Offer name */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Offer Name <span className="text-slate-400">(optional)</span>
        </label>
        <input
          className="input"
          placeholder="e.g. Toyota Dealer Offer June 2025"
          value={offerName}
          onChange={(e) => setOfferName(e.target.value)}
        />
      </div>

      {/* What happens next */}
      <div className="card p-4 mb-6 bg-blue-50 border-blue-200">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">
          What happens after upload?
        </h3>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>OCR extracts text from your document</li>
          <li>Gemini AI identifies all key contract fields</li>
          <li>Red flags and fairness score are calculated</li>
          <li>Plain language summary is generated</li>
          <li>You get a full breakdown in ~30 seconds</li>
        </ol>
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="btn-primary w-full justify-center py-3 text-base"
      >
        {uploading
          ? <><Spinner className="text-white" /> Uploading & Analyzing...</>
          : <><FileText size={18} /> Analyze Contract</>
        }
      </button>
    </div>
  )
}