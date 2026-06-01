import type { ConceptEtf, ConceptStock, ConceptSummary, IncomeStatement, OHLCVBar, Quote } from './types'

function backendUrl() {
  if (typeof window !== 'undefined') return '' // 浏览器：走 Next.js rewrite proxy
  return process.env.BACKEND_URL ?? 'http://localhost:8000' // 服务端：直连后端
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

export async function getConceptEtfs(name: string): Promise<ConceptEtf[]> {
  const res = await fetch(
    `${backendUrl()}/api/v1/concept/${encodeURIComponent(name)}/etfs`,
    { cache: 'no-store' }
  )
  if (res.status === 404) return []
  if (!res.ok) throw new Error(`concept/${name}/etfs failed: ${res.status}`)
  return res.json()
}

export async function getIncomeStatement(symbol: string): Promise<IncomeStatement | null> {
  const res = await fetch(
    `${backendUrl()}/api/v1/financial/${symbol}/income`,
    { cache: 'no-store' }
  )
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`financial/${symbol}/income failed: ${res.status}`)
  return res.json()
}

export async function getOHLCV(symbol: string, months = 3): Promise<OHLCVBar[]> {
  const res = await fetch(
    `${backendUrl()}/api/v1/market/history/${symbol}?months=${months}`,
    { cache: 'no-store' }
  )
  if (!res.ok) return []
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
