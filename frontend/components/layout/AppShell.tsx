'use client'

import { VizProvider } from '@/lib/viz-context'
import { ChatPanel } from './ChatPanel'
import { VizPanel } from '../viz/VizPanel'

export function AppShell({ children }: { children?: React.ReactNode }) {
  return (
    <VizProvider>
      <div className="flex h-screen flex-col relative z-10">

        {/* ── 顶栏 ── */}
        <header
          className="flex h-12 shrink-0 items-center px-5 gap-4"
          style={{
            background: 'rgba(8,14,30,0.97)',
            borderBottom: '1px solid rgba(99,130,190,0.12)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="h-6 w-6 rounded flex items-center justify-center text-[10px] font-bold"
              style={{
                background: 'linear-gradient(135deg, rgb(34,211,238), rgb(129,140,248))',
                color: 'rgb(8,14,30)',
                fontFamily: 'var(--font-bricolage)',
              }}
            >
              Dα
            </div>
            <span
              className="text-sm font-semibold tracking-tight"
              style={{ fontFamily: 'var(--font-bricolage)', color: 'rgb(225,235,255)' }}
            >
              DeepAlpha
            </span>
          </div>

          <div className="h-4 w-px mx-1" style={{ background: 'rgba(99,130,190,0.2)' }} />

          <span className="text-xs" style={{ color: 'rgb(72,90,130)' }}>
            美股投研平台
          </span>

          <div className="ml-auto flex items-center gap-2">
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{
                background: 'rgb(52,211,153)',
                boxShadow: '0 0 6px rgba(52,211,153,0.6)',
                animation: 'pulse-dot 2.5s ease-in-out infinite',
              }}
            />
            <span className="text-[10px]" style={{ color: 'rgb(72,90,130)' }}>
              实时数据
            </span>
          </div>
        </header>

        {/* ── 主体两栏 ── */}
        <div className="flex flex-1 overflow-hidden">

          {/* 左：聊天面板（固定宽度）*/}
          <div
            className="w-[420px] shrink-0 flex flex-col"
            style={{
              background: 'rgb(8,14,30)',
              borderRight: '1px solid rgba(99,130,190,0.10)',
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
