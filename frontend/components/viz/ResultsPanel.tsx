'use client'

import { useViz } from '@/lib/viz-context'
import {
  ScatterChart, Scatter, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'
import type { ConceptStock } from '@/lib/types'

// ── 泡泡散点图：ETF覆盖 vs 权重 ─────────────────────────────────────────
function BubbleChart({ stocks }: { stocks: ConceptStock[] }) {
  const top = stocks.slice(0, 40)
  const data = top.map(s => ({
    x: s.etf_count,
    y: +s.total_weight.toFixed(2),
    name: s.symbol,
    z: Math.sqrt(s.total_weight) * 8,
  }))

  const COLORS = ['#1677FF', '#00D2FF', '#00C882', '#FFB900', '#409CFF', '#FF5A64', '#60a5fa', '#f97316']

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: 'rgb(100,115,140)' }}>
          成分股分布图
        </p>
        <p className="text-[9px]" style={{ color: 'rgb(150,160,180)' }}>
          X = ETF覆盖数 · Y = 合计权重% · 圆大=权重高
        </p>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <ScatterChart margin={{ top: 8, right: 20, bottom: 20, left: 0 }}>
          <XAxis
            type="number"
            dataKey="x"
            name="ETF覆盖"
            tick={{ fontSize: 9, fill: 'rgb(150,160,180)', fontFamily: 'var(--font-ibm-mono)' }}
            tickLine={false}
            axisLine={false}
            label={{ value: 'ETF覆盖', position: 'insideBottom', offset: -8, fontSize: 9, fill: 'rgb(150,160,180)' }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="权重"
            tick={{ fontSize: 9, fill: 'rgb(150,160,180)', fontFamily: 'var(--font-ibm-mono)' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={v => `${v}%`}
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3', stroke: 'rgba(22,119,255,0.2)' }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div
                  className="px-3 py-2 rounded-lg text-[10px]"
                  style={{
                    background: 'rgb(255,255,255)',
                    border: '1px solid rgba(22,119,255,0.20)',
                    fontFamily: 'var(--font-ibm-mono)',
                    color: 'rgb(60,70,90)',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.10)',
                  }}
                >
                  <p style={{ color: 'rgb(22,119,255)' }} className="font-semibold">{d.name}</p>
                  <p>ETF覆盖: {d.x}</p>
                  <p>权重: {d.y}%</p>
                </div>
              )
            }}
          />
          <ReferenceLine y={0} stroke="rgba(0,0,0,0.06)" />
          <Scatter data={data} shape="circle">
            {data.map((d, i) => (
              <Cell key={d.name} fill={COLORS[i % COLORS.length]} fillOpacity={0.8} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* 前 10 标签 */}
      <div className="flex flex-wrap gap-1.5">
        {top.slice(0, 12).map((s, i) => (
          <div
            key={s.symbol}
            className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px]"
            style={{
              background: 'rgb(245,247,250)',
              border: '1px solid rgba(0,0,0,0.08)',
            }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full shrink-0"
              style={{ background: COLORS[i % COLORS.length] }}
            />
            <span style={{ fontFamily: 'var(--font-ibm-mono)', color: 'rgb(60,70,90)' }}>
              {s.symbol}
            </span>
            <span style={{ color: 'rgb(150,160,180)' }}>{s.total_weight.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── 财务横向柱状图 ────────────────────────────────────────────────────────
function FinancialBars({ output, symbol }: { output: string; symbol: string }) {
  // 从 AI 输出字符串解析财务数字
  const parse = (key: string) => {
    const m = output.match(new RegExp(`${key}[：:][\\s]*\\$?([\\d.]+)B`))
    return m ? parseFloat(m[1]) : null
  }

  const items = [
    { key: '营业收入', label: 'Revenue',   color: '#1677FF' },
    { key: '毛利润',   label: 'Gross',     color: '#00D2FF' },
    { key: '营业利润', label: 'Operating', color: '#409CFF' },
    { key: '净利润',   label: 'Net',       color: '#FFB900' },
    { key: 'EBITDA',  label: 'EBITDA',    color: '#FF5A64' },
  ].map(i => ({ ...i, value: parse(i.key) })).filter(i => i.value !== null)

  if (!items.length) {
    return <p className="text-xs" style={{ color: 'rgb(100,115,140)' }}>{output}</p>
  }

  const max = Math.max(...items.map(i => i.value!))

  return (
    <div className="space-y-3">
      <p
        className="text-[10px] uppercase tracking-widest font-semibold"
        style={{ color: 'rgb(100,115,140)' }}
      >
        {symbol} 财务摘要（单位：B）
      </p>
      <div className="space-y-2.5">
        {items.map(item => (
          <div key={item.key} className="space-y-1">
            <div className="flex justify-between text-[10px]">
              <span style={{ color: 'rgb(100,115,140)', fontFamily: 'var(--font-figtree)' }}>
                {item.key}
              </span>
              <span style={{ color: item.color, fontFamily: 'var(--font-ibm-mono)' }}>
                ${item.value!.toFixed(2)}B
              </span>
            </div>
            <div
              className="h-1.5 rounded-full"
              style={{ background: 'rgb(240,244,248)', width: '100%' }}
            >
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${(item.value! / max * 100).toFixed(1)}%`,
                  background: `linear-gradient(90deg, ${item.color}, ${item.color}88)`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── 实时报价展示卡 ────────────────────────────────────────────────────────
function QuoteDisplay({ symbol, output }: { symbol: string; output: string }) {
  // 解析 AI 输出
  const price = output.match(/价格=([0-9.]+)/)?.[1]
  const pct = output.match(/涨跌幅=([+-]?[0-9.]+%)/)?.[1]
  const cap = output.match(/市值=([0-9.]+[BM])/)?.[1]
  const isUp = pct && !pct.startsWith('-')

  return (
    <div className="space-y-3">
      <p className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: 'rgb(100,115,140)' }}>
        实时报价
      </p>
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: '最新价', value: price ? `$${price}` : '—', color: 'rgb(30,38,55)', big: true },
          { label: '涨跌幅', value: pct ?? '—', color: isUp ? 'rgb(0,180,100)' : 'rgb(255,80,90)', big: true },
          { label: '市值',   value: cap ?? '—', color: 'rgb(255,185,0)', big: false },
        ].map(item => (
          <div
            key={item.label}
            className="px-3 py-2.5 rounded-lg"
            style={{
              background: 'rgb(255,255,255)',
              border: '1px solid rgba(0,0,0,0.08)',
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}
          >
            <p className="text-[9px] mb-1" style={{ color: 'rgb(150,160,180)' }}>{item.label}</p>
            <p
              className="font-semibold tabular-nums"
              style={{
                fontSize: item.big ? 16 : 13,
                fontFamily: 'var(--font-ibm-mono)',
                color: item.color,
              }}
            >
              {item.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── 空欢迎屏 ──────────────────────────────────────────────────────────────
function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 py-8">
      <div className="grid grid-cols-3 gap-2 opacity-40">
        {['📊', '📉', '💹', '📈', '🔍', '💡'].map((e, i) => (
          <div
            key={i}
            className="h-10 w-10 rounded-lg flex items-center justify-center text-xl"
            style={{ background: 'rgb(240,244,248)', border: '1px solid rgba(22,119,255,0.1)' }}
          >
            {e}
          </div>
        ))}
      </div>
      <div className="text-center space-y-1.5">
        <p className="text-sm font-semibold" style={{ color: 'rgb(100,115,140)', fontFamily: 'var(--font-bricolage)' }}>
          结果将在此可视化
        </p>
        <p className="text-xs max-w-[220px]" style={{ color: 'rgb(150,160,180)' }}>
          查询股票报价、概念成分股、财务数据时，
          结果将自动渲染为图表或表格
        </p>
      </div>
    </div>
  )
}

// ── 主面板 ────────────────────────────────────────────────────────────────
export function ResultsPanel() {
  const { result } = useViz()

  return (
    <div className="h-full px-4 py-4">
      {!result && <WelcomeScreen />}

      {result?.kind === 'quote' && (
        <QuoteDisplay symbol={result.symbol} output={result.output} />
      )}

      {result?.kind === 'concept_stocks' && result.stocks.length > 0 && (
        <BubbleChart stocks={result.stocks} />
      )}

      {result?.kind === 'financials' && (
        <FinancialBars symbol={result.symbol} output={result.output} />
      )}

      {result?.kind === 'concepts' && (
        <div className="text-xs" style={{ color: 'rgb(100,115,140)' }}>
          <p className="text-[10px] uppercase tracking-widest font-semibold mb-3" style={{ color: 'rgb(100,115,140)' }}>
            可用概念分类
          </p>
          <p className="whitespace-pre-wrap leading-relaxed" style={{ fontFamily: 'var(--font-figtree)' }}>
            {result.output}
          </p>
        </div>
      )}
    </div>
  )
}