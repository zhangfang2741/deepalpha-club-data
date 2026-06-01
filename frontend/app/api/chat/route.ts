import { createOpenAI } from '@ai-sdk/openai'
import { streamText, tool, stepCountIs, convertToModelMessages } from 'ai'
import { z } from 'zod/v4'

const minimax = createOpenAI({
  apiKey: process.env.MINIMAX_API_KEY!,
  baseURL: 'https://api.minimax.chat/v1',
})

const base = process.env.BACKEND_URL ?? 'http://localhost:8000'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function api(path: string): Promise<any> {
  const res = await fetch(`${base}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`)
  return res.json()
}

const SYSTEM = `你是 DeepAlpha 投研助手，专注于美股市场分析。

可用工具覆盖：概念股池、实时行情、财务报表（利润表/资产负债表/现金流）、
财务比率、估值、分析师评级与目标价、公司画像、新闻资讯、内幕交易、
市场涨跌榜、板块表现、财报日历。

规则：
- 优先调用工具获取最新数据，不要凭记忆回答行情和财务问题
- 数据以中文呈现，金额单位用 B（十亿）或 M（百万）
- 遇到综合分析需求时可并行调用多个工具`

export async function POST(req: Request) {
  const { messages } = await req.json()

  try {
    const result = await streamText({
      model: minimax.chat('MiniMax-Text-01'),
      system: SYSTEM,
      messages: await convertToModelMessages(messages),
      stopWhen: stepCountIs(8),
      tools: {

        // ── 概念股池 ──────────────────────────────────────────────────────
        search_concept: tool({
          description: '查询美股概念股池，返回该概念下成分股列表（含ETF覆盖数和权重）',
          inputSchema: z.object({
            concept: z.string().describe('概念名称，如 "Technology"'),
            min_etf_count: z.number().int().min(1).default(1),
          }),
          execute: async ({ concept, min_etf_count }) => {
            const res = await fetch(
              `${base}/api/v1/concept/${encodeURIComponent(concept)}?min_etf_count=${min_etf_count}`,
              { cache: 'no-store' }
            )
            if (!res.ok) return `概念 '${concept}' 不存在或暂无数据`
            const stocks: Array<{ symbol: string; etf_count: number; total_weight: number }> = await res.json()
            const lines = stocks.slice(0, 20).map(s =>
              `${s.symbol}: ETF覆盖=${s.etf_count}, 权重=${s.total_weight.toFixed(1)}%`
            )
            return `概念 '${concept}' 共 ${stocks.length} 只成分股（前20）：\n` + lines.join('\n')
          },
        }),

        list_concepts: tool({
          description: '列出所有可用的美股概念板块分类名称及成分股数量',
          inputSchema: z.object({}),
          execute: async () => {
            const list: Array<{ concept: string; concept_name_zh?: string; stock_count: number }> =
              await api('/api/v1/concept/list')
            return list.map(c => `${c.concept_name_zh ?? c.concept}（${c.stock_count}只）`).join('\n')
          },
        }),

        // ── 行情 ─────────────────────────────────────────────────────────
        get_quote: tool({
          description: '获取美股股票实时报价、涨跌幅、市值、PE等',
          inputSchema: z.object({ symbol: z.string().describe('股票代码，如 "NVDA"') }),
          execute: async ({ symbol }) => {
            const q: {
              symbol: string; name?: string; price: number;
              changesPercentage?: number; marketCap?: number; pe?: number
            } = await api(`/api/v1/market/quote/${symbol}`)
            const pct = q.changesPercentage != null ? `${q.changesPercentage.toFixed(2)}%` : 'N/A'
            const cap = q.marketCap ? `$${(q.marketCap / 1e9).toFixed(1)}B` : 'N/A'
            return `${q.symbol} ${q.name ?? ''}: 价格=$${q.price}, 涨跌幅=${pct}, 市值=${cap}, PE=${q.pe ?? 'N/A'}`
          },
        }),

        // ── 财务报表 ──────────────────────────────────────────────────────
        get_income_statement: tool({
          description: '获取公司最新年度利润表（营收、毛利、净利润、EBITDA、EPS）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const stmt: {
              date: string; period: string; revenue?: number; grossProfit?: number;
              netIncome?: number; ebitda?: number; eps?: number; epsDiluted?: number
            } | null = await api(`/api/v1/financial/${s}/income`).catch(() => null)
            if (!stmt) return `暂无 ${s} 的财务数据`
            const f = (v?: number) => v != null ? `$${(v / 1e9).toFixed(2)}B` : 'N/A'
            return `${s} 利润表（${stmt.date} ${stmt.period}）：\n营收=${f(stmt.revenue)}, 毛利=${f(stmt.grossProfit)}, 净利润=${f(stmt.netIncome)}, EBITDA=${f(stmt.ebitda)}, EPS=$${stmt.eps?.toFixed(2) ?? 'N/A'}（稀释$${stmt.epsDiluted?.toFixed(2) ?? 'N/A'}）`
          },
        }),

        get_balance_sheet: tool({
          description: '获取公司最新资产负债表（总资产、负债、净资产、现金、债务）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const bs: {
              date: string; totalAssets?: number; totalLiabilities?: number;
              totalStockholdersEquity?: number; cashAndCashEquivalents?: number;
              totalDebt?: number; netDebt?: number
            } | null = await api(`/api/v1/financial/${s}/balance`).catch(() => null)
            if (!bs) return `暂无 ${s} 的资产负债表数据`
            const f = (v?: number) => v != null ? `$${(v / 1e9).toFixed(2)}B` : 'N/A'
            return `${s} 资产负债表（${bs.date}）：总资产=${f(bs.totalAssets)}, 总负债=${f(bs.totalLiabilities)}, 净资产=${f(bs.totalStockholdersEquity)}, 现金=${f(bs.cashAndCashEquivalents)}, 净债务=${f(bs.netDebt)}`
          },
        }),

        get_cash_flow: tool({
          description: '获取公司最新现金流量表（经营/资本支出/自由现金流）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const cf: {
              date: string; operatingCashFlow?: number;
              capitalExpenditure?: number; freeCashFlow?: number
            } | null = await api(`/api/v1/financial/${s}/cashflow`).catch(() => null)
            if (!cf) return `暂无 ${s} 的现金流数据`
            const f = (v?: number) => v != null ? `$${(v / 1e9).toFixed(2)}B` : 'N/A'
            return `${s} 现金流（${cf.date}）：经营现金流=${f(cf.operatingCashFlow)}, 资本支出=${f(cf.capitalExpenditure)}, 自由现金流=${f(cf.freeCashFlow)}`
          },
        }),

        get_financial_ratios: tool({
          description: '获取公司财务比率（毛利率、净利率、ROE、ROA、流动比率）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const r: {
              date: string; grossProfitMargin?: number; netProfitMargin?: number;
              returnOnEquity?: number; returnOnAssets?: number; currentRatio?: number;
              debtEquityRatio?: number
            } | null = await api(`/api/v1/financial/${s}/ratios`).catch(() => null)
            if (!r) return `暂无 ${s} 的财务比率数据`
            const p = (v?: number) => v != null ? `${(v * 100).toFixed(1)}%` : 'N/A'
            return `${s} 财务比率（${r.date}）：毛利率=${p(r.grossProfitMargin)}, 净利率=${p(r.netProfitMargin)}, ROE=${p(r.returnOnEquity)}, ROA=${p(r.returnOnAssets)}, 流动比率=${r.currentRatio?.toFixed(2) ?? 'N/A'}`
          },
        }),

        get_key_metrics: tool({
          description: '获取公司关键估值指标（PE、PB、EV/EBITDA、FCF收益率）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const m: {
              date: string; peRatio?: number; priceToBook?: number;
              priceToSales?: number; evToEbitda?: number; freeCashFlowPerShare?: number
            } | null = await api(`/api/v1/financial/${s}/metrics`).catch(() => null)
            if (!m) return `暂无 ${s} 的关键指标数据`
            return `${s} 关键指标（${m.date}）：PE=${m.peRatio?.toFixed(1) ?? 'N/A'}, PB=${m.priceToBook?.toFixed(2) ?? 'N/A'}, PS=${m.priceToSales?.toFixed(2) ?? 'N/A'}, EV/EBITDA=${m.evToEbitda?.toFixed(1) ?? 'N/A'}, FCF/股=$${m.freeCashFlowPerShare?.toFixed(2) ?? 'N/A'}`
          },
        }),

        get_valuation: tool({
          description: '获取公司 DCF 内在价值估算与当前股价对比',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const v: { dcf?: number; stockPrice?: number } | null =
              await api(`/api/v1/financial/${s}/valuation`).catch(() => null)
            if (!v) return `暂无 ${s} 的估值数据`
            const disc = v.dcf && v.stockPrice
              ? ((v.stockPrice - v.dcf) / v.dcf * 100).toFixed(1) : null
            return `${s} DCF估值：内在价值=$${v.dcf?.toFixed(2) ?? 'N/A'}, 当前股价=$${v.stockPrice?.toFixed(2) ?? 'N/A'}${disc != null ? `（${+disc > 0 ? '溢价' : '折价'} ${Math.abs(+disc)}%）` : ''}`
          },
        }),

        // ── 分析师 ────────────────────────────────────────────────────────
        get_analyst_ratings: tool({
          description: '获取分析师买入/持有/卖出评级汇总及最新评级',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const ratings: Array<{ ratingRecommendation: string; date: string; analystName?: string }> =
              await api(`/api/v1/analyst/${s}/ratings`).catch(() => [])
            if (!ratings.length) return `暂无 ${s} 的分析师评级`
            const latest = ratings[0]
            return `${s} 分析师评级（共${ratings.length}份）：最新=${latest.ratingRecommendation}（${latest.date}）`
          },
        }),

        get_price_targets: tool({
          description: '获取分析师目标价（最新、平均、最高、最低）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const targets: Array<{ priceTarget?: number; analystCompany?: string; publishedDate?: string }> =
              await api(`/api/v1/analyst/${s}/targets`).catch(() => [])
            if (!targets.length) return `暂无 ${s} 的目标价数据`
            const prices = targets.map(t => t.priceTarget).filter((p): p is number => p != null)
            const avg = prices.length ? (prices.reduce((a, b) => a + b, 0) / prices.length).toFixed(2) : 'N/A'
            const t0 = targets[0]
            return `${s} 目标价（共${targets.length}份）：最新=$${t0.priceTarget?.toFixed(2) ?? 'N/A'}（${t0.analystCompany}，${t0.publishedDate}），均值=$${avg}，最高=$${Math.max(...prices).toFixed(2)}，最低=$${Math.min(...prices).toFixed(2)}`
          },
        }),

        // ── 公司信息 ──────────────────────────────────────────────────────
        get_company_profile: tool({
          description: '获取公司基本信息（行业、板块、员工数、CEO、业务描述）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const p: {
              companyName?: string; sector?: string; industry?: string;
              country?: string; ceo?: string; fullTimeEmployees?: number;
              ipoDate?: string; description?: string
            } = await api(`/api/v1/company/${s}/profile`).catch(() => ({}))
            const desc = p.description ? p.description.slice(0, 250) + '…' : ''
            return `${s} ${p.companyName ?? ''}：板块=${p.sector}，行业=${p.industry}，CEO=${p.ceo}，员工=${p.fullTimeEmployees ?? 'N/A'}，上市日=${p.ipoDate ?? 'N/A'}\n${desc}`
          },
        }),

        get_peers: tool({
          description: '获取股票的同行竞争对手列表',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const peers: string[] = await api(`/api/v1/company/${s}/peers`).catch(() => [])
            if (!peers.length) return `暂无 ${s} 的竞争对手数据`
            return `${s} 同行对标：${peers.join(', ')}`
          },
        }),

        // ── 新闻 ─────────────────────────────────────────────────────────
        get_news: tool({
          description: '获取股票最新新闻资讯（标题、来源、情绪）',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const articles: Array<{
              title: string; site?: string; publishedDate?: string; sentiment?: string
            }> = await api(`/api/v1/news/${s}?limit=8`).catch(() => [])
            if (!articles.length) return `暂无 ${s} 相关新闻`
            return `${s} 最新新闻：\n` + articles.map(a =>
              `• ${a.title} (${a.site ?? '?'}，${a.sentiment ?? '?'})`
            ).join('\n')
          },
        }),

        // ── 内幕交易 ──────────────────────────────────────────────────────
        get_insider_trades: tool({
          description: '获取公司内部人员（高管/董事）最近买卖记录',
          inputSchema: z.object({ symbol: z.string() }),
          execute: async ({ symbol }) => {
            const s = symbol.toUpperCase()
            const trades: Array<{
              transactionDate?: string; reportingName?: string;
              acquisitionOrDisposition?: string; securitiesTransacted?: number; price?: number
            }> = await api(`/api/v1/insider/${s}?limit=10`).catch(() => [])
            if (!trades.length) return `暂无 ${s} 的内幕交易数据`
            return `${s} 内幕交易（最近10笔）：\n` + trades.map(t =>
              `${t.transactionDate} ${t.reportingName}: ${t.acquisitionOrDisposition === 'A' ? '买入' : '卖出'} ${t.securitiesTransacted?.toLocaleString() ?? '?'}股 @ $${t.price?.toFixed(2) ?? '?'}`
            ).join('\n')
          },
        }),

        // ── 市场表现 ──────────────────────────────────────────────────────
        get_market_movers: tool({
          description: '获取今日美股涨幅榜或跌幅榜前10只股票',
          inputSchema: z.object({
            direction: z.enum(['gainers', 'losers']).describe('gainers=涨榜 losers=跌榜'),
          }),
          execute: async ({ direction }) => {
            const movers: Array<{
              symbol: string; name?: string; price?: number; changesPercentage?: number
            }> = await api(`/api/v1/market/movers/${direction}`).catch(() => [])
            if (!movers.length) return `暂无${direction === 'gainers' ? '涨幅' : '跌幅'}榜数据`
            return `今日${direction === 'gainers' ? '涨幅' : '跌幅'}榜：\n` + movers.map(m =>
              `${m.symbol} ${m.name ?? ''}: $${m.price?.toFixed(2) ?? '?'} (${m.changesPercentage?.toFixed(2) ?? '?'}%)`
            ).join('\n')
          },
        }),

        get_sector_performance: tool({
          description: '获取美股各板块今日涨跌幅排行',
          inputSchema: z.object({}),
          execute: async () => {
            const sectors: Array<{ sector: string; changesPercentage?: string }> =
              await api('/api/v1/market/sectors').catch(() => [])
            if (!sectors.length) return '暂无板块表现数据'
            return '板块表现：\n' + sectors.map(s => `${s.sector}: ${s.changesPercentage}`).join('\n')
          },
        }),

        // ── 日历事件 ──────────────────────────────────────────────────────
        get_upcoming_earnings: tool({
          description: '获取未来7天即将发布财报的美股公司列表',
          inputSchema: z.object({}),
          execute: async () => {
            const events: Array<{
              date: string; symbol: string; epsEstimated?: number; time?: string
            }> = await api('/api/v1/calendar/earnings').catch(() => [])
            if (!events.length) return '未来7天暂无财报发布'
            return '即将发布财报（7天内）：\n' + events.slice(0, 15).map(e =>
              `${e.date} ${e.symbol}: EPS预期=${e.epsEstimated ?? 'N/A'}, 时段=${e.time ?? '?'}`
            ).join('\n')
          },
        }),
      },
    })

    return result.toUIMessageStreamResponse()
  } catch (err) {
    console.error('[chat] streamText failed:', err)
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}
