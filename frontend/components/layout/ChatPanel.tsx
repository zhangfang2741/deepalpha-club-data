'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, useEffect, useRef, type FormEvent, type ChangeEvent } from 'react'
import { Message } from '@/components/chat/Message'
import { useViz } from '@/lib/viz-context'
import { getConceptStocks } from '@/lib/api'

const QUICK_QUESTIONS = [
  'NVDA 最近走势如何？',
  'AI 概念中 ETF 覆盖最高的股票？',
  'AAPL 利润表',
  '列出所有可用概念',
]

export function ChatPanel() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  })

  const { setActiveSymbol, setResult } = useViz()
  const [input, setInput] = useState('')
  const isLoading = status === 'submitted' || status === 'streaming'
  const bottomRef = useRef<HTMLDivElement>(null)

  // ── 滚动到底 ──────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── 监听工具调用完成，驱动右侧可视化 ────────────────────────────────────
  useEffect(() => {
    for (const msg of messages) {
      if (msg.role !== 'assistant') continue
      for (const part of msg.parts) {
        if (!part.type.startsWith('tool-')) continue
        const p = part as { type: string; toolName?: string; state: string; input?: Record<string, unknown>; output?: string }
        if (p.state !== 'output-available') continue

        const toolName = p.toolName ?? p.type.slice(5)
        const inp = p.input ?? {}
        const out = p.output ?? ''

        if (toolName === 'get_quote') {
          const symbol = String(inp.symbol ?? '').toUpperCase()
          if (symbol) {
            setActiveSymbol(symbol)
            setResult({ kind: 'quote', symbol, output: out })
          }
        } else if (toolName === 'get_financials') {
          const symbol = String(inp.symbol ?? '').toUpperCase()
          if (symbol) {
            setActiveSymbol(symbol)
            setResult({ kind: 'financials', symbol, output: out })
          }
        } else if (toolName === 'search_concept') {
          const concept = String(inp.concept ?? '')
          if (concept) {
            // 从后端重新拉取结构化数据用于可视化
            getConceptStocks(concept).then(stocks => {
              if (stocks.length) {
                setResult({ kind: 'concept_stocks', concept, stocks })
              }
            }).catch(() => {/* ignore */})
          }
        } else if (toolName === 'list_concepts') {
          setResult({ kind: 'concepts', output: out })
        }
      }
    }
  }, [messages, setActiveSymbol, setResult])

  function handleInputChange(e: ChangeEvent<HTMLInputElement>) {
    setInput(e.target.value)
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const text = input.trim()
    if (!text || isLoading) return
    setInput('')
    sendMessage({ text })
  }

  return (
    <div className="flex flex-col h-full">

      {/* ── 顶栏 ── */}
      <div
        className="flex items-center justify-between px-4 py-3 shrink-0"
        style={{ borderBottom: '1px solid rgba(99,130,190,0.10)' }}
      >
        <div className="flex items-center gap-2">
          <div
            className="h-6 w-6 rounded-md flex items-center justify-center text-[9px] font-bold"
            style={{
              background: 'linear-gradient(135deg, rgb(34,211,238), rgb(129,140,248))',
              color: 'rgb(8,14,30)',
            }}
          >
            AI
          </div>
          <span
            className="text-xs font-semibold"
            style={{ color: 'rgb(180,195,225)', fontFamily: 'var(--font-bricolage)' }}
          >
            投研助手
          </span>
        </div>

        {isLoading && (
          <div className="flex items-center gap-1">
            {[0, 1, 2].map(i => (
              <span
                key={i}
                className="h-1 w-1 rounded-full"
                style={{
                  background: 'rgb(34,211,238)',
                  animation: `pulse-dot 0.9s ease-in-out ${i * 0.15}s infinite`,
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── 消息流 ── */}
      <div className="flex-1 overflow-y-auto min-h-0 px-3 py-3 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col gap-3 pt-4">
            <div className="flex flex-col items-center gap-3 py-4">
              <div
                className="h-14 w-14 rounded-2xl flex items-center justify-center text-2xl"
                style={{
                  background: 'rgba(34,211,238,0.06)',
                  border: '1px solid rgba(34,211,238,0.12)',
                  filter: 'drop-shadow(0 0 12px rgba(34,211,238,0.15))',
                }}
              >
                🔭
              </div>
              <p className="text-xs text-center" style={{ color: 'rgb(100,120,160)' }}>
                询问股票行情、概念成分股、<br />财务数据等投研问题
              </p>
            </div>

            {/* 快捷问题 */}
            <div className="space-y-1.5">
              {QUICK_QUESTIONS.map(q => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs transition-all duration-150"
                  style={{
                    background: 'rgba(13,22,46,0.8)',
                    border: '1px solid rgba(99,130,190,0.10)',
                    color: 'rgb(120,140,180)',
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(34,211,238,0.2)'
                    ;(e.currentTarget as HTMLButtonElement).style.color = 'rgb(180,200,240)'
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(18,30,60,0.9)'
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(99,130,190,0.10)'
                    ;(e.currentTarget as HTMLButtonElement).style.color = 'rgb(120,140,180)'
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(13,22,46,0.8)'
                  }}
                >
                  <span style={{ color: 'rgb(34,211,238)', marginRight: 6 }}>→</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(m => (
          <Message key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* ── 输入框 ── */}
      <div
        className="shrink-0 p-3"
        style={{ borderTop: '1px solid rgba(99,130,190,0.10)' }}
      >
        <form onSubmit={handleSubmit}>
          <div
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl transition-all duration-200"
            style={{
              background: 'rgba(13,22,46,0.9)',
              border: '1px solid rgba(99,130,190,0.15)',
            }}
            onFocusCapture={e => (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(34,211,238,0.35)'}
            onBlurCapture={e => (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(99,130,190,0.15)'}
          >
            <input
              value={input}
              onChange={handleInputChange}
              placeholder="询问任何投研问题…"
              disabled={isLoading}
              className="flex-1 bg-transparent text-xs outline-none placeholder:opacity-40 disabled:opacity-40"
              style={{
                color: 'rgb(225,235,255)',
                fontFamily: 'var(--font-figtree)',
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center h-6 w-6 rounded-lg transition-all duration-150 disabled:opacity-25"
              style={{
                background: 'rgba(34,211,238,0.2)',
                color: 'rgb(34,211,238)',
                border: '1px solid rgba(34,211,238,0.3)',
              }}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M1 9L9 1M9 1H3M9 1V7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
