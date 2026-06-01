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
                      background: 'rgba(34,211,238,0.12)',
                      border: '1px solid rgba(34,211,238,0.2)',
                      color: 'rgb(200,230,255)',
                      borderBottomRightRadius: 4,
                    }
                  : {
                      background: 'rgba(18,30,60,0.9)',
                      border: '1px solid rgba(99,130,190,0.15)',
                      color: 'rgb(180,200,240)',
                      borderBottomLeftRadius: 4,
                    }
              }
            >
              {isUser ? (
                <span style={{ fontFamily: 'var(--font-figtree)' }}>{part.text}</span>
              ) : (
                <div
                  className="prose prose-invert prose-xs max-w-none"
                  style={{ fontFamily: 'var(--font-figtree)' }}
                >
                  <ReactMarkdown
                    components={{
                      code: ({ children }) => (
                        <code
                          className="px-1 py-0.5 rounded text-[10px]"
                          style={{
                            fontFamily: 'var(--font-ibm-mono)',
                            background: 'rgba(34,211,238,0.1)',
                            color: 'rgb(34,211,238)',
                          }}
                        >
                          {children}
                        </code>
                      ),
                      strong: ({ children }) => (
                        <strong style={{ color: 'rgb(225,235,255)' }}>{children}</strong>
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
