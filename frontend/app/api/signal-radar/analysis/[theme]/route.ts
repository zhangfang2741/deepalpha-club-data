import { NextRequest, NextResponse } from 'next/server'

// 允许最长 5 分钟（Next.js App Router 默认 30s，这里显式延长）
export const maxDuration = 300

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000'

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ theme: string }> }
) {
  const { theme } = await params
  const searchParams = req.nextUrl.searchParams
  const query = searchParams.toString()
  const url = `${BACKEND}/api/v1/signal-radar/theme/${encodeURIComponent(theme)}/analysis${query ? '?' + query : ''}`

  try {
    const res = await fetch(url, {
      cache: 'no-store',
      signal: AbortSignal.timeout(4 * 60 * 1000), // 4 分钟
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ error: message }, { status: 502 })
  }
}
