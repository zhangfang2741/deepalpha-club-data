'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useConceptList } from '@/hooks/use-concept'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function ConceptSidebar() {
  const pathname = usePathname()
  const { data: concepts, isLoading } = useConceptList()

  return (
    <nav className="p-2 space-y-0.5">
      <p className="px-2 py-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
        概念分类
      </p>

      {isLoading &&
        Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-full rounded-md mb-1" />
        ))}

      {concepts?.map(c => {
        const href = `/concept/${encodeURIComponent(c.concept)}`
        const active = pathname === href
        return (
          <Link
            key={c.concept}
            href={href}
            className={cn(
              'flex items-center justify-between px-2 py-1.5 rounded-md text-sm transition-colors',
              'hover:bg-accent hover:text-accent-foreground',
              active
                ? 'bg-accent text-accent-foreground font-medium'
                : 'text-muted-foreground'
            )}
          >
            <span className="truncate max-w-[130px]">{c.concept}</span>
            <span className="text-[10px] text-muted-foreground tabular-nums ml-1 shrink-0">
              {c.stock_count}
            </span>
          </Link>
        )
      })}
    </nav>
  )
}
