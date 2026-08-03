import * as XLSX from 'xlsx'
import type { BatchResult, EconomicSummary } from '../types'

function buildIntentionSheet(res: BatchResult[]) {
  const rows = res.map((r) => ({
    'Producto': r.product_name || 'General',
    'Intención (Calificación)': `${'⭐'.repeat(r.stars || 3)} (${r.stars || 3}/5)`,
    'Reseña Resumen (Español)': r.review,
    'Traducción Resumen (Inglés)': r.text_en,
    'Cantidad Reseñas Agrupadas': r.frequency || 1,
    'Tokens Resumen ES': r.tokens_original,
    'Tokens Resumen EN': r.tokens_en,
    'Mejor idioma': r.best_lang === 'en' ? 'Inglés' : r.best_lang === 'es' ? 'Español' : 'Igual',
  }))
  return XLSX.utils.json_to_sheet(rows)
}

function buildRatingsSheet(ratings: Record<string, number>) {
  const rows = Object.entries(ratings).map(([prod, rating]) => ({
    'Producto / Aplicación': prod,
    'Rating Promedio (1-5 Estrellas)': `${rating} ⭐`,
    'Estado': rating >= 4.0 ? 'Excelente' : rating >= 3.0 ? 'Aceptable' : 'Atención Requerida',
  }))
  return XLSX.utils.json_to_sheet(rows)
}

function buildProjectionSheet(res: BatchResult[], sum: EconomicSummary) {
  return XLSX.utils.json_to_sheet([
    { Métrica: 'Total reseñas procesadas', Valor: sum.total_reviews },
    { Métrica: 'Clusters semánticos identificados', Valor: res.length },
    { Métrica: 'Total tokens (original)', Valor: sum.total_tokens_original },
    { Métrica: 'Total tokens (inglés)', Valor: sum.total_tokens_en },
    { Métrica: 'Ahorro diario (10k res/día)', Valor: `$${sum.daily_savings_10k}` },
    { Métrica: 'Ahorro mensual (10k res/día)', Valor: `$${sum.monthly_savings_10k}` },
  ])
}

export function downloadExcel(
  results: BatchResult[],
  summary: EconomicSummary | null,
  ratings?: Record<string, number>,
  filename = 'resumen_ejecutivo_costos.xlsx',
) {
  const wb = XLSX.utils.book_new()

  XLSX.utils.book_append_sheet(wb, buildIntentionSheet(results), 'Resumen de Intenciones')

  if (ratings && Object.keys(ratings).length > 0) {
    XLSX.utils.book_append_sheet(wb, buildRatingsSheet(ratings), 'Rating 5 Estrellas por Producto')
  }

  if (summary) {
    XLSX.utils.book_append_sheet(wb, buildProjectionSheet(results, summary), 'Proyección económica')
  }

  XLSX.writeFile(wb, filename)
}
