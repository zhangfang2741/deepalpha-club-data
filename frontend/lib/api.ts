import type { ConceptEtf, ConceptStock, ConceptSummary, DailyThemeScore, IncomeStatement, OHLCVBar, Quote } from './types'

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

export interface ConceptAnalysis {
  products: string
  position: string
  competition: string
  supply_chain: string
  ecosystem: string
}

export async function getConceptAnalysis(name: string): Promise<ConceptAnalysis> {
  const res = await fetch(
    `${backendUrl()}/api/v1/concept/${encodeURIComponent(name)}/analysis`,
    { cache: 'no-store' }
  )
  if (!res.ok) throw new Error(`concept/${name}/analysis failed: ${res.status}`)
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

export async function getRadarLeaderboard(
  date?: string,
  window = '30d',
  category = 'all',
  limit = 50
): Promise<DailyThemeScore[]> {
  const params = new URLSearchParams({ window, category, limit: String(limit) })
  if (date) params.set('date', date)
  const res = await fetch(`${backendUrl()}/api/v1/signal-radar/leaderboard?${params}`, { cache: 'no-store' })
  if (!res.ok) return []
  return res.json()
}

export async function getRadarTrend(
  themeName: string,
  from: string,
  to: string
): Promise<DailyThemeScore[]> {
  const params = new URLSearchParams({ from, to })
  const res = await fetch(
    `${backendUrl()}/api/v1/signal-radar/trend/${encodeURIComponent(themeName)}?${params}`,
    { cache: 'no-store' }
  )
  if (!res.ok) return []
  return res.json()
}

export async function searchRadarThemes(q: string, limit = 20): Promise<string[]> {
  const params = new URLSearchParams({ q, limit: String(limit) })
  const res = await fetch(`${backendUrl()}/api/v1/signal-radar/themes?${params}`, { cache: 'no-store' })
  if (!res.ok) return []
  return res.json()
}

export interface ThemeSignal {
  ticker: string
  source_type: string
  signal_date: string
  sec_url: string
  text_snippet: string
  confidence: number
}

export async function getThemeSignals(
  themeName: string,
  from?: string,
  to?: string,
  limit = 50
): Promise<ThemeSignal[]> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  const res = await fetch(
    `${backendUrl()}/api/v1/signal-radar/theme/${encodeURIComponent(themeName)}/signals?${params}`,
    { cache: 'no-store' }
  )
  if (!res.ok) return []
  return res.json()
}

export interface ThemeAnalysis {
  products: string
  position: string
  competition: string
  supply_chain: string
  ecosystem: string
}

export async function getThemeAnalysis(
  themeName: string,
  from?: string,
  to?: string,
  limit = 50
): Promise<ThemeAnalysis> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (from) params.set('from', from)
  if (to) params.set('to', to)

  // 使用专用 API route（绕过 Next.js rewrite 代理的 30 秒超时限制）
  const url = typeof window !== 'undefined'
    ? `/api/signal-radar/analysis/${encodeURIComponent(themeName)}?${params}`
    : `${process.env.BACKEND_URL ?? 'http://localhost:8000'}/api/v1/signal-radar/theme/${encodeURIComponent(themeName)}/analysis?${params}`

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 4 * 60 * 1000) // 4分钟超时
  try {
    const res = await fetch(url, { cache: 'no-store', signal: controller.signal })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`HTTP ${res.status}${text ? ': ' + text.slice(0, 200) : ''}`)
    }
    return res.json()
  } finally {
    clearTimeout(timer)
  }
}
