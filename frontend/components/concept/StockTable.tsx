import type { ConceptStock } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell,
  TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

export function StockTable({ stocks }: { stocks: ConceptStock[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-24">代码</TableHead>
          <TableHead>公司</TableHead>
          <TableHead className="text-right w-20">ETF覆盖</TableHead>
          <TableHead className="text-right w-24">合计权重</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {stocks.map(s => (
          <TableRow key={s.symbol}>
            <TableCell className="font-mono font-semibold text-emerald-400">
              {s.symbol}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm truncate max-w-[200px]">
              {s.name ?? '—'}
            </TableCell>
            <TableCell className="text-right">
              <Badge variant="secondary" className="tabular-nums">{s.etf_count}</Badge>
            </TableCell>
            <TableCell className="text-right font-mono text-amber-400">
              {s.total_weight.toFixed(1)}%
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
