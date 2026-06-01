import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ToolCallBadgeProps {
  toolName: string
  state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | 'approval-requested' | 'approval-responded' | 'output-denied'
}

const LABELS: Record<string, string> = {
  search_concept: '查询概念股池',
  get_quote:      '获取实时报价',
  list_concepts:  '列举概念分类',
}

export function ToolCallBadge({ toolName, state }: ToolCallBadgeProps) {
  const label = LABELS[toolName] ?? toolName
  const done = state === 'output-available'
  const error = state === 'output-error'

  return (
    <Badge
      variant="outline"
      className={cn(
        'text-xs font-normal py-0.5',
        done
          ? 'border-emerald-800 text-emerald-400'
          : error
            ? 'border-red-800 text-red-400'
            : 'border-amber-800 text-amber-400 animate-pulse'
      )}
    >
      {done ? '✓ ' : error ? '✗ ' : '⏳ '}{label}
    </Badge>
  )
}
