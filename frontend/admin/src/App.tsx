import { Routes, Route, Navigate } from 'react-router-dom'
import Monitoring from './pages/Monitoring'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/monitoring" replace />} />
      <Route path="/monitoring" element={<Monitoring />} />
    </Routes>
  )
}
