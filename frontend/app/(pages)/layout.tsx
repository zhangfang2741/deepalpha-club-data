import Link from 'next/link'

export default function PagesLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="flex h-screen flex-col"
      style={{ background: 'rgb(246,248,252)', color: 'rgb(15,23,42)' }}
    >
      {/* 顶栏（与 AppShell 保持一致） */}
      <header
        className="flex h-12 shrink-0 items-center px-5 gap-4"
        style={{
          background: 'rgb(22,119,255)',
          borderBottom: 'none',
          boxShadow: '0 2px 8px rgba(22,119,255,0.30)',
        }}
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <div
            className="h-7 w-7 rounded-lg flex items-center justify-center text-[11px] font-bold"
            style={{
              background: 'linear-gradient(135deg, rgb(22,119,255), rgb(0,210,255))',
              color: 'white',
              boxShadow: '0 2px 12px rgba(22,119,255,0.4)',
            }}
          >
            Dα
          </div>
          <span
            className="text-sm font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-bricolage)', color: 'rgb(255,255,255)' }}
          >
            DeepAlpha
          </span>
        </Link>

        <div className="h-4 w-px mx-1" style={{ background: 'rgba(255,255,255,0.30)' }} />

        {/* 导航 */}
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className="px-3 py-1.5 text-xs rounded-lg transition-all duration-200"
            style={{ color: 'rgba(255,255,255,0.85)' }}
          >
            研究助手
          </Link>
          <span
            className="px-3 py-1.5 text-xs rounded-lg font-medium"
            style={{
              color: 'rgb(22,119,255)',
              background: 'rgb(255,255,255)',
              boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
            }}
          >
            信号雷达
          </span>
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{
              background: 'rgb(0,200,130)',
              boxShadow: '0 0 8px rgba(0,200,130,0.6)',
            }}
          />
          <span className="text-[10px] font-medium" style={{ color: 'rgba(255,255,255,0.85)' }}>
            实时数据
          </span>
        </div>
      </header>

      {/* 页面内容 */}
      <main className="flex-1 overflow-auto" style={{ background: 'rgb(246,248,252)' }}>
        {children}
      </main>
    </div>
  )
}