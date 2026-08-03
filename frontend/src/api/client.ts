import axios from 'axios'
import type { ConfigStatus, BatchUploadResponse } from '../types'

const api = axios.create({ baseURL: '/api' })

export async function getConfigStatus(): Promise<ConfigStatus> {
  const resp = await api.get('/config/status')
  return resp.data
}

export async function startBatch(
  file: File,
  optentTokens: boolean,
): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  form.append('optent_tokens', String(optentTokens))
  const resp = await api.post('/batch/start', form)
  return resp.data.task_id
}

export async function getBatchProgress(taskId: string): Promise<{
  logs: string[]
  done: boolean
  result: BatchUploadResponse | null
}> {
  const resp = await api.get(`/batch/progress/${taskId}`)
  return resp.data
}

export async function processFolder(
  files: File[],
  optentTokens: boolean,
): Promise<BatchUploadResponse> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  form.append('optent_tokens', String(optentTokens))
  const resp = await api.post('/batch/folder', form)
  return resp.data
}
