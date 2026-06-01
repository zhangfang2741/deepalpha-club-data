'use client'

import type { FormEvent, ChangeEvent } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
  input: string
  isLoading: boolean
  onInputChange: (e: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
}

export function ChatInput({ input, isLoading, onInputChange, onSubmit }: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="flex gap-2 p-3 border-t shrink-0">
      <Input
        value={input}
        onChange={onInputChange}
        placeholder="分析 NVDA 在 AI 概念中的地位..."
        disabled={isLoading}
        className="flex-1 text-sm h-8"
        autoComplete="off"
      />
      <Button
        type="submit"
        size="sm"
        className="h-8 px-3"
        disabled={isLoading || !input.trim()}
      >
        ↑
      </Button>
    </form>
  )
}
