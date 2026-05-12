import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { StatusPanel } from '@/components/panels/StatusPanel'
import { BacktestPanel } from '@/components/panels/BacktestPanel'
import { NewsPanel } from '@/components/panels/NewsPanel'
import { PreTradePanel } from '@/components/panels/PreTradePanel'
import { ChatPanel } from '@/components/panels/ChatPanel'
import { TradeControlPanel } from '@/components/panels/TradeControlPanel'
import { APIPlayground } from '@/components/panels/APIPlayground'
import { RequestHistoryPanel } from '@/components/panels/RequestHistoryPanel'
import { RiskConfigPanel } from '@/components/panels/RiskConfigPanel'
import { DataCatalogPanel } from '@/components/panels/DataCatalogPanel'
import { TrainingPanel } from '@/components/panels/TrainingPanel'
import { OperationsOverviewPanel } from '@/components/panels/OperationsOverviewPanel'
import { Toaster } from '@/components/ui/sonner'
import { Badge } from '@/components/ui/badge'
import { Link } from '@phosphor-icons/react'
import { RequestLoggerProvider, useRequestLoggerContext } from '@/lib/RequestLoggerContext'
import { setRequestLogger } from '@/lib/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function AppContent() {
  const [activeTab, setActiveTab] = useState('operations')
  const { logRequest } = useRequestLoggerContext()

  useEffect(() => {
    setRequestLogger(logRequest)
  }, [logRequest])

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-mono font-medium tracking-tight">BioNeuronAI Operations</h1>
          <Badge variant="secondary" className="gap-1.5 font-mono text-xs">
            <Link size={14} weight="bold" />
            {API_BASE_URL}
          </Badge>
        </div>
      </header>

      <main className="container mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="operations">Operations</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
            <TabsTrigger value="config">Config</TabsTrigger>
            <TabsTrigger value="tools">Dev Tools</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
          </TabsList>

          <TabsContent value="operations" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <OperationsOverviewPanel />
              <TradeControlPanel />
              <PreTradePanel />
              <NewsPanel />
            </div>
          </TabsContent>

          <TabsContent value="validation" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <BacktestPanel />
              <DataCatalogPanel />
              <TrainingPanel />
            </div>
          </TabsContent>

          <TabsContent value="config" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <StatusPanel />
              <RiskConfigPanel />
            </div>
          </TabsContent>

          <TabsContent value="tools" className="space-y-4">
            <APIPlayground />
            <RequestHistoryPanel />
          </TabsContent>

          <TabsContent value="chat">
            <ChatPanel />
          </TabsContent>
        </Tabs>
      </main>

      <Toaster />
    </div>
  )
}

function App() {
  return (
    <RequestLoggerProvider>
      <AppContent />
    </RequestLoggerProvider>
  )
}

export default App
