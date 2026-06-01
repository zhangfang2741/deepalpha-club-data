'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import type { ConceptStock } from '@/lib/types'

export function WeightChart({ stocks, limit = 15 }: { stocks: ConceptStock[]; limit?: number }) {
  const data = stocks
    .slice(0, limit)
    .map(s => ({ symbol: s.symbol, weight: +s.total_weight.toFixed(1) }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
        <XAxis
          type="number"
          tick={{ fontSize: 11, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="symbol"
          width={56}
          tick={{ fontSize: 11, fill: '#6ee7b7', fontFamily: 'monospace' }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          formatter={(v: unknown) => [`${v}%`, '合计权重']}
          contentStyle={{
            fontSize: 12,
            background: 'hsl(222 47% 7%)',
            border: '1px solid hsl(217 33% 14%)',
            borderRadius: 6,
          }}
          cursor={{ fill: 'hsl(217 33% 12%)' }}
        />
        <Bar dataKey="weight" radius={[0, 3, 3, 0]} maxBarSize={16}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 0 ? '#f59e0b' : '#34d399'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
