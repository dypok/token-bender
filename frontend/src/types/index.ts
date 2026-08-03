export interface ConfigStatus {
  engine: string
  model_ready: boolean
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
  classification?: {
    error_type: string
    component: string
  } | null
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
