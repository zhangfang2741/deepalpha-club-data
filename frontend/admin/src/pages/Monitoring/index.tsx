export default function Monitoring() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">DeepAlpha 统一监控中心</h1>
      <div className="grid grid-cols-3 gap-4">
        <ServiceCard name="Airflow" port={8080} />
        <ServiceCard name="Kafka UI" port={8090} />
        <ServiceCard name="Kibana" port={5601} />
        <ServiceCard name="Grafana" port={3000} />
        <ServiceCard name="Prometheus" port={9090} />
        <ServiceCard name="Data API" port={8000} />
      </div>
    </div>
  )
}

function ServiceCard({ name, port }: { name: string; port: number }) {
  return (
    <a
      href={`http://localhost:${port}`}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-4 border rounded-lg hover:bg-gray-50 transition-colors"
    >
      <h3 className="font-semibold">{name}</h3>
      <p className="text-sm text-gray-500">localhost:{port}</p>
    </a>
  )
}
