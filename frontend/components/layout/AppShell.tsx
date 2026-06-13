'use client'

import Link from 'next/link'
import { VizProvider } from '@/lib/viz-context'
import { ChatPanel } from './ChatPanel'
import { VizPanel } from '../viz/VizPanel'

export function AppShell({ children }: { children?: React.ReactNode }) {
  return (
    <VizProvider>
      <div className="flex h-screen flex-col relative z-10">

        {/* ── 顶栏（保持深色，突出导航） ── */}
        <header
          className="flex h-12 shrink-0 items-center px-5 gap-4"
          style={{
            background: 'rgb(22,119,255)',
            borderBottom: 'none',
            boxShadow: '0 2px 8px rgba(22,119,255,0.30)',
          }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="h-7 w-7 rounded-lg flex items-center justify-center text-[11px] font-bold animate-float"
              style={{
                background: 'linear-gradient(135deg, rgb(22,119,255), rgb(0,210,255))',
                color: 'white',
                fontFamily: 'var(--font-bricolage)',
                boxShadow: '0 2px 12px rgba(22,119,255,0.4)',
              }}
            >
              Dα
            </div>
            <span
              className="text-sm font-bold tracking-tight"
              style={{ fontFamily: 'var(--font-bricolage)', color: 'rgb(255,255,255)' }}
            >
              DeepAlpha
            </span>
          </div>

          <div className="h-4 w-px mx-1" style={{ background: 'rgba(255,255,255,0.30)' }} />

          <nav className="flex items-center gap-1">
            <span
              className="px-3 py-1.5 text-xs rounded-lg font-medium transition-all duration-200"
              style={{
                color: 'rgb(22,119,255)',
                background: 'rgb(255,255,255)',
                boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
                border: 'none',
              }}
            >
              研究助手
            </span>
            <Link
              href="/radar"
              className="px-3 py-1.5 text-xs rounded-lg transition-all duration-200"
              style={{ color: 'rgba(255,255,255,0.85)' }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLAnchorElement).style.color = 'rgb(255,255,255)'
                ;(e.currentTarget as HTMLAnchorElement).style.background = 'rgba(255,255,255,0.15)'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLAnchorElement).style.color = 'rgba(255,255,255,0.85)'
                ;(e.currentTarget as HTMLAnchorElement).style.background = 'transparent'
              }}
            >
              信号雷达
            </Link>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <span
              className="h-2 w-2 rounded-full"
              style={{
                background: 'rgb(0,200,130)',
                boxShadow: '0 0 8px rgba(0,200,130,0.6)',
                animation: 'pulse-dot 2.5s ease-in-out infinite',
              }}
            />
            <span className="text-[10px] font-medium" style={{ color: 'rgba(255,255,255,0.85)' }}>
              实时数据
            </span>
          </div>
        </header>

        {/* ── 主体两栏 ── */}
        <div className="flex flex-1 overflow-hidden">

          {/* 左：聊天面板（固定宽度，浅色背景）*/}
          <div
            className="w-[420px] shrink-0 flex flex-col"
            style={{
              background: 'rgb(255,255,255)',
              borderRight: '1px solid rgba(0,0,0,0.06)',
              boxShadow: '2px 0 8px rgba(0,0,0,0.04)',
            }}
          >
            <ChatPanel />
          </div>

          {/* 右：可视化面板（蜡烛图 + 动态结果）*/}
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
            <VizPanel />
          </div>

        </div>
      </div>
    </VizProvider>
  )
}