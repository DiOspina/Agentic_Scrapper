import { useState } from 'react'
import { useAppStore } from '../stores/useAppStore'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Textarea } from '../components/ui/Textarea'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { User, Shield, Bell, Database, Globe, Key, Palette, Moon, Sun, Save, Loader2, TestTube, Trash2 } from 'lucide-react'
import { cn } from '../utils/helpers'
import toast from 'react-hot-toast'

const THEME_OPTIONS = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Globe },
]

const LANGUAGE_OPTIONS = [
  { value: 'es', label: 'Spanish' },
  { value: 'en', label: 'English' },
  { value: 'pt', label: 'Portuguese' },
]

const NOTIFICATION_CHANNELS = [
  { id: 'email', label: 'Email', icon: '📧' },
  { id: 'telegram', label: 'Telegram', icon: '📱' },
  { id: 'slack', label: 'Slack', icon: '💬' },
  { id: 'webhook', label: 'Webhook', icon: '🔗' },
]

export function Settings() {
  const { darkMode, setDarkMode } = useAppStore()
  const [activeTab, setActiveTab] = useState<'general' | 'appearance' | 'notifications' | 'integrations' | 'security' | 'advanced'>('general')
  const [saving, setSaving] = useState(false)
  const [showApiKeyModal, setShowApiKeyModal] = useState(false)
  const [newApiKey, setNewApiKey] = useState('')

  const tabs = [
    { id: 'general', label: 'General', icon: Globe },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'integrations', label: 'Integrations', icon: Database },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'advanced', label: 'Advanced', icon: TestTube },
  ]

  const handleSave = async () => {
    setSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setSaving(false)
    toast.success('Settings saved successfully')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Settings</h1>
        <p className="text-dark-500 dark:text-dark-400 mt-1">Configure your Agenttic experience</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar Navigation */}
        <aside className="w-56 flex-shrink-0">
          <nav className="bg-white dark:bg-dark-900 rounded-xl border border-dark-200 dark:border-dark-700 p-3 space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                      : 'text-dark-600 hover:bg-dark-100 hover:text-dark-900 dark:text-dark-400 dark:hover:bg-dark-800'
                  )}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </aside>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {activeTab === 'general' && (
            <GeneralSettings onSave={handleSave} saving={saving} />
          )}
          {activeTab === 'appearance' && (
            <AppearanceSettings darkMode={darkMode} setDarkMode={setDarkMode} />
          )}
          {activeTab === 'notifications' && (
            <NotificationSettings />
          )}
          {activeTab === 'integrations' && (
            <IntegrationSettings />
          )}
          {activeTab === 'security' && (
            <SecuritySettings showApiKeyModal={showApiKeyModal} setShowApiKeyModal={setShowApiKeyModal} newApiKey={newApiKey} />
          )}
          {activeTab === 'advanced' && (
            <AdvancedSettings />
          )}
        </div>
      </div>

      {/* API Key Modal */}
      <Modal
        isOpen={showApiKeyModal}
        onClose={() => { setShowApiKeyModal(false); setNewApiKey('') }}
        title="New API Key Generated"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-dark-600 dark:text-dark-400">
            Copy this API key now. You won't be able to see it again.
          </p>
          <div className="flex gap-2">
            <Input
              value={newApiKey}
              onChange={(e) => setNewApiKey(e.target.value)}
              readOnly
              className="flex-1 font-mono bg-dark-100 dark:bg-dark-800"
            />
            <Button
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(newApiKey)
                toast.success('Copied to clipboard')
              }}
            >
              Copy
            </Button>
          </div>
          <Button variant="secondary" onClick={() => { setShowApiKeyModal(false); setNewApiKey('') }}>
            Done
          </Button>
        </div>
      </Modal>
    </div>
  )
}

