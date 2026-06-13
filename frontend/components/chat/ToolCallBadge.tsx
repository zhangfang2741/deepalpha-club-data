interface ToolCallBadgeProps {
  toolName: string
  state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | 'approval-requested' | 'approval-responded' | 'output-denied'
}

const LABELS: Record<string, string> = {
  search_concept: '查询概念股池',
  get_quote:      '获取实时报价',
  get_financials: '获取财务数据',
  list_concepts:  '列举概念分类',
}

export function ToolCallBadge({ toolName, state }: ToolCallBadgeProps) {
  const label = LABELS[toolName] ?? toolName
  const done  = state === 'output-available'
  const error = state === 'output-error'
  const busy  = !done && !error

  return (
    <div
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium"
      style={{
        background: done
          ? 'rgba(0,200,130,0.08)'
          : error
            ? 'rgba(255,90,100,0.08)'
            : 'rgba(22,119,255,0.08)',
        border: `1px solid ${
          done
            ? 'rgba(0,200,130,0.2)'
            : error
              ? 'rgba(255,90,100,0.2)'
              : 'rgba(22,119,255,0.2)'
        }`,
        color: done
          ? 'rgb(0,200,130)'
          : error
            ? 'rgb(255,90,100)'
            : 'rgb(22,119,255)',
        fontFamily: 'var(--font-figtree)',
      }}
    >
      {busy && (
        <span
          className="h-1.5 w-1.5 rounded-full shrink-0"
          style={{
            background: 'rgb(22,119,255)',
            animation: 'pulse-dot 1s ease-in-out infinite',
          }}
        />
      )}
      {done && <span className="text-[9px]">✦</span>}
      {error && <span className="text-[9px]">✗</span>}
      <span>{label}</span>
    </div>
  )
}
