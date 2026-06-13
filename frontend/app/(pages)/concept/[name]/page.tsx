import { ConceptStocksClient } from '@/components/concept/ConceptStocksClient'

interface PageProps {
  params: Promise<{ name: string }>
}

export default async function ConceptDetailPage({ params }: PageProps) {
  const { name } = await params
  return <ConceptStocksClient conceptName={decodeURIComponent(name)} />
}
