'use client'

import { useMemo, useState, useRef, useCallback } from 'react'
import type { OHLCVBar } from '@/lib/types'

interface TooltipData {
  bar: OHLCVBar
  x: number
  y: number
}

const PAD = { top: 16, right: 56, bottom: 36, left: 8 }
const VOL_HEIGHT_RATIO = 0.18

function niceRange(min: number, max: number, ticks = 6) {
  const range = max - min
  const step = Math.pow(10, Math.floor(Math.log10(range / ticks)))
  const niceStep = [1, 2, 2.5, 5, 10].map(f => f * step).find(s => range / s <= ticks) ?? step
  const niceMin = Math.floor(min / niceStep) * niceStep
  const niceMax = Math.ceil(max / niceStep) * niceStep
  const levels: number[] = []
  for (let v = niceMin; v <= niceMax + niceStep * 0.001; v += niceStep) levels.push(+v.toFixed(4))
  return { min: niceMin, max: niceMax, levels }
}

export function CandlestickChart({
  bars,
  symbol,
}: {
  bars: OHLCVBar[]
  symbol: string
}) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [tooltip, setTooltip] = useState<TooltipData | null>(null)
  const [dims, setDims] = useState({ w: 800, h: 400 })

  const resizeObserver = useCallback((node: SVGSVGElement | null) => {
    if (!node) return
    const ro = new ResizeObserver(([entry]) => {
      setDims({ w: entry.contentRect.width, h: entry.contentRect.height })
    })
    ro.observe(node)
  }, [])

  const { w, h } = dims
  const chartH = h - PAD.top - PAD.bottom
  const priceH = chartH * (1 - VOL_HEIGHT_RATIO)
  const volH = chartH * VOL_HEIGHT_RATIO
  const chartW = w - PAD.left - PAD.right

  const prices = useMemo(() => bars.flatMap(b => [b.h, b.l]), [bars])
  const priceMin = Math.min(...prices)
  const priceMax = Math.max(...prices)
  const { min: yMin, max: yMax, levels } = useMemo(
    () => niceRange(priceMin, priceMax), [priceMin, priceMax]
  )

  const maxVol = useMemo(() => Math.max(...bars.map(b => b.v)), [bars])

  const n = bars.length
  const candleW = Math.max(1.5, Math.min(16, chartW / n * 0.7))
  const spacing = chartW / n

  const toY = (price: number) =>
    PAD.top + priceH * (1 - (price - yMin) / (yMax - yMin))

  const toVolY = (vol: number) =>
    PAD.top + priceH + volH * (1 - vol / maxVol) + 4

  // ── MA5 / MA20 ────────────────────────────────────────────
  const ma = (period: number) =>
    bars.map((_, i) => {
      if (i < period - 1) return null
      const avg = bars.slice(i - period + 1, i + 1).reduce((s, b) => s + b.c, 0) / period
      return avg
    })
  const ma5 = ma(5)
  const ma20 = ma(20)

  const maPath = (values: (number | null)[]) => {
    const pts = values
      .map((v, i) => v == null ? null : `${PAD.left + (i + 0.5) * spacing},${toY(v)}`)
      .filter((p): p is string => p !== null)
    if (!pts.length) return ''
    return pts.reduce((acc, pt, i) => acc + (i === 0 ? `M${pt}` : `L${pt}`), '')
  }

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return
    const rect = svgRef.current.getBoundingClientRect()
    const mx = e.clientX - rect.left - PAD.left
    const idx = Math.round(mx / spacing - 0.5)
    if (idx >= 0 && idx < bars.length) {
      setTooltip({ bar: bars[idx], x: e.clientX - rect.left, y: e.clientY - rect.top })
    }
  }, [bars, spacing])

  if (!bars.length) return null

  return (
    <div className="relative w-full h-full select-none">
      <svg
        ref={node => { (svgRef as React.MutableRefObject<SVGSVGElement | null>).current = node; resizeObserver(node) }}
        className="w-full h-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setTooltip(null)}
      >
        {/* ── 网格线 ── */}
        {levels.map(level => (
          <g key={level}>
            <line
              x1={PAD.left} x2={w - PAD.right}
              y1={toY(level)} y2={toY(level)}
              stroke="rgba(0,0,0,0.06)" strokeWidth={1}
            />
            <text
              x={w - PAD.right + 6}
              y={toY(level)}
              dy="0.35em"
              fontSize={9}
              fill="rgb(150,160,180)"
              fontFamily="var(--font-ibm-mono)"
            >
              {level >= 1000 ? level.toLocaleString() : level.toFixed(level < 1 ? 4 : 2)}
            </text>
          </g>
        ))}

        {/* ── 当前价水平线 ── */}
        {(() => {
          const last = bars[bars.length - 1]
          const y = toY(last.c)
          const isUp = last.c >= last.o
          return (
            <>
              <line
                x1={PAD.left} x2={w - PAD.right}
                y1={y} y2={y}
                stroke={isUp ? 'rgba(0,200,130,0.3)' : 'rgba(255,90,100,0.3)'}
                strokeWidth={1}
                strokeDasharray="3 3"
              />
              <text
                x={w - PAD.right + 6} y={y} dy="0.35em"
                fontSize={9}
                fill={isUp ? 'rgb(0,200,130)' : 'rgb(255,90,100)'}
                fontFamily="var(--font-ibm-mono)"
                fontWeight={600}
              >
                {last.c.toFixed(last.c < 1 ? 4 : 2)}
              </text>
            </>
          )
        })()}

        {/* ── MA 线 ── */}
        <path d={maPath(ma5)} fill="none" stroke="rgba(255,185,0,0.7)" strokeWidth={1.2} />
        <path d={maPath(ma20)} fill="none" stroke="rgba(22,119,255,0.6)" strokeWidth={1.2} />

        {/* ── 蜡烛 ── */}
        {bars.map((b, i) => {
          const x = PAD.left + (i + 0.5) * spacing
          const isUp = b.c >= b.o
          const color = isUp ? '#00C882' : '#FF5A64'
          const bodyTop = toY(Math.max(b.o, b.c))
          const bodyBot = toY(Math.min(b.o, b.c))
          const bodyH = Math.max(1, bodyBot - bodyTop)

          return (
            <g key={b.t}>
              {/* 影线 */}
              <line
                x1={x} x2={x}
                y1={toY(b.h)} y2={toY(b.l)}
                stroke={color}
                strokeWidth={1}
                opacity={0.7}
              />
              {/* 实体 */}
              <rect
                x={x - candleW / 2}
                y={bodyTop}
                width={candleW}
                height={bodyH}
                fill={isUp ? color : 'none'}
                stroke={color}
                strokeWidth={isUp ? 0 : 1}
                opacity={0.85}
              />
            </g>
          )
        })}

        {/* ── 成交量柱 ── */}
        {bars.map((b, i) => {
          const x = PAD.left + (i + 0.5) * spacing
          const isUp = b.c >= b.o
          const volY = toVolY(b.v)
          const volBase = PAD.top + priceH + volH + 4
          return (
            <rect
              key={`v${b.t}`}
              x={x - candleW / 2}
              y={volY}
              width={candleW}
              height={Math.max(1, volBase - volY)}
              fill={isUp ? 'rgba(0,200,130,0.35)' : 'rgba(255,90,100,0.25)'}
            />
          )
        })}

        {/* ── X 轴日期标签 ── */}
        {(() => {
          const step = Math.max(1, Math.floor(n / 8))
          return bars.filter((_, i) => i % step === 0).map((b, _, arr) => {
            const i = bars.indexOf(b)
            const x = PAD.left + (i + 0.5) * spacing
            return (
              <text
                key={b.t}
                x={x} y={h - 8}
                textAnchor="middle"
                fontSize={9}
                fill="rgb(150,160,180)"
                fontFamily="var(--font-ibm-mono)"
              >
                {b.t.slice(5)}
              </text>
            )
          })
        })()}

        {/* ── 悬浮十字线 ── */}
        {tooltip && (
          <>
            <line
              x1={tooltip.x} x2={tooltip.x}
              y1={PAD.top} y2={PAD.top + priceH}
              stroke="rgba(22,119,255,0.4)" strokeWidth={1} strokeDasharray="3 3"
            />
            <line
              x1={PAD.left} x2={w - PAD.right}
              y1={toY(tooltip.bar.c)} y2={toY(tooltip.bar.c)}
              stroke="rgba(22,119,255,0.25)" strokeWidth={1} strokeDasharray="3 3"
            />
          </>
        )}

        {/* ── 图例 ── */}
        <g transform={`translate(${PAD.left + 8}, ${PAD.top + 6})`}>
          <rect x={0} y={0} width={4} height={4} fill="rgba(255,185,0,0.8)" />
          <text x={8} y={4} fontSize={8} fill="rgba(255,185,0,0.8)" fontFamily="var(--font-ibm-mono)">MA5</text>
          <rect x={36} y={0} width={4} height={4} fill="rgba(22,119,255,0.7)" />
          <text x={44} y={4} fontSize={8} fill="rgba(22,119,255,0.7)" fontFamily="var(--font-ibm-mono)">MA20</text>
        </g>
      </svg>

      {/* ── Tooltip ── */}
      {tooltip && (
        <div
          className="absolute pointer-events-none px-3 py-2 rounded-lg text-[10px] z-20"
          style={{
            left: tooltip.x + 12,
            top: tooltip.y - 10,
            transform: tooltip.x > w * 0.65 ? 'translateX(-100%)' : undefined,
            background: 'rgb(255,255,255)',
            border: '1px solid rgba(22,119,255,0.20)',
            fontFamily: 'var(--font-ibm-mono)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          }}
        >
          <p className="mb-1" style={{ color: 'rgb(100,115,140)' }}>{tooltip.bar.t}</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
            {[
              ['开', tooltip.bar.o],
              ['高', tooltip.bar.h],
              ['低', tooltip.bar.l],
              ['收', tooltip.bar.c],
            ].map(([label, val]) => (
              <div key={label as string} className="flex justify-between gap-2">
                <span style={{ color: 'rgb(150,160,180)' }}>{label}</span>
                <span style={{ color: (val as number) >= tooltip.bar.o ? 'rgb(0,180,100)' : 'rgb(255,80,90)' }}>
                  {(val as number).toFixed((val as number) < 1 ? 4 : 2)}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-1" style={{ color: 'rgb(150,160,180)' }}>
            量 {(tooltip.bar.v / 1e6).toFixed(1)}M
          </p>
        </div>
      )}
    </div>
  )
}
