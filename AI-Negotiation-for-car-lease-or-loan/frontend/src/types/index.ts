export interface UserRead {
    user_id: string;
    email: string;
    full_name: string | null;
    created_at: string;
    is_active: boolean;
}

export interface SLAJson {
    apr?: number | string | null;
    lease_term?: number | string | null;
    monthly_payment?: number | string | null;
    down_payment?: number | string | null;
    residual_value?: number | string | null;
    buyout_price?: number | string | null;
    loan_term?: number | string | null;
    loan_amount?: number | string | null;
    mileage_allowance?: number | string | null;
    mileage_overage_charge?: number | string | null;
    early_termination_fee?: number | string | null;
    late_fee?: number | string | null;
    gap_coverage?: string | null;
    prepayment_penalty?: string | null;
    balloon_payment?: string | null;
    maintenance_responsibility?: string | null;
    warranty?: string | null;
    acquisition_fee?: number | string | null;
    disposition_fee?: number | string | null;
    vin?: string | null;
    [key: string]: any;
}

export interface DocumentRead {
    doc_id: string;
    user_id: string;
    filename: string;
    sla_json?: SLAJson | null;
    contract_fairness_score?: number | null;
    vin?: string | null;
    upload_timestamp: string;
    processing_status: string;
    sla_retry_count: number;
    error_message?: string | null;
    sla_progress?: {
        step: number;
        total: number;
        message: string;
    } | null;
}

export interface DocumentDetail extends DocumentRead {
    raw_extracted_text?: string | null;
}

export interface ThreadSummary {
    thread_id: string;
    first_message_preview: string;
    last_updated: string;
}

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    isStreaming?: boolean;
}
