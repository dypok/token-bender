export const fmtMoney = (v: number) =>
  `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

export const fmtInt = (v: number) => v.toLocaleString('en-US')

export const bestLangLabel = (best: string) =>
  best === 'en' ? 'Inglés' : best === 'es' ? 'Español' : 'Igual'