function GeneralSettings({ onSave, saving }: { onSave: () => void; saving: boolean }) {
  const [formData, setFormData] = useState({
    name: 'Admin User',
    email: 'admin@agenttic.ai',
    company: 'Agenttic Inc.',
    timezone: 'America/Bogota',
    language: 'es',
    dateFormat: 'DD/MM/YYYY',
  })

  return (
    <Card>
      <CardTitle title="General Settings" subtitle="Basic account and application preferences" action={
        <Button onClick={onSave} loading={saving} leftIcon={<Save className="w-4 h-4" />}>
          Save Changes
        </Button>
      } />
      <CardContent>
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Full Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <Input
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <Input
            label="Company"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <Select
              label="Language"
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              options={LANGUAGE_OPTIONS}
            />
            <Select
              label="Timezone"
              value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              options={[
                { value: 'America/Bogota', label: 'America/Bogota (UTC-5)' },
                { value: 'America/New_York', label: 'America/New_York (UTC-5)' },
                { value: 'America/Los_Angeles', label: 'America/Los_Angeles (UTC-8)' },
                { value: 'Europe/Madrid', label: 'Europe/Madrid (UTC+1)' },
                { value: 'Europe/London', label: 'Europe/London (UTC+0)' },
                { value: 'Asia/Tokyo', label: 'Asia/Tokyo (UTC+9)' },
                { value: 'UTC', label: 'UTC' },
              ]}
            />
            <Select
              label="Date Format"
              value={formData.dateFormat}
              onChange={(e) => setFormData({ ...formData, dateFormat: e.target.value })}
              options={[
                { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
                { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
                { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
              ]}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function AppearanceSettings({ darkMode, setDarkMode }: { darkMode: boolean; setDarkMode: (enabled: boolean) => void }) {
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>(darkMode ? 'dark' : 'light')
  const [compactMode, setCompactMode] = useState(false)
  const [animations, setAnimations] = useState(true)

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle title="Theme" subtitle="Choose your preferred color scheme" />
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            {THEME_OPTIONS.map((option) => {
              const Icon = option.icon
              return (
                <button
                  key={option.value}
                  onClick={() => { setTheme(option.value); setDarkMode(option.value === 'dark') }}
                  className={cn(
                    'p-6 rounded-xl border-2 transition-all',
                    theme === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-dark-200 dark:border-dark-700 hover:border-dark-300 dark:hover:border-dark-600'
                  )}
                >
                  <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3', theme === option.value ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-dark-100 dark:bg-dark-800')}>
                    <Icon className={cn('w-6 h-6', theme === option.value ? 'text-primary-600 dark:text-primary-400' : 'text-dark-500 dark:text-dark-400')} />
                  </div>
                  <h4 className="font-medium text-dark-900 dark:text-white">{option.label}</h4>
                  <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">
                    {option.value === 'light' ? 'Always light' : option.value === 'dark' ? 'Always dark' : 'Match system'}
                  </p>
                </button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="Display" subtitle="Customize the interface" />
        <CardContent>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <p className="font-medium text-dark-900 dark:text-white">Compact Mode</p>
                <p className="text-sm text-dark-500 dark:text-dark-400">Reduce padding and spacing</p>
              </div>
              <input
                type="checkbox"
                checked={compactMode}
                onChange={(e) => setCompactMode(e.target.checked)}
                className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <p className="font-medium text-dark-900 dark:text-white">Animations</p>
                <p className="text-sm text-dark-500 dark:text-dark-400">Enable transitions and animations</p>
              </div>
              <input
                type="checkbox"
                checked={animations}
                onChange={(e) => setAnimations(e.target.checked)}
                className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
            </label>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function NotificationSettings() {
  const [enabled, setEnabled] = useState(true)
  const [channels, setChannels] = useState({
    email: true,
    telegram: false,
    slack: false,
    webhook: false,
  })
  const [events, setEvents] = useState({
    execution_complete: true,
    execution_failed: true,
    execution_started: false,
    document_processed: false,
    workflow_triggered: false,
    daily_summary: true,
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle title="Notifications" subtitle="Configure how you receive alerts" />
        <CardContent>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <p className="font-medium text-dark-900 dark:text-white">Enable Notifications</p>
                <p className="text-sm text-dark-500 dark:text-dark-400">Receive notifications for important events</p>
              </div>
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
            </label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="Channels" subtitle="Choose where to receive notifications" />
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {NOTIFICATION_CHANNELS.map((channel) => (
              <label key={channel.id} className="flex items-center gap-3 p-4 rounded-xl border border-dark-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors cursor-pointer">
                <span className="text-3xl">{channel.icon}</span>
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">{channel.label}</p>
                  <p className="text-sm text-dark-500 dark:text-dark-400">Channel</p>
                </div>
                <input
                  type="checkbox"
                  checked={channels[channel.id as keyof typeof channels]}
                  onChange={(e) => setChannels({ ...channels, [channel.id]: e.target.checked })}
                  className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500 ml-auto"
                />
              </label>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="Events" subtitle="Select which events trigger notifications" />
        <CardContent>
          <div className="space-y-3">
            {[
              { id: 'execution_complete', label: 'Execution Completed', description: 'When a pipeline finishes successfully' },
              { id: 'execution_failed', label: 'Execution Failed', description: 'When a pipeline encounters an error' },
              { id: 'execution_started', label: 'Execution Started', description: 'When a pipeline begins running' },
              { id: 'document_processed', label: 'Document Processed', description: 'When a document finishes processing' },
              { id: 'workflow_triggered', label: 'Workflow Triggered', description: 'When a scheduled workflow runs' },
              { id: 'daily_summary', label: 'Daily Summary', description: 'Daily digest of system activity' },
            ].map((event) => (
              <label key={event.id} className="flex items-start gap-3 p-4 rounded-lg border border-dark-200 dark:border-dark-700 hover:bg-dark-50 dark:hover:bg-dark-800/50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={events[event.id as keyof typeof events]}
                  onChange={(e) => setEvents({ ...events, [event.id]: e.target.checked })}
                  className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500 mt-0.5"
                />
                <div>
                  <p className="font-medium text-dark-900 dark:text-white">{event.label}</p>
                  <p className="text-sm text-dark-500 dark:text-dark-400">{event.description}</p>
                </div>
              </label>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function IntegrationSettings() {
  const [integrations, setIntegrations] = useState({
    n8n: { enabled: true, url: 'http://localhost:5678', apiKey: '' },
    openai: { enabled: true, apiKey: '' },
    anthropic: { enabled: false, apiKey: '' },
    qdrant: { enabled: true, url: 'http://localhost:6333', apiKey: '' },
    postgres: { enabled: true, url: 'postgresql://localhost:5432/agenttic' },
    redis: { enabled: true, url: 'redis://localhost:6379' },
  })
  const [editing, setEditing] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      {Object.entries(integrations).map(([key, config]) => (
        <Card key={key}>
          <CardTitle
            title={key.toUpperCase()}
            subtitle={config.enabled ? 'Connected' : 'Not configured'}
            action={
              <Button
                variant={editing === key ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setEditing(editing === key ? null : key)}
              >
                {editing === key ? 'Save' : 'Configure'}
              </Button>
            }
          />
          <CardContent>
            {editing === key ? (
              <div className="space-y-4">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.enabled}
                    onChange={(e) => setIntegrations({ ...integrations, [key]: { ...config, enabled: e.target.checked } })}
                    className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="font-medium text-dark-900 dark:text-white">Enable integration</span>
                </label>
                {(key === 'n8n' || key === 'qdrant' || key === 'postgres' || key === 'redis') && (
                  <Input
                    label={key === 'postgres' || key === 'redis' ? 'Connection URL' : 'API URL'}
                    value={config.url}
                    onChange={(e) => setIntegrations({ ...integrations, [key]: { ...config, url: e.target.value } })}
                    placeholder={`http://localhost:${key === 'n8n' ? '5678' : key === 'qdrant' ? '6333' : key === 'postgres' ? '5432' : '6379'}`}
                  />
                )}
                {(key === 'openai' || key === 'anthropic' || key === 'n8n' || key === 'qdrant') && (
                  <Input
                    label="API Key"
                    type="password"
                    value={config.apiKey}
                    onChange={(e) => setIntegrations({ ...integrations, [key]: { ...config, apiKey: e.target.value } })}
                    placeholder="••••••••"
                    helperText="Leave empty to keep current key"
                  />
                )}
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 text-sm">
                <div>
                  <p className="text-dark-500 dark:text-dark-400">Status</p>
                  <Badge variant={config.enabled ? 'success' : 'neutral'} dot>
                    {config.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
                {(key === 'n8n' || key === 'qdrant' || key === 'postgres' || key === 'redis') && (
                  <div>
                    <p className="text-dark-500 dark:text-dark-400">URL</p>
                    <p className="font-mono text-dark-900 dark:text-white truncate max-w-xs">{config.url}</p>
                  </div>
                )}
                {(key === 'openai' || key === 'anthropic' || key === 'n8n' || key === 'qdrant') && (
                  <div>
                    <p className="text-dark-500 dark:text-dark-400">API Key</p>
                    <p className="font-mono text-dark-900 dark:text-white">{config.apiKey ? '••••••••' : 'Not set'}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function SecuritySettings({ showApiKeyModal, setShowApiKeyModal, newApiKey }: { showApiKeyModal: boolean; setShowApiKeyModal: (show: boolean) => void; newApiKey: string }) {
  const [twoFactor, setTwoFactor] = useState(false)
  const [sessionTimeout, setSessionTimeout] = useState(24)
  const [apiKeys, setApiKeys] = useState([
    { id: '1', name: 'Production API', key: 'agt_••••••••••••••••', created: '2024-01-15', lastUsed: '2 hours ago' },
    { id: '2', name: 'Development', key: 'agt_••••••••••••••••', created: '2024-01-10', lastUsed: '3 days ago' },
  ])

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle title="Two-Factor Authentication" subtitle="Add an extra layer of security to your account" />
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-dark-900 dark:text-white">Enable 2FA</p>
              <p className="text-sm text-dark-500 dark:text-dark-400">Require authentication code on login</p>
            </div>
            <input
              type="checkbox"
              checked={twoFactor}
              onChange={(e) => setTwoFactor(e.target.checked)}
              className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="Session Management" subtitle="Control how long sessions stay active" />
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Session Timeout"
              value={sessionTimeout.toString()}
              onChange={(e) => setSessionTimeout(parseInt(e.target.value))}
              options={[
                { value: '1', label: '1 Hour' },
                { value: '4', label: '4 Hours' },
                { value: '8', label: '8 Hours' },
                { value: '24', label: '24 Hours' },
                { value: '168', label: '1 Week' },
              ]}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="API Keys" subtitle="Manage your API keys for programmatic access" action={
          <Button onClick={() => { setNewApiKey('agt_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)); setShowApiKeyModal(true) }} leftIcon={<Key className="w-4 h-4" />}>
            Generate New Key
          </Button>
        } />
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-200 dark:border-dark-700">
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Key</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Last Used</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-200 dark:divide-dark-700">
                {apiKeys.map((key) => (
                  <tr key={key.id} className="hover:bg-dark-50 dark:hover:bg-dark-800/50">
                    <td className="px-4 py-3 font-medium text-dark-900 dark:text-white">{key.name}</td>
                    <td className="px-4 py-3 font-mono text-dark-600 dark:text-dark-400">{key.key}</td>
                    <td className="px-4 py-3 text-dark-600 dark:text-dark-400">{key.created}</td>
                    <td className="px-4 py-3 text-dark-600 dark:text-dark-400">{key.lastUsed}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function AdvancedSettings() {
  const [debugMode, setDebugMode] = useState(false)
  const [logLevel, setLogLevel] = useState('info')
  const [dataRetention, setDataRetention] = useState(90)
  const [maxFileSize, setMaxFileSize] = useState(50)
  const [rateLimit, setRateLimit] = useState(100)

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle title="Debug & Logging" subtitle="Configure debugging and log levels" />
        <CardContent>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <p className="font-medium text-dark-900 dark:text-white">Debug Mode</p>
                <p className="text-sm text-dark-500 dark:text-dark-400">Enable detailed logging and debug endpoints</p>
              </div>
              <input
                type="checkbox"
                checked={debugMode}
                onChange={(e) => setDebugMode(e.target.checked)}
                className="w-5 h-5 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
            </label>
            <Select
              label="Log Level"
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              options={[
                { value: 'debug', label: 'Debug' },
                { value: 'info', label: 'Info' },
                { value: 'warn', label: 'Warning' },
                { value: 'error', label: 'Error' },
              ]}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="Data Retention" subtitle="Configure how long data is stored" />
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <Input
              label="Execution Logs (days)"
              type="number"
              value={dataRetention}
              onChange={(e) => setDataRetention(parseInt(e.target.value))}
              min="1"
              max="365"
            />
            <Input
              label="Max File Size (MB)"
              type="number"
              value={maxFileSize}
              onChange={(e) => setMaxFileSize(parseInt(e.target.value))}
              min="1"
              max="500"
            />
            <Input
              label="Rate Limit (req/min)"
              type="number"
              value={rateLimit}
              onChange={(e) => setRateLimit(parseInt(e.target.value))}
              min="10"
              max="1000"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle title="Danger Zone" subtitle="Irreversible actions" />
        <CardContent>
          <div className="flex items-center justify-between p-4 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-900/20">
            <div>
              <p className="font-medium text-red-800 dark:text-red-400">Reset All Data</p>
              <p className="text-sm text-red-600 dark:text-red-300">Permanently delete all executions, documents, and workflows. This cannot be undone.</p>
            </div>
            <Button variant="danger" size="sm">Reset Data</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}