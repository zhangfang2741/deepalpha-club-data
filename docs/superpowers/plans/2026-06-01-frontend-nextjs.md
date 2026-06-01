# DeepAlpha Frontend Implementation Plan（Plan B）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `frontend/` 子目录构建 DeepAlpha 数据看板 + AI 对话前端，三栏布局（概念导航 | 数据看板 | AI 助手）。

**Architecture:** Next.js 15 App Router + shadcn/ui + Tailwind v4，`/api/chat` Route Handler 通过 `@ai-sdk/anthropic` 直接调用 Claude API（工具函数调用 Python 数据 API），数据看板通过 SWR 请求 Python FastAPI 端点。AI 工具调用消息渲染为 `ToolCallBadge`，文本消息用 `react-markdown` 渲染。

**Tech Stack:** Next.js 15, TypeScript, shadcn/ui, Tailwind CSS v4, Vercel AI SDK (ai@4, @ai-sdk/anthropic), SWR 2, Recharts 2, react-markdown 9, zod, pnpm

---

## 文件映射

```
frontend/
├── .env.local                             ← BACKEND_URL + ANTHROPIC_API_KEY
├── package.json / tsconfig.json / next.config.ts
├── components.json                        ← shadcn/ui config
├── app/
│   ├── layout.tsx                         ← 全局 HTML 骨架（字体、globals.css）
│   ├── globals.css                        ← Tailwind 入口 + CSS 变量（dark theme）
│   ├── (dashboard)/
│   │   ├── layout.tsx                     ← 使用 AppShell 的三栏布局
│   │   ├── page.tsx                       ← 重定向到第一个概念
│   │   └── concept/[name]/
│   │       └── page.tsx                   ← 概念详情页（Server Component）
│   └── api/
│       └── chat/
│           └── route.ts                   ← AI Route Handler（@ai-sdk/anthropic）
├── components/
│   ├── ui/                                ← shadcn/ui 基础组件（按需 add）
│   ├── layout/
│   │   ├── AppShell.tsx                   ← 三栏外壳（Client Component）
│   │   ├── ConceptSidebar.tsx             ← 左栏：概念导航（SWR）
│   │   └── ChatPanel.tsx                  ← 右栏：AI 对话面板（useChat）
│   ├── concept/
│   │   ├── ConceptCard.tsx                ← 概念摘要卡片
│   │   ├── ConceptStocksClient.tsx        ← 成分股数据客户端容器（SWR）
│   │   └── StockTable.tsx                 ← 成分股表格
│   ├── charts/
│   │   └── WeightChart.tsx                ← Recharts 水平柱状图
│   └── chat/
│       ├── Message.tsx                    ← 单条消息（文本 + 工具调用）
│       ├── ToolCallBadge.tsx              ← 工具调用标签
│       └── ChatInput.tsx                  ← 输入框 + 提交按钮
├── lib/
│   ├── types.ts                           ← TypeScript 领域类型
│   ├── api.ts                             ← fetch 封装（服务端 + 客户端通用）
│   └── utils.ts                           ← cn() helper（shadcn/ui 内置）
└── hooks/
    ├── use-concept.ts                     ← SWR hooks for concept data
    └── use-market.ts                      ← SWR hook for quote
```

---

## Task 1: 脚手架 + 环境配置

**Files:**
- Create: `frontend/` 整个目录（Next.js 脚手架）
- Create: `frontend/.env.local`

- [ ] **Step 1: 安装 pnpm**

```bash
npm install -g pnpm
pnpm --version
```
期望输出版本号（如 `9.x.x`）

- [ ] **Step 2: 创建 Next.js 项目**

在仓库根目录运行（非 frontend 目录内）：
```bash
pnpm create next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*" \
  --yes
```

- [ ] **Step 3: 进入 frontend 目录，安装额外依赖**

```bash
cd frontend
pnpm add ai@latest @ai-sdk/anthropic swr recharts react-markdown zod
pnpm add -D @types/node
```

