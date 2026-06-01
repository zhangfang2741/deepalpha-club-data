// hooks/use-concept.ts
import useSWR from 'swr'
import { getConceptList, getConceptStocks } from '@/lib/api'
import type { ConceptStock, ConceptSummary } from '@/lib/types'

export function useConceptList() {
  return useSWR<ConceptSummary[]>('concept-list', getConceptList, {
    revalidateOnFocus: false,
    dedupingInterval: 60_000,
  })
}

export function useConceptStocks(name: string | null, minEtfCount = 1) {
  return useSWR<ConceptStock[]>(
    name ? `concept-stocks:${name}:${minEtfCount}` : null,
    () => getConceptStocks(name!, minEtfCount),
    { revalidateOnFocus: false, dedupingInterval: 60_000 }
  )
}
