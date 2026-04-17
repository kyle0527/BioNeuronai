> **⏸ 部署狀態：暫緩（第二階段）**
> 本前端為交易操作儀板（Trading Dashboard），原始碼保留但目前不作為部署目標。
> 第一階段僅推進 `frontend/devops-d/`。詳見 [部署準備紀錄](../../docs/DEPLOYMENT_READINESS_RECORD_20260417.md)。

# BioNeuronAI Trading Operations Dashboard

A modern, professional trading operations dashboard for the BioNeuronAI project. Built with React, TypeScript, and Tailwind CSS, featuring real-time data visualization, backtesting capabilities, AI chat assistance, and trade execution controls.

## Features

### 📊 Overview Dashboard
- **System Status**: Real-time monitoring of module availability and health
- **Backtest Catalog**: View available datasets and backtest resources
- **Recent Runs**: Track the latest backtest executions
- **News Sentiment**: Analyze market sentiment for trading symbols
- **Pretrade Checklist**: Validate trade conditions before execution

### 📈 Backtest Operations
- Configure backtest parameters (symbol, interval, dates, balance)
- **Inspect**: Preview data availability and warnings
- **Simulate**: Run strategy simulations with performance metrics
- **Run**: Execute full backtests and track results
- View comprehensive run history with status tracking

### 💬 Chat Assistant
- AI-powered trading assistant with conversation history
- Multi-language support (Auto, English, Chinese)
- Symbol context for targeted analysis
- Persistent conversation across sessions
- Response confidence and latency tracking

### ⚡ Trade Control
- Start/stop live trading operations
- Comprehensive safety warnings and checklist
- Trading status monitoring
- Confirmation dialogs for high-risk operations

### 📊 Performance Analytics
- Real-time portfolio tracking with live API integration
- Comprehensive P&L visualization and performance metrics
- Asset allocation breakdown with visual distribution
- Complete trade history with status tracking
- Time range filtering (7d, 30d, 90d, 1y, all)
- Mock data generation for testing and demonstrations
- CSV export for portfolio, trades, and full reports
- Automatic refresh with loading states
- Live vs mock data source indicators

## Technology Stack

- **Frontend**: React 19 + TypeScript
- **Styling**: Tailwind CSS v4 with custom dark theme
- **UI Components**: shadcn/ui components
- **Icons**: Phosphor Icons
- **State Management**: React Hooks
- **Build Tool**: Vite
- **API Integration**: Fetch API with TypeScript types

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running at `http://localhost:8000` (or configure custom URL)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Configuration

#### API Base URL

The dashboard connects to a FastAPI backend. You can configure the API base URL in two ways:

**1. Environment Variable** (Recommended)

Create a `.env` file in the project root:

```env
VITE_API_BASE_URL=http://localhost:8000
```

**2. Configuration File**

Edit `src/lib/api-config.ts`:

```typescript
export const API_CONFIG = {
  BASE_URL: 'http://your-api-url.com',
  API_VERSION: '/api/v1',
  TIMEOUT: 30000,
} as const
```

## API Endpoints

The dashboard integrates with the following FastAPI endpoints:

- `GET /api/v1/status` - System health and module status
- `GET /api/v1/backtest/catalog` - Available datasets
- `GET /api/v1/backtest/runs?limit=10` - Recent backtest runs
- `POST /api/v1/news` - News sentiment analysis
- `POST /api/v1/pretrade` - Pretrade validation checklist
- `GET /api/v1/backtest/inspect` - Inspect backtest data
- `POST /api/v1/backtest/simulate` - Simulate backtest execution
- `POST /api/v1/backtest/run` - Execute backtest
- `POST /api/v1/chat` - AI chat assistant
- `POST /api/v1/trade/start` - Start trading operations
- `POST /api/v1/trade/stop` - Stop trading operations
- `GET /api/v1/analytics/portfolio` - Portfolio holdings and metrics
- `GET /api/v1/analytics/trades?limit=100` - Trade history
- `GET /api/v1/analytics/performance?days=30` - Performance data

For detailed API specifications and response formats, see `BACKEND_API.md`.

## Project Structure

```
src/
├── components/
│   ├── pages/
│   │   ├── overview-page.tsx       # Dashboard overview
│   │   ├── analytics-page.tsx      # Performance analytics
│   │   ├── backtest-page.tsx       # Backtest operations
│   │   ├── chat-page.tsx           # AI chat assistant
│   │   └── trade-control-page.tsx  # Trade execution control
│   ├── ui/                         # shadcn components
│   ├── data-table.tsx              # Reusable data table
│   ├── metric-card.tsx             # KPI metric card
│   └── status-badge.tsx            # Status indicator badge
├── lib/
│   ├── api-client.ts               # API integration layer
│   ├── api-config.ts               # API configuration
│   ├── types.ts                    # TypeScript type definitions
│   ├── analytics-types.ts          # Analytics data types
│   ├── mock-data-generator.ts      # Mock data for testing
│   ├── export-utils.ts             # CSV export utilities
│   └── utils.ts                    # Utility functions
├── App.tsx                         # Main app with routing
├── index.css                       # Theme and global styles
└── main.tsx                        # Entry point
```

## Development

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Type Checking

```bash
npm run type-check
```

## Design System

### Color Palette

- **Background**: Rich black (`oklch(0.12 0.01 240)`)
- **Primary**: Deep cyan (`oklch(0.65 0.15 200)`) - Actions and focus
- **Accent**: Electric amber (`oklch(0.75 0.15 80)`) - Warnings and CTAs
- **Card**: Dark charcoal (`oklch(0.18 0.01 240)`) - Elevated surfaces

### Typography

- **Headings**: JetBrains Mono (monospace for technical precision)
- **Body**: Inter (clean sans-serif for readability)
- **Data/Code**: JetBrains Mono (consistent with technical context)

### Responsive Design

- **Desktop**: Persistent sidebar navigation (width: 256px)
- **Mobile**: Collapsible drawer navigation with hamburger menu
- **Breakpoint**: 768px (Tailwind `md`)

## Safety & Best Practices

⚠️ **Trading Warnings**: The dashboard includes prominent safety warnings for live trading operations:

- Always test strategies on testnet first
- Never trade with funds you cannot afford to lose
- Use stop-loss protection and risk limits
- Monitor positions actively
- Understand that autonomous trading carries significant risk

## Contributing

This is a demonstration dashboard. For production use:

1. Implement proper authentication and authorization
2. Add comprehensive error logging and monitoring
3. Implement rate limiting and request validation
4. Add unit and integration tests
5. Set up CI/CD pipelines
6. Implement proper secret management

## License

See LICENSE file for details.

## Support

For issues and questions:
- Check the PRD.md file for design decisions
- Review API endpoint documentation
- Verify backend is running and accessible

---

Built with ❤️ for trading operations excellence