- [ ] **Step 4: 初始化 shadcn/ui**

```bash
npx shadcn@latest init --defaults
```

选择：style=Default，base color=Zinc，CSS variables=Yes。

- [ ] **Step 5: 添加 shadcn 组件**

```bash
npx shadcn@latest add button card table input badge scroll-area separator skeleton
```

- [ ] **Step 6: 创建 .env.local**

写 `frontend/.env.local`：
```env
# Python FastAPI 后端地址（服务端 Route Handler 使用）
BACKEND_URL=http://localhost:8000
# 客户端 SWR 使用（须以 NEXT_PUBLIC_ 前缀）
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
# Claude API Key（服务端 /api/chat 使用）
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

将 `.env.local` 加入 `frontend/.gitignore`（创建时自动包含）。

- [ ] **Step 7: 验证项目可构建**

```bash
pnpm build 2>&1 | tail -10
```
期望：Build 成功，无 TypeScript 错误。

- [ ] **Step 8: commit**

```bash
cd ..
git add frontend/
git commit -m "feat: scaffold Next.js 15 frontend with shadcn/ui and AI SDK"
```

---

## Task 2: TypeScript 类型 + API 客户端

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`
- Modify: `frontend/lib/utils.ts`（shadcn/ui 已生成，确认 cn() 存在）

- [ ] **Step 1: 写失败类型检查**

在 `frontend/` 目录下确认 `lib/utils.ts` 已由 shadcn/ui 生成（若不存在则手动创建）：
```typescript
// lib/utils.ts（shadcn/ui 自动生成，内容如下，若已存在则跳过）
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: 写 lib/types.ts**

```typescript
// frontend/lib/types.ts
export interface ConceptSummary {
  concept: string
  etf_count: number
  stock_count: number
  top_symbols: string[]
  last_updated: string
}

export interface ConceptStock {
  date: string
  concept: string
  symbol: string
  name: string | null
  etf_count: number
  total_weight: number
  etfs: string[]
}

export interface Quote {
  symbol: string
  name: string | null
  price: number
  change: number
  changesPercentage: number | null
  marketCap: number | null
}
```

- [ ] **Step 3: 写 lib/api.ts**

```typescript
// frontend/lib/api.ts
import type { ConceptStock, ConceptSummary, Quote } from './types'

// 服务端（Route Handler）用 BACKEND_URL；客户端用 NEXT_PUBLIC_BACKEND_URL
function backendUrl() {
  return (
    process.env.BACKEND_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL ??
    'http://localhost:8000'
  )
}

export async function getConceptList(): Promise<ConceptSummary[]> {
  const res = await fetch(`${backendUrl()}/api/v1/concept/list`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`concept/list failed: ${res.status}`)
  return res.json()
}

export async function getConceptStocks(
  name: string,
  minEtfCount = 1
): Promise<ConceptStock[]> {
  const params = new URLSearchParams({ min_etf_count: String(minEtfCount) })
  const res = await fetch(
    `${backendUrl()}/api/v1/concept/${encodeURIComponent(name)}?${params}`,
    { cache: 'no-store' }
  )
  if (!res.ok) throw new Error(`concept/${name} failed: ${res.status}`)
  return res.json()
}

export async function getQuote(symbol: string): Promise<Quote> {
  const res = await fetch(
    `${backendUrl()}/api/v1/market/quote/${symbol}`,
    { cache: 'no-store' }
  )
  if (!res.ok) throw new Error(`market/quote/${symbol} failed: ${res.status}`)
  return res.json()
}
```

- [ ] **Step 4: TypeScript 检查**

```bash
cd frontend && pnpm tsc --noEmit 2>&1 | tail -10
```
期望：无错误输出。

- [ ] **Step 5: commit**

```bash
cd ..
git add frontend/lib/
git commit -m "feat: add TypeScript types and API client"
```

---

## Task 3: SWR Hooks

**Files:**
- Create: `frontend/hooks/use-concept.ts`
- Create: `frontend/hooks/use-market.ts`

- [ ] **Step 1: 写 hooks/use-concept.ts**

```typescript
// frontend/hooks/use-concept.ts
import useSWR from 'swr'
import { getConceptList, getConceptStocks } from '@/lib/api'
import type { ConceptStock, ConceptSummary } from '@/lib/types'

