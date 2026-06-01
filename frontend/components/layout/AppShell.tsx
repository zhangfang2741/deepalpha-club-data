// components/layout/AppShell.tsx
'use client'

import { useState } from 'react'
import { ConceptSidebar } from './ConceptSidebar'
import { ChatPanel } from './ChatPanel'
import { Separator } from '@/components/ui/separator'

export function AppShell({ children }: { children: React.ReactNode }) {
  const [chatOpen, setChatOpen] = useState(true)

  return (
    <div className="flex h-screen flex-col">
      {/* 顶栏 */}
      <header className="flex h-12 shrink-0 items-center border-b px-4 gap-6">
        <span className="font-bold text-amber-400 tracking-tight">DeepAlpha</span>
        <Separator orientation="vertical" className="h-5" />
        <nav className="flex gap-4 text-sm text-muted-foreground">
          <span className="text-foreground font-medium">概念股池</span>
        </nav>
        <button
          onClick={() => setChatOpen(v => !v)}
          className="ml-auto text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          {chatOpen ? '收起助手 ✕' : '▶ AI 助手'}
        </button>
      </header>

      {/* 三栏主体 */}
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-52 shrink-0 border-r overflow-y-auto">
          <ConceptSidebar />
        </aside>

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>

        {chatOpen && (
          <aside className="w-80 shrink-0 border-l flex flex-col">
            <ChatPanel />
          </aside>
        )}
      </div>
    </div>
  )
}
