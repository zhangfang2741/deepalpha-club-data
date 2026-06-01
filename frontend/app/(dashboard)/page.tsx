import { redirect } from 'next/navigation'
import { getConceptList } from '@/lib/api'

export default async function DashboardPage() {
  try {
    const concepts = await getConceptList()
    if (concepts.length > 0) {
      redirect(`/concept/${encodeURIComponent(concepts[0].concept)}`)
    }
  } catch {
    // 后端不可用时降级显示
  }
  return (
    <div className="flex h-64 items-center justify-center text-muted-foreground text-sm">
      暂无概念数据，请确认后端服务已启动（http://localhost:8000）
    </div>
  )
}
