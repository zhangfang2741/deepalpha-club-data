import type { Metadata } from 'next'
import { Bricolage_Grotesque, Figtree, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'

const bricolage = Bricolage_Grotesque({
  subsets: ['latin'],
  variable: '--font-bricolage',
  display: 'swap',
  weight: ['400', '500', '600', '700', '800'],
})

const figtree = Figtree({
  subsets: ['latin'],
  variable: '--font-figtree',
  display: 'swap',
  weight: ['300', '400', '500', '600'],
})

const ibmMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-ibm-mono',
  display: 'swap',
  weight: ['400', '500', '600'],
})

export const metadata: Metadata = {
  title: 'DeepAlpha — 投研平台',
  description: '美股概念股数据分析平台',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${bricolage.variable} ${figtree.variable} ${ibmMono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
