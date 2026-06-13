'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useConceptList } from '@/hooks/use-concept'

export function ConceptSidebar() {
  const pathname = usePathname()
  const { data: concepts, isLoading } = useConceptList()

  return (
    <nav className="flex flex-col h-full py-3">

      {/* 标题 */}
      <div className="px-4 pb-3">
        <p
          className="text-[10px] font-semibold tracking-[0.15em] uppercase"
          style={{ color: 'rgb(100,116,139)' }}
        >
          投资主题
        </p>
      </div>

      {/* 概念列表 */}
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">

        {isLoading && (
          Array.from({ length: 10 }).map((_, i) => (
            <div
              key={i}
              className="h-8 rounded skeleton-shimmer mb-1"
              style={{ opacity: 1 - i * 0.08 }}
            />
          ))
        )}

        {concepts?.map(c => {
          const href = `/concept/${encodeURIComponent(c.concept)}`
          const active = pathname === href
          const label = c.concept_name_zh ?? c.concept

          // 规模指示：stock_count 映射到圆点大小
          const dotSize = c.stock_count > 80 ? 6 : c.stock_count > 40 ? 5 : 4

          return (
            <Link
              key={c.concept}
              href={href}
              className="flex items-center justify-between px-3 py-2 rounded-md text-sm transition-all duration-150 group"
              style={{
                background: active ? 'rgba(0,0,0,0.06)' : 'transparent',
                borderLeft: active
                  ? '2px solid rgb(22,119,255)'
                  : '2px solid transparent',
                color: active
                  ? 'rgb(22,119,255)'
                  : 'rgb(51,65,85)',
              }}
            >
              <span
                className="truncate text-xs font-medium"
                style={{
                  fontFamily: 'var(--font-figtree)',
                  color: active ? 'rgb(22,119,255)' : undefined,
                }}
              >
                {label}
              </span>

              <div className="flex items-center gap-1.5 ml-2 shrink-0">
                <span
                  className="text-[9px] tabular-nums"
                  style={{
                    fontFamily: 'var(--font-ibm-mono)',
                    color: active ? 'rgba(22,119,255,0.7)' : 'rgb(100,116,139)',
                  }}
                >
                  {c.stock_count}
                </span>
                <span
                  className="rounded-full shrink-0"
                  style={{
                    width: dotSize,
                    height: dotSize,
                    background: active
                      ? 'rgb(22,119,255)'
                      : 'rgba(22,119,255,0.2)',
                    boxShadow: active ? '0 0 6px rgba(22,119,255,0.5)' : undefined,
                  }}
                />
              </div>
            </Link>
          )
        })}
      </div>

      {/* 底部版权 */}
      <div className="px-4 pt-3 border-t" style={{ borderColor: 'rgba(0,0,0,0.04)' }}>
        <p className="text-[9px]" style={{ color: 'rgb(100,116,139)' }}>
          数据来源 Yahoo Finance · Morningstar
        </p>
      </div>
    </nav>
  )
}