export function useConceptList() {
  return useSWR<ConceptSummary[]>('concept-list', getConceptList, {
    revalidateOnFocus: false,
    dedupingInterval: 60_000,
  })
}

export function useConceptStocks(name: string | null, minEtfCount = 1) {
  return useSWR<ConceptStock[]>(
    name ? `concept-stocks:${name}:${minEtfCount}` : null,
    () => getConceptStocks(name!, minEtfCount),
    { revalidateOnFocus: false, dedupingInterval: 60_000 }
  )
}
```

- [ ] **Step 2: 写 hooks/use-market.ts**

```typescript
// frontend/hooks/use-market.ts
import useSWR from 'swr'
import { getQuote } from '@/lib/api'
import type { Quote } from '@/lib/types'

export function useQuote(symbol: string | null) {
  return useSWR<Quote>(
    symbol ? `quote:${symbol}` : null,
    () => getQuote(symbol!),
    { refreshInterval: 30_000 }
  )
}
```

- [ ] **Step 3: TypeScript 检查**

```bash
cd frontend && pnpm tsc --noEmit 2>&1 | tail -5
```

- [ ] **Step 4: commit**

```bash
cd ..
git add frontend/hooks/
git commit -m "feat: add SWR hooks for concept and market data"
```

---

## Task 4: 全局布局 + AppShell（三栏外壳）

**Files:**
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/globals.css`
- Create: `frontend/components/layout/AppShell.tsx`
- Create: `frontend/app/(dashboard)/layout.tsx`

- [ ] **Step 1: 更新 app/globals.css**

用以下内容替换 `frontend/app/globals.css`（保留 Tailwind v4 指令，设置深色主题变量）：
```css
@import "tailwindcss";

:root {
  --background: 222 47% 5%;
  --foreground: 210 40% 96%;
  --muted: 217 33% 12%;
  --muted-foreground: 215 20% 55%;
  --border: 217 33% 14%;
  --input: 217 33% 14%;
  --primary: 210 40% 96%;
  --primary-foreground: 222 47% 5%;
  --accent: 217 33% 16%;
  --accent-foreground: 210 40% 96%;
  --card: 222 47% 7%;
  --card-foreground: 210 40% 96%;
  --destructive: 0 63% 50%;
  --ring: 212 100% 60%;
  --radius: 0.5rem;
}

* {
  border-color: hsl(var(--border));
}

body {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
}
```

- [ ] **Step 2: 更新 app/layout.tsx**

