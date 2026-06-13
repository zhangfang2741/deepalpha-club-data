export interface ConceptSummary {
  concept: string
  concept_name_zh: string | null
  etf_count: number
  stock_count: number
  top_symbols: string[]
  last_updated: string
}

export interface ConceptEtf {
  concept: string
  etf_symbol: string
  etf_name: string | null
  etf_name_zh: string | null
  description_zh: string | null
  aum_million: number | null
  concept_name_zh: string | null
}

export interface ConceptStock {
  date: string
  concept: string
  symbol: string
  name: string | null
  etf_count: number
  total_weight: number
  etfs: string[]
}

export interface IncomeStatement {
  symbol: string
  date: string
  period: string
  revenue: number | null
  grossProfit: number | null
  operatingIncome: number | null
  netIncome: number | null
  eps: number | null
  epsDiluted: number | null
  ebitda: number | null
}

export interface Quote {
  symbol: string
  name: string | null
  price: number
  change: number
  changesPercentage: number | null
  marketCap: number | null
  dayLow: number | null
  dayHigh: number | null
  yearHigh: number | null
  yearLow: number | null
  volume: number | null
  open: number | null
  previousClose: number | null
  pe: number | null
}

export interface OHLCVBar {
  t: string   // YYYY-MM-DD
  o: number
  h: number
  l: number
  c: number
  v: number
}

export interface DailyThemeScore {
  theme_name: string
  category: 'tech_concept' | 'infra_component' | 'engineering_concept'
  score_date: string
  base_score: number
  momentum: number
  final_score: number
  cumulative_score: number
  company_count: number
  signal_breakdown: Record<string, number>
}
