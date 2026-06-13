import type { ConceptStock } from '@/lib/types'

export function StockTable({ stocks }: { stocks: ConceptStock[] }) {
  const maxWeight = Math.max(...stocks.map(s => s.total_weight))

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{
        background: 'rgb(255,255,255)',
        border: '1px solid rgba(22,119,255,0.10)',
        boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
      }}
    >
      {/* 表头 */}
      <div
        className="grid text-[10px] font-semibold uppercase tracking-[0.12em] px-4 py-2.5"
        style={{
          gridTemplateColumns: '2rem 6rem 1fr 4rem 7rem',
          color: 'rgb(100,115,140)',
          borderBottom: '1px solid rgba(22,119,255,0.08)',
          background: 'rgb(245,247,250)',
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
                borderBottom: i < stocks.length - 1 ? '1px solid rgba(22,119,255,0.04)' : undefined,
              }}
            >
              {/* 排名 */}
              <span
                className="text-[10px] tabular-nums"
                style={{
                  fontFamily: 'var(--font-ibm-mono)',
                  color: i < 3 ? 'rgb(255,185,0)' : 'rgb(150,160,180)',
                }}
              >
                {i + 1}
              </span>

              {/* 代码 */}
              <span
                className="text-sm font-semibold"
                style={{
                  fontFamily: 'var(--font-ibm-mono)',
                  color: 'rgb(22,119,255)',
                }}
              >
                {s.symbol}
              </span>

              {/* 公司名 */}
              <span
                className="text-xs truncate pr-4"
                style={{ color: 'rgb(100,115,140)' }}
              >
                {s.name ?? '—'}
              </span>

              {/* ETF 覆盖数 */}
              <div className="flex justify-end">
                <span
                  className="text-xs tabular-nums px-1.5 py-0.5 rounded"
                  style={{
                    fontFamily: 'var(--font-ibm-mono)',
                    background: 'rgba(22,119,255,0.08)',
                    color: 'rgb(22,119,255)',
                    border: '1px solid rgba(22,119,255,0.15)',
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
                    color: 'rgb(255,185,0)',
                  }}
                >
                  {s.total_weight.toFixed(1)}%
                </span>
                <div
                  className="h-0.5 rounded-full"
                  style={{ width: '3.5rem', background: 'rgb(240,244,248)' }}
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${weightPct}%`,
                      background: weightPct > 70
                        ? 'rgb(255,185,0)'
                        : 'rgba(255,185,0,0.5)',
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
