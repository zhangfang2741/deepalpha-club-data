import type { ConceptStock, ConceptSummary, Quote } from './types'

function backendUrl() {
  return (
    process.env.BACKEND_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL ??
    'http://localhost:8000'
  )
}

export async function getConceptList(): Promise<ConceptSummary[]> {
  const res = await fetch(`${backendUrl()}/api/v1/concept/list`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`concept/list failed: ${res.status}`)
  return res.json()
}

export async function getConceptStocks(
  name: string,
  minEtfCount = 1
): Promise<ConceptStock[]> {
  const params = new URLSearchParams({ min_etf_count: String(minEtfCount) })
  const res = await fetch(
    `${backendUrl()}/api/v1/concept/${encodeURIComponent(name)}?${params}`,
    { cache: 'no-store' }
  )
  if (!res.ok) throw new Error(`concept/${name} failed: ${res.status}`)
  return res.json()
}

export async function getQuote(symbol: string): Promise<Quote> {
  const res = await fetch(
    `${backendUrl()}/api/v1/market/quote/${symbol}`,
    { cache: 'no-store' }
  )
  if (!res.ok) throw new Error(`market/quote/${symbol} failed: ${res.status}`)
  return res.json()
}
