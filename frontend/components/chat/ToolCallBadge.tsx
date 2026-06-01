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
          ? 'rgba(52,211,153,0.08)'
          : error
            ? 'rgba(251,113,133,0.08)'
            : 'rgba(251,191,36,0.08)',
        border: `1px solid ${
          done
            ? 'rgba(52,211,153,0.2)'
            : error
              ? 'rgba(251,113,133,0.2)'
              : 'rgba(251,191,36,0.2)'
        }`,
        color: done
          ? 'rgb(52,211,153)'
          : error
            ? 'rgb(251,113,133)'
            : 'rgb(251,191,36)',
        fontFamily: 'var(--font-figtree)',
        animation: busy ? undefined : undefined,
      }}
    >
      {busy && (
        <span
          className="h-1.5 w-1.5 rounded-full shrink-0"
          style={{
            background: 'rgb(251,191,36)',
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