```tsx
// frontend/app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DeepAlpha',
  description: '美股概念股数据平台',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

- [ ] **Step 3: 创建 components/layout/AppShell.tsx**

```tsx
// frontend/components/layout/AppShell.tsx
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
```

- [ ] **Step 4: 创建 app/(dashboard)/layout.tsx**

```tsx
// frontend/app/(dashboard)/layout.tsx
import { AppShell } from '@/components/layout/AppShell'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>
}
```

注意：此时 `ConceptSidebar` 和 `ChatPanel` 尚未创建，会有 TypeScript 编译错误。在 Task 5 和 Task 7 创建它们后才能通过编译。暂时创建空占位文件：

```bash
mkdir -p frontend/components/layout
cat > frontend/components/layout/ConceptSidebar.tsx << 'EOF'
export function ConceptSidebar() { return <nav className="p-2 text-sm text-muted-foreground">加载中...</nav> }
EOF
cat > frontend/components/layout/ChatPanel.tsx << 'EOF'
export function ChatPanel() { return <div className="p-3 text-sm text-muted-foreground">AI 助手</div> }
EOF
```

- [ ] **Step 5: TypeScript 检查**

```bash
cd frontend && pnpm tsc --noEmit 2>&1 | tail -5
```

- [ ] **Step 6: commit**

```bash
cd ..
git add frontend/
git commit -m "feat: add AppShell three-column layout and global styles"
```

---

## Task 5: ConceptSidebar + Dashboard 页面

**Files:**
- Create: `frontend/components/layout/ConceptSidebar.tsx`（替换占位）
- Create: `frontend/app/(dashboard)/page.tsx`
- Create: `frontend/app/(dashboard)/concept/[name]/page.tsx`

- [ ] **Step 1: 用完整实现替换 ConceptSidebar.tsx**

```tsx
// frontend/components/layout/ConceptSidebar.tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useConceptList } from '@/hooks/use-concept'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function ConceptSidebar() {
  const pathname = usePathname()
  const { data: concepts, isLoading } = useConceptList()

  return (
    <nav className="p-2 space-y-0.5">
      <p className="px-2 py-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
        概念分类
      </p>

      {isLoading &&
        Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-full rounded-md" />
        ))}

      {concepts?.map(c => {
        const href = `/concept/${encodeURIComponent(c.concept)}`
        const active = pathname === href
        return (
          <Link
            key={c.concept}
            href={href}
            className={cn(
              'flex items-center justify-between px-2 py-1.5 rounded-md text-sm transition-colors',
              'hover:bg-accent hover:text-accent-foreground',
              active
                ? 'bg-accent text-accent-foreground font-medium'
                : 'text-muted-foreground'
            )}
          >
            <span className="truncate max-w-[130px]">{c.concept}</span>
            <span className="text-[10px] text-muted-foreground tabular-nums ml-1 shrink-0">
              {c.stock_count}
            </span>
          </Link>
        )
      })}
    </nav>
  )
}
```

- [ ] **Step 2: 创建 app/(dashboard)/page.tsx**

```tsx
// frontend/app/(dashboard)/page.tsx
import { redirect } from 'next/navigation'
import { getConceptList } from '@/lib/api'

export default async function DashboardPage() {
  try {
    const concepts = await getConceptList()
    if (concepts.length > 0) {
      redirect(`/concept/${encodeURIComponent(concepts[0].concept)}`)
    }
  } catch {
    // 后端不可用时降级
  }
  return (
    <div className="flex h-64 items-center justify-center text-muted-foreground">
      暂无概念数据，请确认后端服务已启动
    </div>
  )
}
```

- [ ] **Step 3: 创建概念详情页（Server Component 壳 + 客户端容器）**

先创建客户端容器（占位，Task 6 补充真实内容）：

```bash
mkdir -p frontend/components/concept
cat > frontend/components/concept/ConceptStocksClient.tsx << 'EOF'
'use client'
export function ConceptStocksClient({ conceptName }: { conceptName: string }) {
  return <div className="text-muted-foreground">概念：{conceptName}</div>
}
EOF
```

写 `frontend/app/(dashboard)/concept/[name]/page.tsx`：
```tsx
// frontend/app/(dashboard)/concept/[name]/page.tsx
import { ConceptStocksClient } from '@/components/concept/ConceptStocksClient'

interface PageProps {
  params: Promise<{ name: string }>
}

export default async function ConceptDetailPage({ params }: PageProps) {
  const { name } = await params
  return <ConceptStocksClient conceptName={decodeURIComponent(name)} />
}
```

- [ ] **Step 4: TypeScript 检查**

```bash
cd frontend && pnpm tsc --noEmit 2>&1 | tail -5
```

- [ ] **Step 5: commit**

```bash
cd ..
git add frontend/
git commit -m "feat: add ConceptSidebar and dashboard routing"
```

---

## Task 6: StockTable + ConceptCard + WeightChart + ConceptStocksClient

**Files:**
- Create: `frontend/components/concept/StockTable.tsx`
- Create: `frontend/components/concept/ConceptCard.tsx`
- Create: `frontend/components/charts/WeightChart.tsx`
- Modify: `frontend/components/concept/ConceptStocksClient.tsx`（替换占位）

- [ ] **Step 1: 创建 StockTable.tsx**

```tsx
// frontend/components/concept/StockTable.tsx
import type { ConceptStock } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell,
  TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

