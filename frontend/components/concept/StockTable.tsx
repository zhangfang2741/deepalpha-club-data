import type { ConceptStock } from '@/lib/types'

export function StockTable({ stocks }: { stocks: ConceptStock[] }) {
  const maxWeight = Math.max(...stocks.map(s => s.total_weight))

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{
        background: 'rgba(13,22,46,0.6)',
        border: '1px solid rgba(99,130,190,0.10)',
      }}
    >
      {/* 表头 */}
      <div
        className="grid text-[10px] font-semibold uppercase tracking-[0.12em] px-4 py-2.5"
        style={{
          gridTemplateColumns: '2rem 6rem 1fr 4rem 7rem',
          color: 'rgb(72,90,130)',
          borderBottom: '1px solid rgba(99,130,190,0.10)',
          background: 'rgba(8,14,30,0.4)',
        }}
      >
        <span>#</span>
        <span>代码</span>
        <span>公司</span>
        <span className="text-right">ETF覆盖</span>
        <span className="text-right">权重</span>
      </div>

      {/* 数据行 */}
      <div>
        {stocks.map((s, i) => {
          const weightPct = (s.total_weight / maxWeight) * 100
          return (
            <div
              key={s.symbol}
              className="grid items-center px-4 py-2.5 stock-row transition-colors duration-100"
              style={{
                gridTemplateColumns: '2rem 6rem 1fr 4rem 7rem',
                borderBottom: i < stocks.length - 1 ? '1px solid rgba(99,130,190,0.06)' : undefined,
              }}
            >
              {/* 排名 */}
              <span
                className="text-[10px] tabular-nums"
                style={{
                  fontFamily: 'var(--font-ibm-mono)',
                  color: i < 3 ? 'rgb(251,191,36)' : 'rgb(42,55,80)',
                }}
              >
                {i + 1}
              </span>

              {/* 代码 */}
              <span
                className="text-sm font-semibold"
                style={{
                  fontFamily: 'var(--font-ibm-mono)',
                  color: 'rgb(34,211,238)',
                }}
              >
                {s.symbol}
              </span>

              {/* 公司名 */}
              <span
                className="text-xs truncate pr-4"
                style={{ color: 'rgb(120,140,180)' }}
              >
                {s.name ?? '—'}
              </span>

              {/* ETF 覆盖数 */}
              <div className="flex justify-end">
                <span
                  className="text-xs tabular-nums px-1.5 py-0.5 rounded"
                  style={{
                    fontFamily: 'var(--font-ibm-mono)',
                    background: 'rgba(34,211,238,0.08)',
                    color: 'rgb(34,211,238)',
                    border: '1px solid rgba(34,211,238,0.15)',
                  }}
                >
                  {s.etf_count}
                </span>
              </div>

              {/* 权重 + 进度条 */}
              <div className="flex flex-col items-end gap-1">
                <span
                  className="text-xs tabular-nums font-medium"
                  style={{
                    fontFamily: 'var(--font-ibm-mono)',
                    color: 'rgb(251,191,36)',
                  }}
                >
                  {s.total_weight.toFixed(1)}%
                </span>
                <div
                  className="h-0.5 rounded-full"
                  style={{ width: '3.5rem', background: 'rgba(99,130,190,0.15)' }}
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${weightPct}%`,
                      background: weightPct > 70
                        ? 'rgb(251,191,36)'
                        : 'rgba(251,191,36,0.5)',
                    }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
