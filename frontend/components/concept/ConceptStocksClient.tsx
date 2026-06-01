'use client'

import { useConceptStocks } from '@/hooks/use-concept'
import { StockTable } from './StockTable'
import { WeightChart } from '@/components/charts/WeightChart'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'

export function ConceptStocksClient({ conceptName }: { conceptName: string }) {
  const { data: stocks, isLoading, error } = useConceptStocks(conceptName)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-[220px] w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-40 items-center justify-center text-red-400 text-sm">
        加载失败：{(error as Error).message}
      </div>
    )
  }

  if (!stocks?.length) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground text-sm">
        暂无数据
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{conceptName}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          共 {stocks.length} 只成分股 · 最后更新 {stocks[0]?.date}
        </p>
      </div>
      <div className="rounded-lg border p-4">
        <p className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wide">
          ETF 权重分布（前15）
        </p>
        <WeightChart stocks={stocks} />
      </div>
      <Separator />
      <StockTable stocks={stocks} />
    </div>
  )
}
