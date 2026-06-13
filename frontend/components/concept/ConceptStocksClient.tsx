'use client'

import { useConceptStocks } from '@/hooks/use-concept'
import { StockTable } from './StockTable'
import { WeightChart } from '@/components/charts/WeightChart'
import useSWR from 'swr'
import { getConceptEtfs, getConceptAnalysis } from '@/lib/api'
import type { ConceptEtf } from '@/lib/types'
import type { ConceptAnalysis } from '@/lib/api'
import { useState } from 'react'

function StatCard({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div
      className="px-4 py-3 rounded-lg"
      style={{
        background: 'rgba(11,20,42,0.8)',
        border: `1px solid ${accent ? 'rgba(22,119,255,0.25)' : 'rgba(0,0,0,0.08)'}`,
      }}
    >
      <p className="text-[10px] uppercase tracking-widest mb-1" style={{ color: 'rgb(100,116,139)' }}>
        {label}
      </p>
      <p
        className="text-xl font-semibold tabular-nums"
        style={{
          fontFamily: 'var(--font-bricolage)',
          color: accent ? 'rgb(22,119,255)' : 'rgb(15,23,42)',
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
        style={{ color: 'rgb(100,116,139)' }}
      >
        相关 ETF — {etfs.length} 只
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2.5">
        {etfs.map(etf => (
          <div
            key={etf.etf_symbol}
            className="flex flex-col gap-1 p-3 rounded-lg transition-all duration-200 group"
            style={{
              background: 'rgba(11,20,42,0.6)',
              border: '1px solid rgba(0,0,0,0.06)',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(22,119,255,0.25)'
              ;(e.currentTarget as HTMLDivElement).style.background = 'rgba(15,28,55,0.8)'
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(0,0,0,0.06)'
              ;(e.currentTarget as HTMLDivElement).style.background = 'rgba(11,20,42,0.6)'
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <span
                className="text-xs font-semibold shrink-0"
                style={{
                  fontFamily: 'var(--font-ibm-mono)',
                  color: 'rgb(22,119,255)',
                }}
              >
                {etf.etf_symbol}
              </span>
              {etf.aum_million && (
                <span
                  className="text-[9px] tabular-nums shrink-0"
                  style={{ color: 'rgb(100,116,139)', fontFamily: 'var(--font-ibm-mono)' }}
                >
                  ${(etf.aum_million / 1000).toFixed(1)}B
                </span>
              )}
            </div>
            <p
              className="text-xs font-medium leading-tight"
              style={{ color: 'rgb(30,41,59)' }}
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

function MarkdownTable({ content, title }: { content: string; title: string }) {
  if (!content.trim()) return null
  const lines = content.trim().split('\n')
  const tableLines = lines.filter(l => l.trim().startsWith('|'))
  if (tableLines.length < 2) {
    return (
      <div className="rounded-lg p-3 text-xs" style={{ background: 'rgba(11,20,42,0.6)', border: '1px solid rgba(0,0,0,0.06)', color: 'rgb(51,65,85)' }}>
        <pre className="whitespace-pre-wrap break-words font-mono text-[11px]">{content}</pre>
      </div>
    )
  }
  const headers = tableLines[0].split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(h => h.trim())
  const rows = tableLines.slice(2).map(row => row.split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(c => c.trim()))
  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid rgba(0,0,0,0.06)' }}>
      <table className="w-full text-xs">
        <thead>
          <tr style={{ background: 'rgba(0,0,0,0.06)' }}>
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2 text-left font-medium" style={{ color: 'rgb(22,119,255)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-t" style={{ borderColor: 'rgba(0,0,0,0.04)' }}>
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2" style={{ color: 'rgb(30,41,59)' }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const ANALYSIS_SECTIONS = [
  { key: 'products', label: '维度一：核心产品', desc: '每家公司的主力产品/服务' },
  { key: 'position', label: '维度二：企业定位', desc: '市场规模、定位、核心优势' },
  { key: 'competition', label: '维度三：竞争格局', desc: '概念内公司之间的竞争关系' },
  { key: 'supply_chain', label: '维度四：供应链关系', desc: '上下游供应商/客户关系' },
  { key: 'ecosystem', label: '维度五：生态位', desc: '平台层/基础设施层/应用层' },
] as const

function AiAnalysisSection({ conceptName }: { conceptName: string }) {
  const [analysis, setAnalysis] = useState<ConceptAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [started, setStarted] = useState(false)

  async function runAnalysis() {
    setLoading(true)
    setError(null)
    try {
      const data = await getConceptAnalysis(conceptName)
      setAnalysis(data)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-[10px] uppercase tracking-[0.15em] font-semibold" style={{ color: 'rgb(100,116,139)' }}>
            AI 深度分析
          </h3>
          <p className="text-[10px] mt-0.5" style={{ color: 'rgb(100,116,139)' }}>
            基于 LLM 世界知识自动生成 · 核心产品 / 企业定位 / 竞争格局 / 供应链 / 生态位
          </p>
        </div>
        {!analysis && !loading && (
          <button
            onClick={() => { setStarted(true); runAnalysis() }}
            className="px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200"
            style={{
              background: 'rgba(22,119,255,0.15)',
              border: '1px solid rgba(22,119,255,0.30)',
              color: 'rgb(22,119,255)',
            }}
          >
            开始分析 →
          </button>
        )}
        {loading && (
          <span className="text-xs animate-pulse" style={{ color: 'rgb(22,119,255)' }}>
            分析中，请稍候...
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-lg p-3 text-xs" style={{ color: 'rgb(255,90,100)', background: 'rgba(255,90,100,0.08)', border: '1px solid rgba(255,90,100,0.2)' }}>
          分析失败：{error}
        </div>
      )}

      {analysis && (
        <div className="flex flex-col gap-4">
          {ANALYSIS_SECTIONS.map(({ key, label, desc }) => (
            <div key={key}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-[10px] font-semibold" style={{ color: 'rgb(22,119,255)' }}>{label}</span>
                <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>{desc}</span>
              </div>
              <MarkdownTable content={analysis[key]} title={label} />
            </div>
          ))}
        </div>
      )}
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
            color: 'rgb(255,90,100)',
            background: 'rgba(255,90,100,0.08)',
            border: '1px solid rgba(255,90,100,0.2)',
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
        <p className="text-sm" style={{ color: 'rgb(100,116,139)' }}>暂无数据</p>
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
          style={{ fontFamily: 'var(--font-bricolage)', color: 'rgb(15,23,42)' }}
        >
          {conceptName}
        </h1>
        <p className="text-xs" style={{ color: 'rgb(100,116,139)' }}>
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

      {/* ── AI 深度分析 ── */}
      <AiAnalysisSection conceptName={conceptName} />

      {/* ── 权重图表 ── */}
      <section>
        <h3
          className="text-[10px] uppercase tracking-[0.15em] font-semibold mb-3"
          style={{ color: 'rgb(100,116,139)' }}
        >
          前 15 大成分股权重
        </h3>
        <div
          className="rounded-lg p-4"
          style={{
            background: 'rgba(11,20,42,0.6)',
            border: '1px solid rgba(0,0,0,0.06)',
          }}
        >
          <WeightChart stocks={stocks} />
        </div>
      </section>

      {/* ── 成分股明细 ── */}
      <section>
        <h3
          className="text-[10px] uppercase tracking-[0.15em] font-semibold mb-3"
          style={{ color: 'rgb(100,116,139)' }}
        >
          全部成分股
        </h3>
        <StockTable stocks={stocks} />
      </section>

    </div>
  )
}
