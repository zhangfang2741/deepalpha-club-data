'use client'

import { useViz } from '@/lib/viz-context'
import useSWR from 'swr'
import { getOHLCV, getQuote } from '@/lib/api'
import { CandlestickChart } from './CandlestickChart'
import { ResultsPanel } from './ResultsPanel'
import type { OHLCVBar, Quote } from '@/lib/types'

function PeriodBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-2 py-0.5 rounded text-[10px] transition-all duration-150"
      style={{
        background: active ? 'rgba(34,211,238,0.15)' : 'transparent',
        color: active ? 'rgb(34,211,238)' : 'rgb(72,90,130)',
        border: `1px solid ${active ? 'rgba(34,211,238,0.3)' : 'transparent'}`,
        fontFamily: 'var(--font-ibm-mono)',
      }}
    >
      {label}
    </button>
  )
}

function ChartSection({ symbol }: { symbol: string }) {
  const periods = [
    { label: '1M', months: 1 },
    { label: '3M', months: 3 },
    { label: '6M', months: 6 },
    { label: '1Y', months: 12 },
  ]
  const [activePeriod, setActivePeriod] = useSWRState(3)

  const { data: bars, isLoading } = useSWR<OHLCVBar[]>(
    `ohlcv-${symbol}-${activePeriod}`,
    () => getOHLCV(symbol, activePeriod),
    { revalidateOnFocus: false }
  )

  const { data: quote } = useSWR<Quote>(
    `quote-${symbol}`,
    () => getQuote(symbol),
    { revalidateOnFocus: false, refreshInterval: 60000 }
  )

  const last = bars?.[bars.length - 1]
  const isUp = last ? last.c >= last.o : true
  const changeFromOpen = last ? ((last.c - last.o) / last.o * 100) : 0

  return (
    <div className="flex flex-col h-full">
      {/* 股票信息栏 */}
      <div
        className="flex items-center gap-4 px-4 py-2.5 shrink-0"
        style={{ borderBottom: '1px solid rgba(99,130,190,0.08)' }}
      >
        <div>
          <span
            className="text-sm font-bold tracking-wide"
            style={{ fontFamily: 'var(--font-bricolage)', color: 'rgb(34,211,238)' }}
          >
            {symbol}
          </span>
          {quote?.name && (
            <span className="ml-2 text-xs" style={{ color: 'rgb(100,120,160)' }}>
              {quote.name}
            </span>
          )}
        </div>

        {quote && (
          <>
            <span
              className="text-lg font-semibold tabular-nums"
              style={{ fontFamily: 'var(--font-ibm-mono)', color: 'rgb(225,235,255)' }}
            >
              ${quote.price.toFixed(2)}
            </span>
            <span
              className="text-xs tabular-nums px-2 py-0.5 rounded"
              style={{
                fontFamily: 'var(--font-ibm-mono)',
                color: (quote.changesPercentage ?? 0) >= 0 ? 'rgb(52,211,153)' : 'rgb(251,113,133)',
                background: (quote.changesPercentage ?? 0) >= 0 ? 'rgba(52,211,153,0.1)' : 'rgba(251,113,133,0.1)',
              }}
            >
              {(quote.changesPercentage ?? 0) >= 0 ? '+' : ''}{(quote.changesPercentage ?? 0).toFixed(2)}%
            </span>
            {quote.marketCap && (
              <span className="text-[10px] ml-auto" style={{ color: 'rgb(72,90,130)' }}>
                市值 ${(quote.marketCap / 1e9).toFixed(1)}B
              </span>
            )}
          </>
        )}

        {/* 周期切换 */}
        <div className="flex gap-0.5 ml-2">
          {periods.map(p => (
            <PeriodBtn
              key={p.months}
              label={p.label}
              active={activePeriod === p.months}
              onClick={() => setActivePeriod(p.months)}
            />
          ))}
        </div>
      </div>

      {/* 蜡烛图 */}
      <div className="flex-1 min-h-0 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex gap-1">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="h-1.5 w-1.5 rounded-full"
                  style={{
                    background: 'rgb(34,211,238)',
                    animation: `pulse-dot 0.9s ease-in-out ${i * 0.15}s infinite`,
                  }}
                />
              ))}
            </div>
          </div>
        )}
        {bars && bars.length > 0 && (
          <CandlestickChart bars={bars} symbol={symbol} />
        )}
      </div>
    </div>
  )
}

// 简单的本地 state hook（避免引入额外依赖）
import { useState as _useState } from 'react'
function useSWRState<T>(initial: T): [T, (v: T) => void] {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  return _useState<T>(initial)
}

export function VizPanel() {
  const { activeSymbol, result } = useViz()

  return (
    <div className="flex flex-col h-full" style={{ background: 'rgb(10,18,38)' }}>

      {/* ── 上方：蜡烛图区 ── */}
      <div
        className="shrink-0"
        style={{
          height: '55%',
          borderBottom: '1px solid rgba(99,130,190,0.10)',
        }}
      >
        {activeSymbol ? (
          <ChartSection symbol={activeSymbol} />
        ) : (
          <WelcomeChart />
        )}
      </div>

      {/* ── 下方：动态结果区 ── */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <ResultsPanel />
      </div>

    </div>
  )
}

function WelcomeChart() {
  return (
    <div
      className="flex flex-col items-center justify-center h-full gap-4"
      style={{ opacity: 0.6 }}
    >
      <div
        className="text-4xl"
        style={{ filter: 'drop-shadow(0 0 16px rgba(34,211,238,0.3))' }}
      >
        📈
      </div>
      <div className="text-center space-y-1">
        <p className="text-sm font-medium" style={{ color: 'rgb(140,160,200)', fontFamily: 'var(--font-bricolage)' }}>
          K 线图将在此显示
        </p>
        <p className="text-xs" style={{ color: 'rgb(72,90,130)' }}>
          向 AI 询问任意股票或 ETF 代码，图表自动加载
        </p>
      </div>
    </div>
  )
}
