'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, useEffect, useRef, type FormEvent, type ChangeEvent } from 'react'
import { Message } from '@/components/chat/Message'
import { ChatInput } from '@/components/chat/ChatInput'
import { ScrollArea } from '@/components/ui/scroll-area'

export function ChatPanel() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  })

  const [input, setInput] = useState('')
  const isLoading = status === 'submitted' || status === 'streaming'

  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
    <>
      <div className="px-3 py-2 border-b shrink-0">
        <span className="text-sm font-medium text-amber-400">AI 助手</span>
        {isLoading && (
          <span className="ml-2 text-xs text-muted-foreground animate-pulse">思考中...</span>
        )}
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="flex flex-col gap-3 p-3">
          {messages.length === 0 && (
            <p className="text-xs text-muted-foreground text-center mt-8 px-4">
              询问任何美股相关问题，如「AI 概念股中 ETF 覆盖最高的有哪些？」
            </p>
          )}
          {messages.map(m => (
            <Message key={m.id} message={m} />
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <ChatInput
        input={input}
        isLoading={isLoading}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
      />
    </>
  )
}
