'use client'

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { ConceptStock } from './types'

// ──────────────────────────────────────────────────────────
// 结果面板可显示的几种数据类型
// ──────────────────────────────────────────────────────────
export type VizResultType =
  | { kind: 'quote';          symbol: string; output: string }
  | { kind: 'concept_stocks'; concept: string; stocks: ConceptStock[] }
  | { kind: 'financials';     symbol: string; output: string }
  | { kind: 'concepts';       output: string }
  | null

export interface VizState {
  /** 蜡烛图当前显示的股票/ETF 代码 */
  activeSymbol: string | null
  /** 结果面板当前数据 */
  result: VizResultType
}

interface VizContextValue extends VizState {
  setActiveSymbol: (symbol: string) => void
  setResult: (r: VizResultType) => void
}

const VizContext = createContext<VizContextValue | null>(null)

export function VizProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<VizState>({
    activeSymbol: null,
    result: null,
  })

  const setActiveSymbol = useCallback((symbol: string) => {
    setState(prev => ({ ...prev, activeSymbol: symbol.toUpperCase() }))
  }, [])

  const setResult = useCallback((result: VizResultType) => {
    setState(prev => ({ ...prev, result }))
  }, [])

  return (
    <VizContext.Provider value={{ ...state, setActiveSymbol, setResult }}>
      {children}
    </VizContext.Provider>
  )
}

export function useViz() {
  const ctx = useContext(VizContext)
  if (!ctx) throw new Error('useViz must be used inside VizProvider')
  return ctx
}
