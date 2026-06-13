'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getRadarLeaderboard, getRadarTrend, getThemeSignals, getThemeAnalysis } from '@/lib/api'
import type { DailyThemeScore } from '@/lib/types'
import type { ThemeSignal, ThemeAnalysis } from '@/lib/api'

const WINDOWS = ['7d', '30d', '90d', '1y', '3y', 'all'] as const
type Window = typeof WINDOWS[number]

const CATEGORIES = [
  { value: 'all', label: '全部' },
  { value: 'tech_concept', label: '技术概念' },
  { value: 'infra_component', label: '基础设施' },
  { value: 'engineering_concept', label: '工程概念' },
] as const

const CATEGORY_COLORS: Record<string, string> = {
  tech_concept: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  infra_component: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  engineering_concept: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
}

const CATEGORY_LABELS: Record<string, string> = {
  tech_concept: '技术概念',
  infra_component: '基础设施',
  engineering_concept: '工程概念',
}

const SOURCE_TYPE_CONFIG: Record<string, { label: string; weight: number; color: string; bg: string }> = {
  earnings_call: { label: '财报电话会', weight: 3, color: 'rgb(255,185,0)', bg: 'rgba(255,185,0,0.10)' },
  capex:        { label: '资本支出',   weight: 4, color: 'rgb(22,119,255)', bg: 'rgba(0,0,0,0.08)' },
  form_d:       { label: 'Form D', weight: 2, color: 'rgb(0,210,255)', bg: 'rgba(0,210,255,0.10)' },
  job_posting:  { label: '招聘帖',    weight: 1, color: 'rgb(0,220,130)', bg: 'rgba(0,220,130,0.10)' },
}

function today() {
  return new Date().toISOString().slice(0, 10)
}

function daysBack(n: number) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

function windowToFrom(w: Window): string {
  const map: Record<Window, number> = { '7d': 7, '30d': 30, '90d': 90, '1y': 365, '3y': 1095, all: 1095 }
  return daysBack(map[w])
}

