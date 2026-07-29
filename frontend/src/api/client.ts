import axios from 'axios'
import type { AnalyzeResponse, ProjectionResponse, ConfigStatus, BatchUploadResponse } from '../types'

const api = axios.create({ baseURL: '/api' })

export async function analyzeText(
  text: string,
  engine: string,
  deeplApiKey: string,
  classify = false,
): Promise<AnalyzeResponse> {
  const resp = await api.post('/analyze', { text, engine, classify }, {
    headers: deeplApiKey ? { 'deepl-api-key': deeplApiKey } : undefined,
  })
  return resp.data
}

export async function getConfigStatus(): Promise<ConfigStatus> {
  const resp = await api.get('/config/status')
  return resp.data
}

export async function computeProjection(
  tokensOriginal: number,
  tokensTranslated: number,
  reviewsPerDay = 10000,
  costPerMillion = 2.5,
  days = 30,
): Promise<ProjectionResponse> {
  const resp = await api.post('/analyze/projection', {
    tokens_original: tokensOriginal,
    tokens_translated: tokensTranslated,
    reviews_per_day: reviewsPerDay,
    cost_per_million_tokens_usd: costPerMillion,
    days,
  })
  return resp.data
}

export async function uploadExcel(
  file: File,
  optentTokens: boolean,
  engine: string,
  deeplApiKey: string,
): Promise<BatchUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('optent_tokens', String(optentTokens))
  form.append('engine', engine)
  const resp = await api.post('/batch/upload', form, {
    headers: deeplApiKey ? { 'deepl-api-key': deeplApiKey } : undefined,
  })
  return resp.data
}

export async function processFolder(
  folderPath: string,
  optentTokens: boolean,
  engine: string,
  deeplApiKey: string,
): Promise<BatchUploadResponse> {
  const resp = await api.post('/batch/folder', {
    folder_path: folderPath,
    optent_tokens: optentTokens,
    engine,
  }, {
    headers: deeplApiKey ? { 'deepl-api-key': deeplApiKey } : undefined,
  })
  return resp.data
}

