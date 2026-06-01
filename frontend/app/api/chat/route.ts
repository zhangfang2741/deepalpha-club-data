import { createOpenAI } from '@ai-sdk/openai'
import { streamText, tool, stepCountIs } from 'ai'
import { z } from 'zod/v4'
import { getConceptList, getConceptStocks, getQuote } from '@/lib/api'

const minimax = createOpenAI({
  apiKey: process.env.MINIMAX_API_KEY!,
  baseURL: 'https://api.minimax.io/v1',
})

const SYSTEM = `你是 DeepAlpha 投研助手，专注于美股市场分析。

可用工具：
- search_concept：查询某概念的成分股列表（含ETF覆盖数和权重）
- get_quote：获取个股实时报价和市值
- list_concepts：列出所有可用的概念分类

规则：优先调用工具获取最新数据，不要凭记忆回答行情类问题。数据以中文呈现。`

export async function POST(req: Request) {
  const { messages } = await req.json()

  const result = await streamText({
    model: minimax('MiniMax-Text-01'),
    system: SYSTEM,
    messages,
    stopWhen: stepCountIs(5),
    tools: {
      search_concept: tool({
        description: '查询美股概念股池，返回该概念下成分股列表',
        inputSchema: z.object({
          concept: z.string().describe('概念名称，如 "AI / Machine Learning"'),
          min_etf_count: z.number().int().min(1).default(1).describe('最低ETF覆盖数'),
        }),
        execute: async ({ concept, min_etf_count }) => {
          const stocks = await getConceptStocks(concept, min_etf_count)
          if (!stocks.length) return `概念 '${concept}' 不存在或暂无数据`
          const lines = stocks
            .slice(0, 20)
            .map(s => `${s.symbol}: ETF覆盖=${s.etf_count}, 权重=${s.total_weight.toFixed(1)}%`)
          return `概念 '${concept}' 共 ${stocks.length} 只成分股（显示前20）：\n` + lines.join('\n')
        },
      }),
      get_quote: tool({
        description: '获取美股股票实时报价、涨跌幅、市值',
        inputSchema: z.object({
          symbol: z.string().describe('股票代码，如 "AAPL"'),
        }),
        execute: async ({ symbol }) => {
          const q = await getQuote(symbol)
          const pct = q.changesPercentage != null ? `${q.changesPercentage.toFixed(2)}%` : 'N/A'
          const cap = q.marketCap ? `${(q.marketCap / 1e9).toFixed(1)}B` : 'N/A'
          return `${q.symbol}: 价格=${q.price}, 涨跌幅=${pct}, 市值=${cap}`
        },
      }),
      list_concepts: tool({
        description: '列出所有可用的美股概念分类名称及成分股数量',
        inputSchema: z.object({}),
        execute: async () => {
          const list = await getConceptList()
          return list.map(c => `${c.concept}（${c.stock_count}只）`).join('\n')
        },
      }),
    },
  })

  return result.toUIMessageStreamResponse()
}
