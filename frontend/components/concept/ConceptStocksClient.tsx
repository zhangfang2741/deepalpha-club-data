'use client'

import { useConceptStocks } from '@/hooks/use-concept'
import { StockTable } from './StockTable'
import { WeightChart } from '@/components/charts/WeightChart'
import useSWR from 'swr'
import { getConceptEtfs } from '@/lib/api'
import type { ConceptEtf } from '@/lib/types'

function StatCard({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div
      className="px-4 py-3 rounded-lg"
      style={{
        background: 'rgba(13,22,46,0.8)',
        border: `1px solid ${accent ? 'rgba(34,211,238,0.2)' : 'rgba(99,130,190,0.12)'}`,
      }}
    >
      <p className="text-[10px] uppercase tracking-widest mb-1" style={{ color: 'rgb(72,90,130)' }}>
        {label}
      </p>
      <p
        className="text-xl font-semibold tabular-nums"
        style={{
          fontFamily: 'var(--font-bricolage)',
          color: accent ? 'rgb(34,211,238)' : 'rgb(225,235,255)',
        }}
      >
        {value}
      </p>
    </div>
  )
}

function EtfSection({ conceptName }: { conceptName: string }) {
  const { data: etfs } = useSWR<ConceptEtf[]>(
    `concept-etfs-${conceptName}`,
    () => getConceptEtfs(conceptName),
    { revalidateOnFocus: false }
  )

  if (!etfs?.length) return null

  return (
    <section>
      <h3
        className="text-[10px] uppercase tracking-[0.15em] font-semibold mb-3"
        style={{ color: 'rgb(72,90,130)' }}
      >
        相关 ETF — {etfs.length} 只
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2.5">
        {etfs.map(etf => (
          <div
            key={etf.etf_symbol}
            className="flex flex-col gap-1 p-3 rounded-lg transition-all duration-200 group"
            style={{
              background: 'rgba(13,22,46,0.6)',
              border: '1px solid rgba(99,130,190,0.10)',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(34,211,238,0.2)'
              ;(e.currentTarget as HTMLDivElement).style.background = 'rgba(18,30,60,0.8)'
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(99,130,190,0.10)'
              ;(e.currentTarget as HTMLDivElement).style.background = 'rgba(13,22,46,0.6)'
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <span
                className="text-xs font-semibold shrink-0"
                style={{
                  fontFamily: 'var(--font-ibm-mono)',
                  color: 'rgb(34,211,238)',
                }}
              >
                {etf.etf_symbol}
              </span>
              {etf.aum_million && (
                <span
                  className="text-[9px] tabular-nums shrink-0"
                  style={{ color: 'rgb(72,90,130)', fontFamily: 'var(--font-ibm-mono)' }}
                >
                  ${(etf.aum_million / 1000).toFixed(1)}B
                </span>
              )}
            </div>
            <p
              className="text-xs font-medium leading-tight"
              style={{ color: 'rgb(180,195,225)' }}
            >
              {etf.etf_name_zh ?? etf.etf_name ?? etf.etf_symbol}
            </p>
            {etf.description_zh && (
              <p
                className="text-[10px] leading-snug"
                style={{ color: 'rgb(100,120,160)' }}
              >
                {etf.description_zh}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

function LoadingSkeleton() {
  return (
    <div className="p-6 space-y-6 animate-in">
      <div className="space-y-2">
        <div className="h-8 w-48 rounded-lg skeleton-shimmer" />
        <div className="h-4 w-64 rounded skeleton-shimmer" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[0,1,2].map(i => <div key={i} className="h-20 rounded-lg skeleton-shimmer" />)}
      </div>
      <div className="h-56 rounded-lg skeleton-shimmer" />
      <div className="h-64 rounded-lg skeleton-shimmer" />
    </div>
  )
}

export function ConceptStocksClient({ conceptName }: { conceptName: string }) {
  const { data: stocks, isLoading, error } = useConceptStocks(conceptName)

  if (isLoading) return <LoadingSkeleton />

  if (error) {
    return (
      <div className="flex h-60 items-center justify-center">
        <div
          className="text-sm px-4 py-3 rounded-lg"
          style={{
            color: 'rgb(251,113,133)',
            background: 'rgba(251,113,133,0.08)',
            border: '1px solid rgba(251,113,133,0.2)',
          }}
        >
          加载失败：{(error as Error).message}
        </div>
      </div>
    )
  }

  if (!stocks?.length) {
    return (
      <div className="flex h-60 items-center justify-center">
        <p className="text-sm" style={{ color: 'rgb(72,90,130)' }}>暂无数据</p>
      </div>
    )
  }

  const maxWeight = Math.max(...stocks.map(s => s.total_weight))
  const avgCoverage = (stocks.reduce((a, b) => a + b.etf_count, 0) / stocks.length).toFixed(1)

  return (
    <div className="p-6 space-y-8 animate-in">

      {/* ── 页头 ── */}
      <div className="space-y-1">
        <h1
          className="text-2xl font-bold tracking-tight"
          style={{ fontFamily: 'var(--font-bricolage)', color: 'rgb(225,235,255)' }}
        >
          {conceptName}
        </h1>
        <p className="text-xs" style={{ color: 'rgb(72,90,130)' }}>
          最后更新 {stocks[0]?.date}
        </p>
      </div>

      {/* ── 统计卡片 ── */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="成分股" value={stocks.length} accent />
        <StatCard label="平均 ETF 覆盖" value={avgCoverage} />
        <StatCard label="最高权重" value={`${maxWeight.toFixed(1)}%`} />
      </div>

      {/* ── ETF 列表 ── */}
      <EtfSection conceptName={conceptName} />

      {/* ── 权重图表 ── */}
      <section>
        <h3
          className="text-[10px] uppercase tracking-[0.15em] font-semibold mb-3"
          style={{ color: 'rgb(72,90,130)' }}
        >
          前 15 大成分股权重
        </h3>
        <div
          className="rounded-lg p-4"
          style={{
            background: 'rgba(13,22,46,0.6)',
            border: '1px solid rgba(99,130,190,0.10)',
          }}
        >
          <WeightChart stocks={stocks} />
        </div>
      </section>

      {/* ── 成分股明细 ── */}
      <section>
        <h3
          className="text-[10px] uppercase tracking-[0.15em] font-semibold mb-3"
          style={{ color: 'rgb(72,90,130)' }}
        >
          全部成分股
        </h3>
        <StockTable stocks={stocks} />
      </section>

    </div>
  )
}
