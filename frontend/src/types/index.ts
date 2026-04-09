export interface User {
  id: number
  email: string
  full_name?: string
  phone?: string
  created_at: string
}

export interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
}

export interface Contract {
  id: number
  contract_type?: 'lease' | 'loan'
  doc_status: 'uploaded' | 'processing' | 'extracted' | 'failed'
  dealer_offer_name?: string
  contract_date?: string
  fairness_score?: number
  red_flag_level?: string
  notes?: string
  created_at: string
}

export interface SLA {
  id: number
  contract_id: number
  apr_percent?: number
  money_factor?: number
  term_months?: number
  monthly_payment?: number
  down_payment?: number
  fees_total?: number
  residual_value?: number
  residual_percent_msrp?: number
  msrp?: number
  cap_cost?: number
  cap_cost_reduction?: number
  mileage_allowance_yr?: number
  mileage_overage_fee?: number
  early_termination_fee?: number
  disposition_fee?: number
  purchase_option_price?: number
  insurance_requirements?: string
  maintenance_resp?: string
  warranty_summary?: string
  late_fee_policy?: string
  other_terms?: Record<string, unknown>
}

export interface ExtractedClause {
  id: number
  clause_type?: string
  page_number?: number
  text_snippet?: string
  normalized_value?: unknown
  red_flag_level?: string
  comment?: string
}

export interface Vehicle {
  id: number
  vin?: string
  year?: number
  make?: string
  model?: string
  trim?: string
  body_class?: string
  fuel_type?: string
}

export interface Recall {
  recall_number?: string
  issue_date?: string
  component?: string
  summary?: string
  remedy?: string
}

export interface VINReport {
  vehicle: Vehicle
  recalls: Recall[]
}

export interface NegotiationMessage {
  id: number
  sender_role: 'user' | 'assistant' | 'dealer'
  body: string
  suggested_text?: string
  sent_at: string
}

export interface NegotiationThread {
  id: number
  subject?: string
  created_at: string
  messages: NegotiationMessage[]
}

export interface ChatResponse {
  thread_id: number
  response: string
  suggested_message?: string
}

export interface PriceRecommendation {
  vehicle_id: number
  geo_postal?: string
  msrp?: number
  fair_price_low?: number
  fair_price_high?: number
  basis?: string
  methodology?: string
}

export interface CompareResult {
  primary: SLA
  compared: SLA
  analysis: string
  winner: string
}