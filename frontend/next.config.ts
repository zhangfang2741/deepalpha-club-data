import type { NextConfig } from 'next'

// Next.js 16 自动加载项目目录 .env，但本项目的 .env 在父目录
// 通过环境变量注入（dev 时由 next.config.ts 的插件注入）
// 注：运行时直接 export MINIMAX_API_KEY=xxx 也可覆盖
const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${BACKEND}/api/v1/:path*`,
      },
    ]
  },
}

export default nextConfig