function MarkdownTable({ content }: { content: string }) {
  if (!content.trim()) return null
  const lines = content.trim().split('\n')
  const tableLines = lines.filter(l => l.trim().startsWith('|'))
  if (tableLines.length < 2) {
    return (
      <pre className="whitespace-pre-wrap break-words text-[11px] p-3 rounded-lg" style={{ color: 'rgb(51,65,85)', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)' }}>
        {content}
      </pre>
    )
  }
  const headers = tableLines[0].split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(h => h.trim())
  const rows = tableLines.slice(2).map(row => row.split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(c => c.trim()))
  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid rgba(0,0,0,0.06)' }}>
      <table className="w-full text-xs">
        <thead>
          <tr style={{ background: 'rgba(0,0,0,0.06)' }}>
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2 text-left font-medium" style={{ color: 'rgb(22,119,255)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-t" style={{ borderColor: 'rgba(0,0,0,0.04)' }}>
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2" style={{ color: 'rgb(30,41,59)' }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function RadarPage() {
  const [date, setDate] = useState(today())
  const [window, setWindow] = useState<Window>('30d')
  const [category, setCategory] = useState('all')
  const [leaderboard, setLeaderboard] = useState<DailyThemeScore[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null)
  const [trendData, setTrendData] = useState<DailyThemeScore[]>([])
  const [trendLoading, setTrendLoading] = useState(false)
  const [signals, setSignals] = useState<ThemeSignal[]>([])
  const [signalsLoading, setSignalsLoading] = useState(false)
  const [themeAnalysis, setThemeAnalysis] = useState<ThemeAnalysis | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisStarted, setAnalysisStarted] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  const loadLeaderboard = useCallback(async () => {
    setLoading(true)
    try {
      // 不传 date → API 自动取最新有数据的日期
      const data = await getRadarLeaderboard(undefined, window, category, 50)
      setLeaderboard(data)
      if (data.length > 0) {
        // 用实际查询到的日期更新时光机
        setDate(data[0].score_date)
        if (!selectedTheme) {
          setSelectedTheme(data[0].theme_name)
        }
      }
    } finally {
      setLoading(false)
    }
  }, [window, category, selectedTheme])

  useEffect(() => { loadLeaderboard() }, [loadLeaderboard])

  useEffect(() => {
    if (!selectedTheme) return
    setTrendLoading(true)
    const from = windowToFrom(window)
    getRadarTrend(selectedTheme, from, date)
      .then(setTrendData)
      .finally(() => setTrendLoading(false))
  }, [selectedTheme, window, date])

  useEffect(() => {
    if (!selectedTheme) { setSignals([]); return }
    setSignalsLoading(true)
    // 切换主题时重置分析状态
    setThemeAnalysis(null)
    setAnalysisError(null)
    setAnalysisStarted(false)
    getThemeSignals(selectedTheme)
      .then(setSignals)
      .finally(() => setSignalsLoading(false))
  }, [selectedTheme])

  async function runThemeAnalysis() {
    if (!selectedTheme) return
    setAnalysisLoading(true)
    setThemeAnalysis(null)
    setAnalysisError(null)
    try {
      const data = await getThemeAnalysis(selectedTheme)
      // 检查是否所有维度都为空（解析失败但 API 成功的情况）
      const hasContent = Object.values(data).some(v => v?.trim())
      if (!hasContent) {
        setAnalysisError('AI 返回了空内容，请稍后重试')
      } else {
        setThemeAnalysis(data)
        setAnalysisStarted(true)
      }
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : String(err))
    } finally {
      setAnalysisLoading(false)
    }
  }

  const maxScore = leaderboard.length > 0 ? leaderboard[0].cumulative_score : 1

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1
            className="text-xl font-bold tracking-tight"
            style={{ color: 'rgb(15,23,42)', fontFamily: 'var(--font-bricolage)' }}
          >
            信号趋势雷达
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'rgb(100,116,139)' }}>
            从 SEC 8-K / Capex / Form D / Greenhouse 招聘中提取技术主题，追踪结构性趋势
          </p>
        </div>

        {/* 时光机 */}
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'rgb(100,116,139)' }}>时光机</span>
          <input
            type="date"
            value={date}
            max={today()}
            onChange={e => setDate(e.target.value)}
            className="text-sm rounded-lg px-2.5 py-1.5 focus:outline-none transition-all duration-200"
            style={{
              background: 'rgb(246,248,252)',
              border: '1px solid rgba(0,0,0,0.12)',
              color: 'rgb(15,23,42)',
              fontFamily: 'var(--font-ibm-mono)',
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}
          />
        </div>
      </div>

      {/* 控制栏 */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* 时间窗口 */}
        <div
          className="flex items-center gap-1 rounded-lg p-1"
          style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.10)' }}
        >
          {WINDOWS.map(w => (
            <button
              key={w}
              onClick={() => setWindow(w)}
              className="px-3 py-1 text-xs rounded-md transition-all duration-200"
              style={
                window === w
                  ? { background: 'rgba(22,119,255,0.2)', color: 'rgb(22,119,255)', fontWeight: 600 }
                  : { color: 'rgb(100,116,139)' }
              }
            >
              {w.toUpperCase()}
            </button>
          ))}
        </div>

        {/* 类别 */}
        <div
          className="flex items-center gap-1 rounded-lg p-1"
          style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.10)' }}
        >
          {CATEGORIES.map(c => (
            <button
              key={c.value}
              onClick={() => setCategory(c.value)}
              className="px-3 py-1 text-xs rounded-md transition-all duration-200"
              style={
                category === c.value
                  ? { background: 'rgba(22,119,255,0.2)', color: 'rgb(22,119,255)', fontWeight: 600 }
                  : { color: 'rgb(100,116,139)' }
              }
            >
              {c.label}
            </button>
          ))}
        </div>

        {loading && (
          <span className="text-xs animate-pulse" style={{ color: 'rgb(22,119,255)' }}>
            加载中...
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* 排行榜 */}
        <div className="lg:col-span-2 flex flex-col gap-2">
          <h2 className="text-xs font-medium uppercase tracking-wider" style={{ color: 'rgb(100,116,139)' }}>
            排行榜
          </h2>
          <div
            className="rounded-xl overflow-hidden"
            style={{ border: '1px solid rgba(0,0,0,0.08)', background: 'rgb(246,248,252)' }}
          >
            {leaderboard.length === 0 && !loading && (
              <div
                className="flex items-center justify-center h-40 text-sm"
                style={{ color: 'rgb(100,116,139)' }}
              >
                暂无数据，请先运行 signal_radar pipeline
              </div>
            )}
            {leaderboard.map((item, idx) => {
              const barWidth = maxScore > 0 ? (item.cumulative_score / maxScore) * 100 : 0
              const isSelected = selectedTheme === item.theme_name
              return (
                <button
                  key={item.theme_name}
                  onClick={() => setSelectedTheme(item.theme_name)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left transition-all duration-200"
                  style={{
                    borderBottom: '1px solid rgba(0,0,0,0.04)',
                    background: isSelected ? 'rgba(0,0,0,0.04)' : 'transparent',
                  }}
                >
                  <span
                    className="text-sm font-mono w-5 text-center shrink-0"
                    style={{ color: idx < 3 ? 'rgb(255,185,0)' : 'rgb(100,116,139)', fontWeight: idx < 3 ? 700 : 400 }}
                  >
                    {idx + 1}
                  </span>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-sm font-medium truncate"
                        style={{ color: 'rgb(15,23,42)' }}
                      >
                        {item.theme_name}
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded-full border shrink-0 ${CATEGORY_COLORS[item.category]}`}
                      >
                        {CATEGORY_LABELS[item.category]}
                      </span>
                    </div>
                    <div
                      className="mt-1.5 h-1 rounded-full overflow-hidden"
                      style={{ background: 'rgba(22,119,255,0.1)' }}
                    >
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${barWidth}%`,
                          background: 'linear-gradient(90deg, rgb(22,119,255), rgb(0,210,255))',
                        }}
                      />
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>
                        今日 {item.final_score.toFixed(1)} · 动量 {item.momentum.toFixed(2)}x
                      </span>
                      <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>
                        累计 {item.cumulative_score.toFixed(0)}
                      </span>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* 趋势图 */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium uppercase tracking-wider" style={{ color: 'rgb(100,116,139)' }}>
              趋势曲线
              {selectedTheme && (
                <span className="ml-2 normal-case font-semibold" style={{ color: 'rgb(22,119,255)' }}>
                  {selectedTheme}
                </span>
              )}
            </h2>
            {trendLoading && (
              <span className="text-xs animate-pulse" style={{ color: 'rgb(22,119,255)' }}>加载中...</span>
            )}
          </div>

          <div
            className="rounded-xl p-4 h-72"
            style={{ border: '1px solid rgba(0,0,0,0.08)', background: 'rgb(246,248,252)' }}
          >
            {trendData.length === 0 ? (
              <div
                className="flex items-center justify-center h-full text-sm"
                style={{ color: 'rgb(100,116,139)' }}
              >
                {selectedTheme ? '该主题暂无历史数据' : '从左侧选择主题查看趋势'}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
                  <XAxis
                    dataKey="score_date"
                    tick={{ fontSize: 11, fill: 'rgb(100,116,139)' }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={d => d.slice(5)}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: 'rgb(100,116,139)' }}
                    tickLine={false}
                    axisLine={false}
                    width={40}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgb(255,255,255)',
                      border: '1px solid rgba(0,0,0,0.12)',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: 'rgb(15,23,42)',
                      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
                    }}
                    formatter={(value: unknown, name: unknown) => [
                      typeof value === 'number' ? value.toFixed(2) : String(value),
                      String(name) === 'final_score' ? '今日得分' : '累计得分',
                    ]}
                  />
                  <Legend
                    formatter={v => v === 'final_score' ? '今日得分' : '累计得分'}
                    wrapperStyle={{ fontSize: '12px', color: 'rgb(100,116,139)' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="final_score"
                    stroke="rgb(22,119,255)"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: 'rgb(22,119,255)' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="cumulative_score"
                    stroke="rgb(0,210,255)"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="4 2"
                    activeDot={{ r: 3, fill: 'rgb(0,210,255)' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* 信号明细 */}
          {selectedTheme && (() => {
            const latest = trendData[trendData.length - 1]
            const grouped = signals.reduce<Record<string, ThemeSignal[]>>((acc, s) => {
              if (!acc[s.source_type]) acc[s.source_type] = []
              acc[s.source_type].push(s)
              return acc
            }, {})

            return (
              <div className="flex flex-col gap-4">
                {/* 信号明细面板 */}
                <div
                  className="rounded-xl p-4"
                  style={{ border: '1px solid rgba(0,0,0,0.08)', background: 'rgb(246,248,252)' }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-medium uppercase tracking-wider" style={{ color: 'rgb(100,116,139)' }}>
                      信号明细
                   </h3>
                    {signalsLoading && (
                      <span className="text-xs animate-pulse" style={{ color: 'rgb(22,119,255)' }}>加载中...</span>
                    )}
                 </div>

                  {signals.length === 0 && !signalsLoading ? (
                    <div className="text-sm py-6 text-center" style={{ color: 'rgb(100,116,139)' }}>
                     暂无信号明细
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      {Object.entries(grouped).map(([src, srcSignals]) => {
                        const cfg = SOURCE_TYPE_CONFIG[src]
                        return (
                          <div key={src}>
                            <div className="flex items-center gap-2 mb-1.5">
                              <span
                                className="text-[10px] px-2 py-0.5 rounded border"
                                style={{ color: cfg?.color, borderColor: cfg?.color + '40', background: cfg?.bg }}
                              >
                                {cfg?.label ?? src}
                              </span>
                              <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>
                                ×{cfg?.weight ?? 1}权重 · {srcSignals.length}条
                              </span>
                            </div>
                            <div className="flex flex-col gap-1.5">
                              {srcSignals.slice(0, 5).map((s, i) => (
                                <div
                                  key={i}
                                  className="flex items-start gap-2 p-2 rounded-lg text-xs"
                                  style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.04)' }}
                                >
                                  <span
                                    className="shrink-0 font-mono font-semibold text-[10px] px-1.5 py-0.5 rounded"
                                    style={{ color: 'rgb(22,119,255)', background: 'rgba(0,0,0,0.06)' }}
                                  >
                                    {s.ticker}
                                  </span>
                                  <div className="flex-1 min-w-0">
                                    <p
                                      className="leading-relaxed line-clamp-2"
                                      style={{ color: 'rgb(51,65,85)' }}
                                    >
                                      {s.text_snippet.length > 200
                                        ? s.text_snippet.slice(0, 200) + '...'
                                        : s.text_snippet}
                                    </p>
                                    <div className="flex items-center gap-2 mt-1">
                                     <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>
                                        {s.signal_date}
                                      </span>
                                      <a
                                        href={s.sec_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[10px] underline"
                                        style={{ color: 'rgb(22,119,255)' }}
                                      >
                                        SEC 原文 →
                                      </a>
                                     <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>
                                        置信 {s.confidence.toFixed(2)}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                              {srcSignals.length > 5 && (
                                <span className="text-[10px] text-center py-1" style={{ color: 'rgb(100,116,139)' }}>
                                  还有 {srcSignals.length - 5} 条...
                                </span>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>

                {/* AI 深度分析 */}
                <div
                  className="rounded-xl p-4"
                  style={{ border: '1px solid rgba(0,0,0,0.08)', background: 'rgb(246,248,252)' }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="text-xs font-medium uppercase tracking-wider" style={{ color: 'rgb(100,116,139)' }}>
                        AI 深度分析
                      </h3>
                      <p className="text-[10px] mt-0.5" style={{ color: 'rgb(100,116,139)' }}>
                        核心产品 / 企业定位 / 竞争格局 / 供应链 / 生态位
                      </p>
                    </div>
                    {!themeAnalysis && !analysisLoading && (
                      <button
                        onClick={runThemeAnalysis}
                        className="px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200"
                        style={{
                          background: 'rgba(22,119,255,0.15)',
                          border: '1px solid rgba(22,119,255,0.30)',
                          color: 'rgb(22,119,255)',
                        }}
                      >
                        {analysisError ? '重试 →' : '开始分析 →'}
                      </button>
                    )}
                    {analysisLoading && (
                      <span className="text-xs animate-pulse" style={{ color: 'rgb(22,119,255)' }}>
                        分析中（约 30-60 秒）...
                      </span>
                    )}
                  </div>

                  {analysisError && (
                    <div
                      className="rounded-lg p-3 text-xs"
                      style={{ background: 'rgba(255,80,80,0.08)', border: '1px solid rgba(255,80,80,0.20)', color: 'rgb(255,120,120)' }}
                    >
                      分析失败：{analysisError}
                    </div>
                  )}

                  {themeAnalysis && (() => {
                    const sections = [
                      { key: 'products', label: '维度一：核心产品' },
                      { key: 'position', label: '维度二：企业定位' },
                      { key: 'competition', label: '维度三：竞争格局' },
                      { key: 'supply_chain', label: '维度四：供应链关系' },
                      { key: 'ecosystem', label: '维度五：生态位' },
                    ] as const
                    return (
                      <div className="flex flex-col gap-3">
                        {sections.map(({ key, label }) => {
                          const content = themeAnalysis[key]
                          if (!content?.trim()) return null
                          return (
                            <div key={key}>
                              <div className="text-[10px] font-semibold mb-1.5" style={{ color: 'rgb(22,119,255)' }}>
                                {label}
                              </div>
                              <MarkdownTable content={content} />
                            </div>
                          )
                        })}
                      </div>
                    )
                  })()}
                </div>

                {/* 动量说明卡片 */}
                {latest && (
                  <div
                    className="rounded-xl p-4"
                    style={{ border: '1px solid rgba(0,0,0,0.08)', background: 'rgb(246,248,252)' }}
                  >
                    <h3 className="text-xs font-medium uppercase tracking-wider mb-3" style={{ color: 'rgb(100,116,139)' }}>
                      评分说明
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                      {Object.entries(grouped).map(([src]) => {
                        const cfg = SOURCE_TYPE_CONFIG[src]
                        return cfg ? (
                          <div key={src} className="flex flex-col gap-0.5">
                            <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>{cfg.label}</span>
                            <span className="text-sm font-semibold" style={{ color: cfg.color }}>
                              ×{cfg.weight}
                            </span>
                          </div>
                        ) : null
                      })}
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>参与公司</span>
                        <span className="text-sm font-semibold" style={{ color: 'rgb(15,23,42)' }}>
                          {latest.company_count}
                        </span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[10px]" style={{ color: 'rgb(100,116,139)' }}>动量</span>
                        <span className="text-sm font-semibold" style={{ color: 'rgb(255,185,0)' }}>
                          {latest.momentum.toFixed(2)}x
                        </span>
                      </div>
                    </div>
                    <div
                      className="rounded-lg p-3 text-xs leading-relaxed"
                      style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)' }}
                    >
                      <span style={{ color: 'rgb(15,23,42)' }}>公式：</span>
                      <span style={{ color: 'rgb(22,119,255)' }}>最终分 = 加权基础分 × min(动量, 3.0)</span>
                      <br />
                      <span style={{ color: 'rgb(15,23,42)' }}>动量 = 今日基础分 ÷ 过去7天平均基础分</span>
                      <br />
                      <span style={{ color: 'rgb(100,116,139)' }}>
                        权重：资本支出 ×4 · 财报电话会 ×3 · Form D ×2 · 招聘帖 ×1
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      </div>
    </div>
  )
}
