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
  tokens_original: number
  text_en: string
  tokens_en: number
  cost_original_usd: number
  cost_en_usd: number
  best_lang: string
  justification: string
  classification?: BatchClassification
  frequency?: number
  product_name?: string
  stars?: number
}

export interface EconomicSummary {
  total_reviews: number
  total_tokens_original: number
  total_tokens_en: number
  avg_tokens_original: number
  avg_tokens_en: number
  daily_cost_original_10k: number
  daily_cost_en_10k: number
  daily_savings_10k: number
  weekly_savings_10k: number
  monthly_savings_10k: number
  best_global_lang: string
}

export interface BatchUploadResponse {
  results: BatchResult[]
  economic_summary: EconomicSummary
  product_ratings?: Record<string, number>
}
