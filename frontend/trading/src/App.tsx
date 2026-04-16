import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { OverviewPage } from '@/components/pages/overview-page'
import { BacktestPage } from '@/components/pages/backtest-page'
import { ChatPage } from '@/components/pages/chat-page'
import { TradeControlPage } from '@/components/pages/trade-control-page'
import { AnalyticsPage } from '@/components/pages/analytics-page'
import { House, ChartBar, ChatCircle, Lightning, TrendUp, List } from '@phosphor-icons/react'

type Page = 'overview' | 'backtest' | 'chat' | 'trade' | 'analytics'

const navigation = [
  { id: 'overview' as Page, label: 'Overview', icon: House },
  { id: 'analytics' as Page, label: 'Analytics', icon: TrendUp },
  { id: 'backtest' as Page, label: 'Backtest', icon: ChartBar },
  { id: 'chat' as Page, label: 'Chat Assistant', icon: ChatCircle },
  { id: 'trade' as Page, label: 'Trade Control', icon: Lightning },
]

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <OverviewPage />
      case 'analytics':
        return <AnalyticsPage />
      case 'backtest':
        return <BacktestPage />
      case 'chat':
        return <ChatPage />
      case 'trade':
        return <TradeControlPage />
      default:
        return <OverviewPage />
    }
  }

  const NavContent = () => (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b border-border">
        <h2 className="text-xl font-bold font-mono">BioNeuronAI</h2>
        <p className="text-xs text-muted-foreground mt-1">Trading Operations</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => (
          <Button
            key={item.id}
            variant={currentPage === item.id ? 'default' : 'ghost'}
            className={cn(
              'w-full justify-start',
              currentPage === item.id && 'bg-primary text-primary-foreground'
            )}
            onClick={() => {
              setCurrentPage(item.id)
              setSidebarOpen(false)
            }}
          >
            <item.icon className="mr-3" size={20} />
            {item.label}
          </Button>
        ))}
      </nav>
      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          API: <span className="font-mono">localhost:8000</span>
        </p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-background">
      <div className="hidden md:block fixed left-0 top-0 h-screen w-64 border-r border-border bg-card">
        <NavContent />
      </div>

      <div className="md:pl-64">
        <header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur md:hidden">
          <div className="flex items-center justify-between p-4">
            <div>
              <h1 className="text-lg font-bold font-mono">BioNeuronAI</h1>
              <p className="text-xs text-muted-foreground">Trading Operations</p>
            </div>
            <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                  <List size={20} />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                <NavContent />
              </SheetContent>
            </Sheet>
          </div>
        </header>

        <main className="p-4 md:p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

export default App
