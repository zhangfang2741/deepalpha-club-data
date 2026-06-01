'use client'

import type { UIMessage } from 'ai'
import ReactMarkdown from 'react-markdown'
import { ToolCallBadge } from './ToolCallBadge'
import { cn } from '@/lib/utils'

export function Message({ message }: { message: UIMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex flex-col gap-1.5', isUser ? 'items-end' : 'items-start')}>
      {message.parts.map((part, i) => {
        // 纯文本 part
        if (part.type === 'text') {
          return (
            <div
              key={i}
              className={cn(
                'max-w-[85%] rounded-lg px-3 py-2 text-sm',
                isUser
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-foreground'
              )}
            >
              {isUser ? part.text : <ReactMarkdown>{part.text}</ReactMarkdown>}
            </div>
          )
        }

        // tool-${toolName} 格式的工具调用 part
        if (part.type.startsWith('tool-')) {
          const toolPart = part as {
            type: string
            toolName?: string
            state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | 'approval-requested' | 'approval-responded' | 'output-denied'
          }
          // 从 type 字段提取 toolName（格式：tool-{toolName}）
          const toolName = toolPart.toolName ?? part.type.slice(5)
          return (
            <ToolCallBadge
              key={i}
              toolName={toolName}
              state={toolPart.state}
            />
          )
        }

        // dynamic-tool part
        if (part.type === 'dynamic-tool') {
          const dynamicPart = part as {
            type: 'dynamic-tool'
            toolName: string
            state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | 'approval-requested' | 'approval-responded' | 'output-denied'
          }
          return (
            <ToolCallBadge
              key={i}
              toolName={dynamicPart.toolName}
              state={dynamicPart.state}
            />
          )
        }

        // step-start、reasoning 等跳过
        return null
      })}
    </div>
  )
}
