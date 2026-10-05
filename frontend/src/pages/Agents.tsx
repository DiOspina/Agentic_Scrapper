import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatRelativeTime, getStatusColor } from '../utils/helpers'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { Play, Bot, Zap, Brain, FileText, Settings, ArrowRight, Check, X, Loader2 } from 'lucide-react'
import { cn } from '../utils/helpers'
import toast from 'react-hot-toast'

const agentConfigs = {
  scraper: {
    name: 'Web Scraper',
    description: 'Extract structured and unstructured data from websites with JavaScript rendering support',
    icon: Zap,
    color: 'primary',
    capabilities: [
      'Dynamic content scraping (Playwright)',
      'JavaScript rendering',
      'Table extraction',
      'Link crawling',
      'Structured data (JSON-LD, microdata)',
      'Screenshot capture',
      'CSS selector extraction',
      'Session management & retries',
    ],
    defaultConfig: {
      max_pages: 10,
      max_depth: 2,
      follow_links: true,
      same_domain_only: true,
      wait_timeout: 10000,
      extract_tables: true,
      extract_images: true,
      extract_structured_data: true,
    },
  },
  analyst: {
    name: 'Data Analyst (RAG)',
    description: 'Process documents with embeddings for key metrics extraction, pattern detection, and insights',
    icon: Brain,
    color: 'success',
    capabilities: [
      'Document summarization',
      'Key metrics extraction',
      'Pattern detection',
      'Sentiment analysis',
      'Entity extraction',
      'Comparative analysis',
      'Trend analysis',
      'Anomaly detection',
      'Custom queries with RAG',
    ],
    defaultConfig: {
      analysis_types: ['summarization', 'key_metrics', 'pattern_detection', 'anomaly_detection'],
      chunk_size: 1000,
      chunk_overlap: 200,
      top_k: 5,
      similarity_threshold: 0.7,
    },
  },
  synthesizer: {
    name: 'Report Synthesizer',
    description: 'Generate executive reports in JSON, Markdown, and HTML from analysis results',
    icon: FileText,
    color: 'warning',
    capabilities: [
      'Executive summaries',
      'Detailed analysis reports',
      'Technical reports',
      'JSON output',
      'Markdown output',
      'HTML output',
      'Custom templates',
      'Charts & visualizations',
    ],
    defaultConfig: {
      report_type: 'executive_summary',
      formats: ['json', 'markdown'],
      include_charts: true,
      include_raw_data: false,
      max_length: 10000,
    },
  },
}

type AgentKey = keyof typeof agentConfigs

