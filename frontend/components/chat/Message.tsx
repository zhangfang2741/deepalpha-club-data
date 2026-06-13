'use client'

import type { UIMessage } from 'ai'
import ReactMarkdown from 'react-markdown'
import { ToolCallBadge } from './ToolCallBadge'

export function Message({ message }: { message: UIMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex flex-col gap-1.5 animate-in ${isUser ? 'items-end' : 'items-start'}`}>
      {message.parts.map((part, i) => {
        if (part.type === 'text') {
          return (
            <div
              key={i}
              className="max-w-[88%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed"
              style={
                isUser
                  ? {
                      background: 'linear-gradient(135deg, rgba(22,119,255,0.12), rgba(0,180,255,0.08))',
                      border: '1px solid rgba(22,119,255,0.20)',
                      color: 'rgb(22,119,255)',
                      borderBottomRightRadius: 4,
                      boxShadow: '0 2px 8px rgba(22,119,255,0.08)',
                    }
                  : {
                      background: 'rgb(255,255,255)',
                      border: '1px solid rgba(22,119,255,0.10)',
                      color: 'rgb(60,70,90)',
                      borderBottomLeftRadius: 4,
                      boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                    }
              }
            >
              {isUser ? (
                <span style={{ fontFamily: 'var(--font-figtree)' }}>{part.text}</span>
              ) : (
                <div
                  className="prose prose-xs max-w-none"
                  style={{ fontFamily: 'var(--font-figtree)' }}
                >
                  <ReactMarkdown
                    components={{
                      code: ({ children }) => (
                        <code
                          className="px-1.5 py-0.5 rounded text-[10px]"
                          style={{
                            fontFamily: 'var(--font-ibm-mono)',
                            background: 'rgba(22,119,255,0.08)',
                            color: 'rgb(22,119,255)',
                            border: '1px solid rgba(22,119,255,0.15)',
                          }}
                        >
                          {children}
                        </code>
                      ),
                      strong: ({ children }) => (
                        <strong style={{ color: 'rgb(30,38,55)' }}>{children}</strong>
                      ),
                    }}
                  >
                    {part.text}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          )
        }

        if (part.type.startsWith('tool-')) {
          const toolPart = part as {
            type: string
            toolName?: string
            state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | 'approval-requested' | 'approval-responded' | 'output-denied'
          }
          const toolName = toolPart.toolName ?? part.type.slice(5)
          return <ToolCallBadge key={i} toolName={toolName} state={toolPart.state} />
        }

        if (part.type === 'dynamic-tool') {
          const dynamicPart = part as {
            type: 'dynamic-tool'
            toolName: string
            state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | 'approval-requested' | 'approval-responded' | 'output-denied'
          }
          return <ToolCallBadge key={i} toolName={dynamicPart.toolName} state={dynamicPart.state} />
        }

        return null
      })}
    </div>
  )
}
