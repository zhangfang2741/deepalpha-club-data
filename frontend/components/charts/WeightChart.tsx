'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import type { ConceptStock } from '@/lib/types'

const COLORS = [
  '#1677FF', '#00D2FF', '#00C882', '#FFB900',
  '#409CFF', '#FF5A64', '#60a5fa',
  '#f97316', '#4ade80', '#e879f9',
  '#94a3b8', '#818cf8', '#2dd4bf',
  '#facc15', '#38bdf8', '#86efac',
]

export function WeightChart({ stocks, limit = 15 }: { stocks: ConceptStock[]; limit?: number }) {
  const data = stocks
    .slice(0, limit)
    .map(s => ({ symbol: s.symbol, weight: +s.total_weight.toFixed(1) }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 4 }}>
        <XAxis
          type="number"
          tick={{ fontSize: 10, fill: 'rgb(100,116,139)', fontFamily: 'var(--font-ibm-mono)' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="symbol"
          width={52}
          tick={{ fontSize: 10, fill: 'rgb(22,119,255)', fontFamily: 'var(--font-ibm-mono)' }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          formatter={(v: unknown) => [`${v}%`, '合计权重']}
          contentStyle={{
            fontSize: 11,
            background: 'rgb(246,248,252)',
            border: '1px solid rgba(22,119,255,0.2)',
            borderRadius: 6,
            color: 'rgb(15,23,42)',
            fontFamily: 'var(--font-ibm-mono)',
          }}
          cursor={{ fill: 'rgba(0,0,0,0.04)' }}
        />
        <Bar dataKey="weight" radius={[0, 3, 3, 0]} maxBarSize={14}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} opacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
