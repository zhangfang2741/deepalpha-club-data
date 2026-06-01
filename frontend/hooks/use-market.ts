// hooks/use-market.ts
import useSWR from 'swr'
import { getQuote } from '@/lib/api'
import type { Quote } from '@/lib/types'

export function useQuote(symbol: string | null) {
  return useSWR<Quote>(
    symbol ? `quote:${symbol}` : null,
    () => getQuote(symbol!),
    { refreshInterval: 30_000 }
  )
}
