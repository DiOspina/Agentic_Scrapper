import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { Dashboard } from './pages/Dashboard'
import { Executions } from './pages/Executions'
import { Documents } from './pages/Documents'
import { Workflows } from './pages/Workflows'
import { Agents } from './pages/Agents'
import { Chat } from './pages/Chat'
import { Analytics } from './pages/Analytics'
import { Settings } from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="executions" element={<Executions />} />
        <Route path="documents" element={<Documents />} />
        <Route path="workflows" element={<Workflows />} />
        <Route path="agents" element={<Agents />} />
        <Route path="chat" element={<Chat />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App