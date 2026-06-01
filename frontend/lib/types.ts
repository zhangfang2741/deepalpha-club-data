export interface ConceptSummary {
  concept: string
  etf_count: number
  stock_count: number
  top_symbols: string[]
  last_updated: string
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

export interface Quote {
  symbol: string
  name: string | null
  price: number
  change: number
  changesPercentage: number | null
  marketCap: number | null
}