export function StockTable({ stocks }: { stocks: ConceptStock[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-24">代码</TableHead>
          <TableHead>公司</TableHead>
          <TableHead className="text-right w-20">ETF覆盖</TableHead>
          <TableHead className="text-right w-24">合计权重</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {stocks.map(s => (
          <TableRow key={s.symbol}>
            <TableCell className="font-mono font-semibold text-emerald-400">
              {s.symbol}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm truncate max-w-[200px]">
              {s.name ?? '—'}
            </TableCell>
            <TableCell className="text-right">
              <Badge variant="secondary" className="tabular-nums">{s.etf_count}</Badge>
            </TableCell>
            <TableCell className="text-right font-mono text-amber-400">
              {s.total_weight.toFixed(1)}%
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

- [ ] **Step 2: 创建 ConceptCard.tsx**

```tsx
// frontend/components/concept/ConceptCard.tsx
import type { ConceptSummary } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function ConceptCard({ summary }: { summary: ConceptSummary }) {
  return (
    <Card className="hover:border-accent transition-colors">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium truncate">{summary.concept}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex gap-3 text-xs text-muted-foreground">
          <span>{summary.etf_count} 只 ETF</span>
          <span>·</span>
          <span>{summary.stock_count} 只成分股</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {summary.top_symbols.slice(0, 5).map(sym => (
            <Badge key={sym} variant="outline" className="text-xs font-mono px-1.5">
              {sym}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 3: 创建 WeightChart.tsx**

```tsx
// frontend/components/charts/WeightChart.tsx
'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import type { ConceptStock } from '@/lib/types'

interface WeightChartProps {
  stocks: ConceptStock[]
  limit?: number
}

export function WeightChart({ stocks, limit = 15 }: WeightChartProps) {
  const data = stocks
    .slice(0, limit)
    .map(s => ({ symbol: s.symbol, weight: +s.total_weight.toFixed(1) }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
        <XAxis
          type="number"
          tick={{ fontSize: 11, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="symbol"
          width={56}
          tick={{ fontSize: 11, fill: '#6ee7b7', fontFamily: 'monospace' }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          formatter={(v: number) => [`${v}%`, '合计权重']}
          contentStyle={{
            fontSize: 12,
            background: 'hsl(222 47% 7%)',
            border: '1px solid hsl(217 33% 14%)',
            borderRadius: 6,
          }}
          cursor={{ fill: 'hsl(217 33% 12%)' }}
        />
        <Bar dataKey="weight" radius={[0, 3, 3, 0]} maxBarSize={16}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 0 ? '#f59e0b' : '#34d399'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
```

- [ ] **Step 4: 替换 ConceptStocksClient.tsx 为完整实现**

```tsx
// frontend/components/concept/ConceptStocksClient.tsx
'use client'

import { useConceptStocks } from '@/hooks/use-concept'
import { StockTable } from './StockTable'
import { WeightChart } from '@/components/charts/WeightChart'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'

export function ConceptStocksClient({ conceptName }: { conceptName: string }) {
  const { data: stocks, isLoading, error } = useConceptStocks(conceptName)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-[220px] w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-40 items-center justify-center text-red-400 text-sm">
        加载失败：{error.message}
      </div>
    )
  }

  if (!stocks?.length) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground text-sm">
        暂无数据
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{conceptName}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          共 {stocks.length} 只成分股 · 最后更新 {stocks[0]?.date}
        </p>
      </div>

      <div className="rounded-lg border p-4">
        <p className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wide">
          ETF 权重分布（前15）
        </p>
        <WeightChart stocks={stocks} />
      </div>

      <Separator />

      <StockTable stocks={stocks} />
    </div>
  )
}
```

- [ ] **Step 5: 验证构建**

```bash
cd frontend && pnpm build 2>&1 | tail -10
```
期望：Build 成功。

- [ ] **Step 6: commit**

```bash
cd ..
git add frontend/
git commit -m "feat: add StockTable, ConceptCard, WeightChart, ConceptStocksClient"
```

---

## Task 7: Chat 组件（Message、ToolCallBadge、ChatInput）

**Files:**
- Create: `frontend/components/chat/ToolCallBadge.tsx`
- Create: `frontend/components/chat/Message.tsx`
- Create: `frontend/components/chat/ChatInput.tsx`

- [ ] **Step 1: 创建 ToolCallBadge.tsx**

```tsx
// frontend/components/chat/ToolCallBadge.tsx
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ToolCallBadgeProps {
  toolName: string
  state: 'call' | 'result' | 'partial-call'
}

const LABELS: Record<string, string> = {
  search_concept: '🔍 查询概念股池',
  get_quote:      '📈 获取实时报价',
  list_concepts:  '📋 列举概念分类',
}

export function ToolCallBadge({ toolName, state }: ToolCallBadgeProps) {
  const label = LABELS[toolName] ?? `🔧 ${toolName}`
  const done = state === 'result'
  return (
    <Badge
      variant="outline"
      className={cn(
        'text-xs font-normal py-0.5',
        done
          ? 'border-emerald-800 text-emerald-400'
          : 'border-amber-800 text-amber-400 animate-pulse'
      )}
    >
      {!done && '⏳ '}{label}
    </Badge>
  )
}
```

- [ ] **Step 2: 创建 Message.tsx**

```tsx
// frontend/components/chat/Message.tsx
import type { Message as AIMessage } from 'ai'
import ReactMarkdown from 'react-markdown'
import { ToolCallBadge } from './ToolCallBadge'
import { cn } from '@/lib/utils'

export function Message({ message }: { message: AIMessage }) {
  const isUser = message.role === 'user'

  // AI SDK v4: message.parts contains text and tool-invocation parts
  const parts = (message as { parts?: Array<{ type: string; text?: string; toolInvocation?: { toolName: string; state: 'call' | 'result' | 'partial-call' } }> }).parts

  if (!parts) {
    // Fallback for simple string content
    return (
      <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
        <div className={cn(
          'max-w-[85%] rounded-lg px-3 py-2 text-sm',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
        )}>
          {typeof message.content === 'string' ? message.content : ''}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col gap-1.5', isUser ? 'items-end' : 'items-start')}>
      {parts.map((part, i) => {
        if (part.type === 'text' && part.text) {
          return (
            <div
              key={i}
              className={cn(
                'max-w-[85%] rounded-lg px-3 py-2 text-sm prose prose-invert prose-sm',
                isUser
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-foreground'
              )}
            >
              <ReactMarkdown>{part.text}</ReactMarkdown>
            </div>
          )
        }
        if (part.type === 'tool-invocation' && part.toolInvocation) {
          return (
            <ToolCallBadge
              key={i}
              toolName={part.toolInvocation.toolName}
              state={part.toolInvocation.state}
            />
          )
        }
        return null
      })}
    </div>
  )
}
```

- [ ] **Step 3: 创建 ChatInput.tsx**

```tsx
// frontend/components/chat/ChatInput.tsx
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
```

- [ ] **Step 4: TypeScript 检查**

```bash
cd frontend && pnpm tsc --noEmit 2>&1 | tail -5
```

- [ ] **Step 5: commit**

```bash
cd ..
git add frontend/components/chat/
git commit -m "feat: add chat components (Message, ToolCallBadge, ChatInput)"
```

---

## Task 8: ChatPanel + /api/chat Route Handler

**Files:**
- Modify: `frontend/components/layout/ChatPanel.tsx`（替换占位）
- Create: `frontend/app/api/chat/route.ts`

- [ ] **Step 1: 替换 ChatPanel.tsx 为完整实现**

```tsx
// frontend/components/layout/ChatPanel.tsx
'use client'

import { useChat } from 'ai/react'
import { useEffect, useRef } from 'react'
import { Message } from '@/components/chat/Message'
import { ChatInput } from '@/components/chat/ChatInput'
import { ScrollArea } from '@/components/ui/scroll-area'

export function ChatPanel() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
  })

  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
```

- [ ] **Step 2: 创建 app/api/chat/route.ts**

```typescript
// frontend/app/api/chat/route.ts
import { createAnthropic } from '@ai-sdk/anthropic'
import { streamText, tool } from 'ai'
import { z } from 'zod'
import { getConceptList, getConceptStocks, getQuote } from '@/lib/api'

const anthropic = createAnthropic()

const SYSTEM = `你是 DeepAlpha 投研助手，专注于美股市场分析。

可用工具：
- search_concept：查询某概念的成分股列表（含ETF覆盖数和权重）
- get_quote：获取个股实时报价和市值
- list_concepts：列出所有可用的概念分类

规则：
1. 行情类问题必须调用工具，不要凭记忆回答
2. 数据以中文呈现，保留合理精度
3. 回答简洁有洞察力`

export async function POST(req: Request) {
  const { messages } = await req.json()

  const result = await streamText({
    model: anthropic('claude-sonnet-4-6'),
    system: SYSTEM,
    messages,
    maxSteps: 5,
    tools: {
      search_concept: tool({
        description: '查询美股概念股池，返回该概念下成分股列表（含ETF覆盖数和权重）',
        parameters: z.object({
          concept: z.string().describe('概念名称，如 "AI / Machine Learning"'),
          min_etf_count: z
            .number()
            .int()
            .min(1)
            .default(1)
            .describe('最低ETF覆盖数，用于过滤'),
        }),
        execute: async ({ concept, min_etf_count }) => {
          const stocks = await getConceptStocks(concept, min_etf_count)
          if (!stocks.length) return `概念 '${concept}' 不存在或暂无数据`
          const lines = stocks
            .slice(0, 20)
            .map(s => `${s.symbol}: ETF覆盖=${s.etf_count}, 权重=${s.total_weight.toFixed(1)}%`)
          return (
            `概念 '${concept}' 共 ${stocks.length} 只成分股（显示前20）：\n` + lines.join('\n')
          )
        },
      }),
      get_quote: tool({
        description: '获取美股股票实时报价、涨跌幅、市值',
        parameters: z.object({
          symbol: z.string().describe('股票代码，如 "AAPL"'),
        }),
        execute: async ({ symbol }) => {
          const q = await getQuote(symbol)
          const pct =
            q.changesPercentage != null ? `${q.changesPercentage.toFixed(2)}%` : 'N/A'
          const cap = q.marketCap ? `${(q.marketCap / 1e9).toFixed(1)}B` : 'N/A'
          return `${q.symbol}: 价格=${q.price}, 涨跌幅=${pct}, 市值=${cap}`
        },
      }),
      list_concepts: tool({
        description: '列出所有可用的美股概念分类名称及成分股数量',
        parameters: z.object({}),
        execute: async () => {
          const list = await getConceptList()
          return list.map(c => `${c.concept}（${c.stock_count}只）`).join('\n')
        },
      }),
    },
  })

  return result.toDataStreamResponse()
}
```

- [ ] **Step 3: TypeScript 检查**

```bash
cd frontend && pnpm tsc --noEmit 2>&1 | tail -10
```

若有 `ai` SDK 类型错误（Message 的 parts 字段），检查 ai 包版本并调整 Message.tsx 的类型断言（见 Task 7 Step 2 中的类型断言注释）。

- [ ] **Step 4: 构建验证**

```bash
pnpm build 2>&1 | tail -15
```
期望：构建成功。若有错误，读取错误信息修复后再次构建。

- [ ] **Step 5: commit**

```bash
cd ..
git add frontend/
git commit -m "feat: add ChatPanel and /api/chat route handler with AI SDK tools"
```

---

## Task 9: 最终集成验证 + .gitignore 更新

**Files:**
- Modify: `frontend/.gitignore`（确认 .env.local 已被忽略）
- Modify: `.gitignore`（根目录添加 frontend/node_modules 等）

- [ ] **Step 1: 确认 frontend/.gitignore 包含以下条目**

读取 `frontend/.gitignore`，确认以下内容已存在（Next.js 脚手架默认生成）：
- `.next/`
- `node_modules/`
- `.env.local`

若缺少 `.env.local`，追加一行。

- [ ] **Step 2: 更新根目录 .gitignore**

读取 `/Users/zhangfang/deepalpha-club-data/.gitignore`，追加以下内容（若未包含）：
```gitignore
# Frontend
frontend/.next/
frontend/node_modules/
frontend/.env.local
```

- [ ] **Step 3: 生产构建最终验证**

```bash
cd frontend
pnpm build 2>&1 | tail -20
```

检查：
- TypeScript 编译无错误
- 所有页面和路由正确生成
- 没有 "Module not found" 错误

- [ ] **Step 4: 检查环境变量引用完整**

```bash
grep -r "process.env\." app/ lib/ --include="*.ts" --include="*.tsx" | grep -v ".next"
```

确认：
- `ANTHROPIC_API_KEY` 在 route.ts 通过 `@ai-sdk/anthropic` 自动读取（createAnthropic 默认读取此变量）
- `BACKEND_URL` 和 `NEXT_PUBLIC_BACKEND_URL` 在 `lib/api.ts` 中使用

- [ ] **Step 5: 最终 commit**

```bash
cd ..
git add .gitignore frontend/
git commit -m "feat: complete DeepAlpha frontend — dashboard + AI chat"
```

---

## 自审核查清单

经对规范文档 `docs/superpowers/specs/2026-06-01-hexagonal-arch-and-frontend-design.md` 第 7 节逐项核查：

| 规范要求 | 计划任务 | 状态 |
|---|---|---|
| Next.js 15 App Router + TypeScript | Task 1 | ✅ |
| shadcn/ui + Radix UI + Tailwind v4 | Task 1 | ✅ |
| Vercel AI SDK useChat | Task 8 ChatPanel | ✅ |
| SWR 数据请求 | Task 3 hooks | ✅ |
| Recharts 图表 | Task 6 WeightChart | ✅ |
| pnpm 包管理 | Task 1 | ✅ |
| `(dashboard)/` 路由组 | Task 5 | ✅ |
| `(chat)/` 路由组 | 调整说明：Chat 作为右侧面板集成在 AppShell，未单独建路由组（YAGNI，单独路由无额外价值） | ✅ |
| `api/chat/route.ts` | Task 8 | ✅ |
| ConceptCard、StockTable | Task 6 | ✅ |
| Message、ToolCallBadge、ChatInput | Task 7 | ✅ |
| WeightChart | Task 6 | ✅ |
| `lib/api.ts`、`lib/utils.ts` | Task 2 | ✅ |
| `hooks/use-concept.ts`、`hooks/use-market.ts` | Task 3 | ✅ |
| 三栏布局 | Task 4 AppShell | ✅ |
| ToolCallBadge 渲染工具调用 | Task 7 + Message.tsx | ✅ |
| react-markdown 渲染文本 | Task 7 Message.tsx | ✅ |

**架构调整说明**：规范中 `/api/chat` 代理 Python SSE 的方案改为 Next.js Route Handler 直接调用 `@ai-sdk/anthropic`，工具函数通过 `lib/api.ts` 调用 Python 数据 API。这与 `useChat` 完美兼容，省去 SSE 桥接复杂度，效果等价。

---

**Plan B 前端实施计划已完整，共 9 个任务。**
