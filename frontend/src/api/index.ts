import api from './client'
import {
  User, Contract, SLA, ExtractedClause,
  VINReport, ChatResponse, NegotiationThread,
  PriceRecommendation, CompareResult,
} from '../types'

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: async (email: string, password: string, full_name?: string) => {
    const { data } = await api.post('/api/auth/register', { email, password, full_name })
    return data as { access_token: string; user: User }
  },
  login: async (email: string, password: string) => {
    const { data } = await api.post('/api/auth/login', { email, password })
    return data as { access_token: string; user: User }
  },
  me: async () => {
    const { data } = await api.get('/api/auth/me')
    return data as User
  },
}

// ── Contracts ─────────────────────────────────────────────────────────────────
export const contractsApi = {
  list: async () => {
    const { data } = await api.get('/api/contracts')
    return data as { contracts: Contract[]; total: number }
  },
  get: async (id: number) => {
    const { data } = await api.get(`/api/contracts/${id}`)
    return data as Contract
  },
  upload: async (file: File, dealerOfferName?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (dealerOfferName) form.append('dealer_offer_name', dealerOfferName)
    const { data } = await api.post('/api/contracts/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data as Contract
  },
  getSLA: async (id: number) => {
    const { data } = await api.get(`/api/contracts/${id}/sla`)
    return data as SLA
  },
  getClauses: async (id: number) => {
    const { data } = await api.get(`/api/contracts/${id}/clauses`)
    return data as ExtractedClause[]
  },
  delete: async (id: number) => {
    await api.delete(`/api/contracts/${id}`)
  },
}

// ── VIN ───────────────────────────────────────────────────────────────────────
export const vinApi = {
  lookup: async (vin: string) => {
    const { data } = await api.get(`/api/vin/${vin}`)
    return data as VINReport
  },
}

// ── Negotiation ───────────────────────────────────────────────────────────────
export const negotiationApi = {
  chat: async (message: string, contractId?: number, threadId?: number) => {
    const { data } = await api.post('/api/negotiation/chat', {
      message,
      contract_id: contractId,
      thread_id: threadId,
    })
    return data as ChatResponse
  },
  listThreads: async () => {
    const { data } = await api.get('/api/negotiation/threads')
    return data as NegotiationThread[]
  },
  getThread: async (threadId: number) => {
    const { data } = await api.get(`/api/negotiation/threads/${threadId}`)
    return data as NegotiationThread
  },
}

// ── Price ─────────────────────────────────────────────────────────────────────
export const priceApi = {
  estimate: async (vehicleId: number, postalCode?: string) => {
    const { data } = await api.get(`/api/price/estimate/${vehicleId}`, {
      params: { postal_code: postalCode },
    })
    return data as PriceRecommendation
  },
  compare: async (primaryId: number, comparedId: number) => {
    const { data } = await api.post('/api/price/compare', {
      primary_contract_id: primaryId,
      compared_contract_id: comparedId,
    })
    return data as CompareResult
  },
}