export function Agents() {
  const queryClient = useQueryClient()
  const [selectedAgent, setSelectedAgent] = useState<AgentKey | null>(null)
  const [showRunModal, setShowRunModal] = useState(false)
  const [runConfig, setRunConfig] = useState<any>({})
  const [activeTab, setActiveTab] = useState<'overview' | 'run' | 'logs'>('overview')

  const { data: agentStatus, isLoading } = useQuery({
    queryKey: ['agents', 'status'],
    queryFn: () => api.getAgentsStatus(),
    refetchInterval: 30000,
  })

  const runAgentMutation = useMutation({
    mutationFn: ({ agent, data }: { agent: string; data: any }) => {
      switch (agent) {
        case 'scraper':
          return api.scrape(data)
        case 'analyst':
          return api.analyze(data)
        case 'synthesizer':
          return api.synthesize(data)
      }
    },
    onSuccess: (result) => {
      toast.success('Agent execution completed')
      setShowRunModal(false)
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Execution failed')
    },
  })

  const handleRunAgent = (agent: AgentKey) => {
    setSelectedAgent(agent)
    setRunConfig({ ...agentConfigs[agent].defaultConfig })
    setShowRunModal(true)
    setActiveTab('run')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Agents</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Manage and run AI agents for scraping, analysis, and synthesis</p>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        {(Object.entries(agentConfigs) as [AgentKey, typeof agentConfigs.scraper][]).map(([key, config]) => {
          const Icon = config.icon
          const status = agentStatus?.agents?.find((a: any) => a.name === key)
          return (
            <Card key={key} className="relative overflow-hidden transition-all hover:shadow-lg">
              <div className="absolute top-0 left-0 right-0 h-1" style={{ background: `var(--color-${config.color}-600)` }} />
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-4">
                  <div className={cn('p-3 rounded-xl', `bg-${config.color}-100 text-${config.color}-600 dark:bg-${config.color}-900/30 dark:text-${config.color}-400`)}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <Badge variant={status?.status === 'available' ? 'success' : 'neutral'} dot>
                    {status?.status || 'unknown'}
                  </Badge>
                </div>
                <h3 className="text-lg font-semibold text-dark-900 dark:text-white mb-1">{config.name}</h3>
                <p className="text-sm text-dark-500 dark:text-dark-400 mb-4">{config.description}</p>
                
                <div className="space-y-2 mb-6">
                  {config.capabilities.slice(0, 4).map((cap) => (
                    <div key={cap} className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400">
                      <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {cap}
                    </div>
                  ))}
                  {config.capabilities.length > 4 && (
                    <button
                      onClick={() => { setSelectedAgent(key); setActiveTab('overview'); }}
                      className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 flex items-center gap-1"
                    >
                      +{config.capabilities.length - 4} more
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    onClick={() => handleRunAgent(key)}
                    disabled={runAgentMutation.isPending}
                    className="flex-1"
                    leftIcon={<Play className="w-4 h-4" />}
                  >
                    Run Agent
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => { setSelectedAgent(key); setActiveTab('overview'); }}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Pipeline Overview */}
      <Card>
        <CardTitle title="Multi-Agent Pipeline" subtitle="Chain agents together for complex workflows" />
        <CardContent>
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4 flex-wrap">
              {(['scraper', 'analyst', 'synthesizer'] as AgentKey[]).map((key, index) => (
                <div key={key} className="flex items-center gap-2">
                  <div className={cn('p-2 rounded-lg', `bg-${agentConfigs[key].color}-100 text-${agentConfigs[key].color}-600 dark:bg-${agentConfigs[key].color}-900/30 dark:text-${agentConfigs[key].color}-400`)}>
                    <agentConfigs[key].icon className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-dark-900 dark:text-white">{agentConfigs[key].name}</span>
                  {index < 2 && (
                    <ArrowRight className="w-5 h-5 text-dark-400" />
                  )}
                </div>
              ))}
            </div>
            <Button variant="primary" leftIcon={<Play className="w-4 h-4" />}>
              Run Full Pipeline
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Run Agent Modal */}
      <Modal
        isOpen={showRunModal}
        onClose={() => { setShowRunModal(false); setSelectedAgent(null); }}
        title={`Run ${selectedAgent ? agentConfigs[selectedAgent].name : 'Agent'}`}
        size="lg"
      >
        {selectedAgent && (
          <AgentRunForm
            agent={selectedAgent}
            config={runConfig}
            onConfigChange={setRunConfig}
            onSubmit={(data) => runAgentMutation.mutate({ agent: selectedAgent, data })}
            onClose={() => { setShowRunModal(false); setSelectedAgent(null); }}
            isLoading={runAgentMutation.isPending}
          />
        )}
      </Modal>
    </div>
  )
}

function AgentRunForm({ agent, config, onConfigChange, onSubmit, onClose, isLoading }: any) {
  const [formData, setFormData] = useState(config)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const configFields = {
    scraper: (
      <div className="grid gap-4">
        <Textarea
          label="URLs (one per line)"
          value={formData.urls?.join('\n') || ''}
          onChange={(e) => setFormData({ ...formData, urls: e.target.value.split('\n').filter(Boolean) })}
          placeholder="https://example.com\nhttps://example.org"
          rows={4}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Max Pages"
            type="number"
            value={formData.max_pages}
            onChange={(e) => setFormData({ ...formData, max_pages: parseInt(e.target.value) })}
          />
          <Input
            label="Max Depth"
            type="number"
            value={formData.max_depth}
            onChange={(e) => setFormData({ ...formData, max_depth: parseInt(e.target.value) })}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.follow_links}
              onChange={(e) => setFormData({ ...formData, follow_links: e.target.checked })}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm">Follow Links</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.same_domain_only}
              onChange={(e) => setFormData({ ...formData, same_domain_only: e.target.checked })}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm">Same Domain Only</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.extract_tables}
              onChange={(e) => setFormData({ ...formData, extract_tables: e.target.checked })}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm">Extract Tables</span>
          </label>
        </div>
      </div>
    ),
    analyst: (
      <div className="grid gap-4">
        <Textarea
          label="Queries (one per line)"
          value={formData.queries?.join('\n') || ''}
          onChange={(e) => setFormData({ ...formData, queries: e.target.value.split('\n').filter(Boolean) })}
          placeholder="What are the key metrics?\nAny anomalies detected?\nSummarize the findings"
          rows={4}
        />
        <div>
          <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">Analysis Types</label>
          <div className="flex flex-wrap gap-2">
            {['summarization', 'key_metrics', 'pattern_detection', 'sentiment_analysis', 'entity_extraction', 'anomaly_detection'].map((type) => (
              <label key={type} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.analysis_types?.includes(type)}
                  onChange={(e) => setFormData({
                    ...formData,
                    analysis_types: e.target.checked
                      ? [...(formData.analysis_types || []), type]
                      : (formData.analysis_types || []).filter((t: string) => t !== type),
                  })}
                  className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Chunk Size"
            type="number"
            value={formData.chunk_size}
            onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) })}
          />
          <Input
            label="Top K Results"
            type="number"
            value={formData.top_k}
            onChange={(e) => setFormData({ ...formData, top_k: parseInt(e.target.value) })}
          />
        </div>
      </div>
    ),
    synthesizer: (
      <div className="grid gap-4">
        <Input
          label="Report Title"
          value={formData.title || ''}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          placeholder="Executive Analysis Report"
        />
        <Select
          label="Report Type"
          value={formData.report_type}
          onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
          options={[
            { value: 'executive_summary', label: 'Executive Summary' },
            { value: 'detailed_analysis', label: 'Detailed Analysis' },
            { value: 'technical_report', label: 'Technical Report' },
          ]}
        />
        <div>
          <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-2">Output Formats</label>
          <div className="flex flex-wrap gap-2">
            {['json', 'markdown', 'html'].map((fmt) => (
              <label key={fmt} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.formats?.includes(fmt)}
                  onChange={(e) => setFormData({
                    ...formData,
                    formats: e.target.checked
                      ? [...(formData.formats || []), fmt]
                      : (formData.formats || []).filter((f: string) => f !== fmt),
                  })}
                  className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm capitalize">{fmt}</span>
              </label>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.include_charts}
            onChange={(e) => setFormData({ ...formData, include_charts: e.target.checked })}
            className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm">Include Charts</span>
        </label>
      </div>
    ),
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <p className="text-sm text-dark-600 dark:text-dark-400">
        Configure the agent parameters and click Run to execute.
      </p>

      {configFields[agent as keyof typeof configFields]}

      <div className="flex justify-end gap-3 pt-4 border-t border-dark-200 dark:border-dark-700">
        <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
        <Button type="submit" loading={isLoading}>
          {isLoading ? 'Running...' : 'Run Agent'}
        </Button>
      </div>
    </form>
  )
}