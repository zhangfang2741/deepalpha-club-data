import type { ConceptSummary } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function ConceptCard({ summary }: { summary: ConceptSummary }) {
  return (
    <Card className="hover:border-accent transition-colors">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium truncate">
          {summary.concept_name_zh ?? summary.concept}
        </CardTitle>
        {summary.concept_name_zh && (
          <p className="text-xs text-muted-foreground truncate">{summary.concept}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex gap-3 text-xs text-muted-foreground">
          <span>{summary.etf_count} 只 ETF</span>
          <span>·</span>
          <span>{summary.stock_count} 只成分股</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {summary.top_symbols.slice(0, 5).map(sym => (
            <Badge key={sym} variant="outline" className="text-xs font-mono px-1.5">
              {sym}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
