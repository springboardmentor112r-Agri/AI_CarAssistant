import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileText, Trash2, Plus, AlertTriangle } from 'lucide-react'
import { contractsApi } from '../api'
import { Contract } from '../types'
import toast from 'react-hot-toast'
import Spinner from '../components/ui/Spinner'

export default function ContractsPage() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['contracts'],
    queryFn: contractsApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => contractsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      toast.success('Contract deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete contract')
    },
  })

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.preventDefault()
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this contract?')) {
      deleteMutation.mutate(id)
    }
  }

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>

  const contracts = data?.contracts ?? []

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Contracts</h1>
          <p className="text-slate-500 text-sm mt-1">{contracts.length} contract{contracts.length !== 1 ? 's' : ''} uploaded</p>
        </div>
        <Link to="/contracts/upload" className="btn-primary">
          <Plus size={16} /> Upload New
        </Link>
      </div>

      {contracts.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText size={48} className="mx-auto mb-4 text-slate-300" />
          <h3 className="font-semibold text-slate-600 mb-2">No contracts yet</h3>
          <p className="text-slate-400 text-sm mb-6">Upload your first car lease or loan contract to get started</p>
          <Link to="/contracts/upload" className="btn-primary">
            <Plus size={16} /> Upload Contract
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {contracts.map((contract: Contract) => (
            <Link
              key={contract.id}
              to={`/contracts/${contract.id}`}
              className="card p-5 flex items-center gap-4 hover:shadow-md transition-shadow"
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                contract.doc_status === 'extracted' ? 'bg-green-100' :
                contract.doc_status === 'failed' ? 'bg-red-100' : 'bg-yellow-100'
              }`}>
                <FileText size={20} className={
                  contract.doc_status === 'extracted' ? 'text-green-600' :
                  contract.doc_status === 'failed' ? 'text-red-600' : 'text-yellow-600'
                } />
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-900 truncate">
                  {contract.dealer_offer_name || `Contract #${contract.id}`}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`badge-${
                    contract.doc_status === 'extracted' ? 'green' :
                    contract.doc_status === 'failed' ? 'red' : 'yellow'
                  }`}>
                    {contract.doc_status}
                  </span>
                  {contract.contract_type && (
                    <span className="text-xs text-slate-400 uppercase">{contract.contract_type}</span>
                  )}
                  <span className="text-xs text-slate-400">
                    {new Date(contract.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {contract.fairness_score != null && (
                <div className="text-center shrink-0">
                  <div className={`text-lg font-bold ${
                    contract.fairness_score >= 70 ? 'text-green-600' :
                    contract.fairness_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {contract.fairness_score}
                  </div>
                  <div className="text-xs text-slate-400">score</div>
                </div>
              )}

              {contract.red_flag_level === 'high' && (
                <AlertTriangle size={18} className="text-red-500 shrink-0" />
              )}

              <button
                onClick={(e) => handleDelete(e, contract.id)}
                disabled={deleteMutation.isPending}
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors shrink-0"
              >
                {deleteMutation.isPending ? <Spinner className="w-4 h-4" /> : <Trash2 size={16} />}
              </button>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}