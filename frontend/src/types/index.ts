export interface TokenVariant {
  text: string
  language: string
  token_count: number
}

export interface Classification {
  error_type: string
  component: string
}

export interface AnalyzeResponse {
  original: TokenVariant
  translated: TokenVariant
  spanglish: TokenVariant
  classification: Classification | null
  engine_used: string
}

export interface ProjectionResponse {
  daily_token_diff: number
  monthly_token_diff: number
  monthly_savings_usd: number
}

export interface ConfigStatus {
  ollama_available: boolean
  deepl_configured: boolean
}

export interface BatchClassification {
  error_type: string
  component: string
}

export interface BatchResult {
  review: string
  tokens: number
  classification?: BatchClassification
}

export interface EconomicSummary {
  total_reviews: number
  total_tokens_processed: number
  projected_daily_tokens_10k: number
  projected_monthly_tokens_10k: number
  projected_monthly_savings_usd_10k: number
  avg_tokens_per_review: number
}

export interface BatchUploadResponse {
  results: BatchResult[]
  economic_summary: EconomicSummary
}
