# Planning Guide

A sophisticated trading operations dashboard for BioNeuronAI that provides real-time system monitoring, backtesting capabilities, AI-powered chat assistance, and trade execution controls with a professional, data-focused interface.

**Experience Qualities**:
1. **Professional** - The interface should project confidence and precision expected in financial trading environments with clear data hierarchy and minimal visual noise.
2. **Responsive** - All interactions should feel immediate with loading states, optimistic updates, and smooth transitions that keep users informed of system status.
3. **Informative** - Complex trading data should be distilled into actionable insights through progressive disclosure, smart defaults, and contextual help.

**Complexity Level**: Complex Application (advanced functionality, likely with multiple views)
This is a multi-view dashboard with real-time data fetching, form handling, chat interfaces, trade execution controls, and comprehensive error handling across different API endpoints.

## Essential Features

### Navigation System
- **Functionality**: Collapsible sidebar navigation with route switching and mobile-responsive drawer
- **Purpose**: Provides clear structure for the four main application areas (Overview, Backtest, Chat, Trade Control)
- **Trigger**: User clicks navigation items or uses mobile hamburger menu
- **Progression**: Click navigation item → Route changes → Page content loads with skeleton → Data populates → Interactive state
- **Success criteria**: All routes accessible, current page highlighted, mobile menu works smoothly

### Overview Dashboard (Bento Grid)
- **Functionality**: Multi-card dashboard displaying system status, backtest catalog, recent runs, news sentiment, and pretrade checklist
- **Purpose**: Provides at-a-glance view of all critical system metrics and quick access to common operations
- **Trigger**: Default landing page or clicking "Overview" in navigation
- **Progression**: Page loads → Cards show skeletons → API calls execute in parallel → Cards populate with live data → Interactive elements become available
- **Success criteria**: All five cards display correct data, errors show toast notifications, cards are interactive

### Backtest Operations
- **Functionality**: Form-based interface for configuring and running backtests with results visualization
- **Purpose**: Allows traders to test strategies against historical data before live deployment
- **Trigger**: Navigate to Backtest page, fill form, click inspect/simulate/run buttons
- **Progression**: User enters parameters → Clicks action button → Loading state → Results display in panel → User can view JSON or summary → Click run row to see details
- **Success criteria**: Form validation works, all three operations return data, runs list updates, detail view shows complete information

### Chat Assistant
- **Functionality**: Conversational AI interface for trading queries with context awareness and multilingual support
- **Purpose**: Provides natural language interface to ask questions about trading, get analysis, and receive guidance
- **Trigger**: User types message and presses send or Enter
- **Progression**: User types query → Submits → Message appears in chat → Loading indicator → AI response streams in → Metadata (latency, confidence) displayed
- **Success criteria**: Conversation persists across sessions, language switching works, symbol context applies, all messages render correctly

### Trade Control
- **Functionality**: Start/stop trading operations with safety warnings, status monitoring, real-time WebSocket trade execution updates, price alert notifications, and live order book visualization
- **Purpose**: Controls live trading execution with clear safety guardrails while providing comprehensive market visibility and alert capabilities
- **Trigger**: User clicks start/stop trading buttons after acknowledging warnings, creates price alerts, or enables live WebSocket updates to monitor executions and order book depth
- **Progression**: User clicks start → Confirmation dialog appears → User confirms → API call executes → Status updates → Success/error feedback shown | User enables WebSocket → Connection establishes → Live updates stream in for executions and order book → User creates price alert → Alert triggers when price target met → Toast notification shown | User views order book → Real-time bid/ask prices update → Market depth visualized
- **Success criteria**: Cannot start without confirmation, status clearly visible, errors don't break state, stop always works, WebSocket connection status shows clearly, price alerts persist and trigger correctly, order book updates reflect real-time market depth, trade executions appear instantly when WebSocket enabled

### Performance Analytics
- **Functionality**: Portfolio tracking dashboard with P&L visualization, asset allocation breakdown, performance metrics, trade history, live API integration with real trading data, real-time WebSocket updates for live portfolio tracking, fallback mock data generation, and CSV export capabilities
- **Purpose**: Provides comprehensive real-time view of trading performance with key metrics, trends, insights, and data export options for external analysis. WebSocket integration enables instant updates when trades execute or portfolio values change without manual refresh.
- **Trigger**: Navigate to Analytics page from navigation (automatically fetches live data), toggle Real-time switch to enable WebSocket connection, click Refresh Live button to reload from API, click Mock Data button for demonstration/testing, or click export buttons
- **Progression**: Page loads → Loading skeletons show → Live API calls execute (portfolio, trades, performance) → Data populates or error toast appears → User toggles WebSocket on → Connection establishes → Real-time status indicator shows "Live" → Portfolio updates stream in automatically → User can switch time ranges → User can refresh or generate mock data → User can export data as CSV
- **Success criteria**: Live API integration works with proper error handling, WebSocket connection establishes successfully with visual status indicator (connected/connecting/disconnected), real-time updates apply to portfolio without page refresh, loading states show during API calls, data source badge indicates live vs mock data, time range filtering triggers API refresh, all metrics display correctly with live or mock data, portfolio breakdown is accurate, CSV exports download successfully with proper formatting, fallback to mock data works when API unavailable, WebSocket auto-reconnects on connection loss with toast notifications

## Edge Case Handling

- **API Unavailable**: Display error toast with retry button, show cached data if available, provide fallback instructions
- **Network Timeout**: Show loading states with timeout after 30s, allow manual retry, maintain form data
- **Invalid Form Data**: Inline validation with clear error messages, prevent submission until valid
- **Empty States**: Show helpful empty state messages with next action suggestions (no runs, no messages, etc.)
- **Malformed API Response**: Catch parsing errors, log to console, show user-friendly error message, don't crash app
- **Concurrent Operations**: Disable action buttons while operations in progress, queue requests if needed
- **Mobile Viewport**: Collapse sidebar, stack cards vertically, simplify tables to mobile-friendly format
- **Long Data Sets**: Implement pagination or virtual scrolling for runs tables and chat history

## Design Direction

The design should evoke precision, confidence, and technical sophistication appropriate for financial trading software. It should feel like a professional Bloomberg terminal reimagined with modern design principles - data-dense but not cluttered, powerful but not overwhelming, technical but not intimidating.

## Color Selection

A dark-mode-first palette with high contrast for readability during extended trading sessions, using terminal-inspired colors with strategic accent highlights.

- **Primary Color**: Deep cyan (`oklch(0.65 0.15 200)`) - Communicates technology, trust, and precision. Used for primary actions, active states, and key metrics.
- **Secondary Colors**: 
  - Slate gray (`oklch(0.35 0.02 240)`) for secondary actions and muted backgrounds
  - Dark charcoal (`oklch(0.18 0.01 240)`) for card backgrounds with subtle depth
- **Accent Color**: Electric amber (`oklch(0.75 0.15 80)`) - Attention-grabbing for critical alerts, CTAs, and warnings about trading operations
- **Foreground/Background Pairings**:
  - Background (Rich Black `oklch(0.12 0.01 240)`): Light gray text (`oklch(0.95 0 0)`) - Ratio 16.8:1 ✓
  - Primary (Deep Cyan `oklch(0.65 0.15 200)`): White text (`oklch(1 0 0)`) - Ratio 5.2:1 ✓
  - Accent (Electric Amber `oklch(0.75 0.15 80)`): Black text (`oklch(0.12 0.01 240)`) - Ratio 11.5:1 ✓
  - Card (Dark Charcoal `oklch(0.18 0.01 240)`): Light gray text (`oklch(0.95 0 0)`) - Ratio 13.2:1 ✓
  - Success (Green `oklch(0.7 0.15 150)`): White text (`oklch(1 0 0)`) - Ratio 5.8:1 ✓
  - Error (Red `oklch(0.65 0.20 25)`): White text (`oklch(1 0 0)`) - Ratio 4.9:1 ✓

## Font Selection

Typography should balance technical precision with modern readability, using monospace for data and sans-serif for UI elements.

- **Typographic Hierarchy**:
  - H1 (Page Title): JetBrains Mono Bold / 32px / -0.02em letter spacing / leading-tight
  - H2 (Section Title): JetBrains Mono SemiBold / 24px / -0.01em / leading-snug
  - H3 (Card Title): Inter SemiBold / 18px / normal spacing / leading-normal
  - Body (UI Text): Inter Regular / 14px / normal spacing / leading-relaxed
  - Caption (Metadata): Inter Medium / 12px / normal spacing / leading-normal / text-muted-foreground
  - Code/Data: JetBrains Mono Regular / 13px / normal spacing / leading-relaxed / monospace

## Animations

Animations should be subtle and purposeful, reinforcing the professional nature while providing feedback. Use micro-interactions for data updates and smooth transitions for page navigation. Card hover states should have subtle lift effects (2px translate-y with shadow), loading skeletons should pulse gently, and status indicators should animate color transitions over 200ms. Toast notifications slide in from top-right with spring physics. Avoid flashy or distracting animations that could obscure critical trading data.

## Component Selection

- **Components**:
  - Sidebar: Custom responsive sidebar with collapsible behavior (shadcn patterns)
  - Card: For all dashboard panels with consistent padding and hover states
  - Button: Primary actions (start trade, run backtest), secondary (cancel, reset), destructive (stop trading)
  - Form + Input + Label: All backtest configuration inputs with validation
  - Dialog: Trade control confirmations and run detail views
  - Drawer: Mobile navigation and quick detail panels
  - Table: Recent runs list with sortable columns and row click
  - Badge: Status indicators (success, warning, error, info)
  - Skeleton: Loading states for all async data
  - Scroll Area: Chat messages and long data lists
  - Separator: Visual dividers in complex layouts
  - Toast (Sonner): All error/success notifications
  
- **Customizations**:
  - Status Badge Component: Custom variant with dot indicator for live status (online/offline/error)
  - Metric Card Component: Reusable card with label, value, change indicator, and optional sparkline
  - Data Table Component: Enhanced table with empty states, loading states, and responsive mobile view
  - Message Bubble Component: Custom chat UI with timestamp, confidence, and latency metadata
  
- **States**:
  - Buttons: Default (solid primary), hover (brightness increase), active (slight scale), disabled (opacity 50%, cursor not-allowed), loading (spinner icon)
  - Inputs: Default (border-input), focus (ring-2 ring-primary), error (border-destructive, ring-destructive), disabled (opacity 50%, bg-muted)
  - Cards: Default (bg-card, border), hover (shadow-md, translate-y-[-2px] for interactive cards), selected (border-primary)
  
- **Icon Selection**:
  - Navigation: House (overview), ChartBar (backtest), ChatCircle (chat), Lightning (trade control), TrendUp (analytics)
  - Actions: Play (start), Stop (stop), ArrowsClockwise (refresh), MagnifyingGlass (inspect), Flask (simulate)
  - Status: CheckCircle (success), Warning (warning), XCircle (error), Info (info)
  - UI: List (menu), X (close), CaretDown (dropdown), ArrowRight (detail), Download (export)
  
- **Spacing**:
  - Page padding: p-6 (24px) on desktop, p-4 (16px) on mobile
  - Card padding: p-6 for body, p-4 for compact cards
  - Section gaps: gap-6 for main layout, gap-4 for related elements, gap-2 for tight groups
  - Component spacing: mb-6 for sections, mb-4 for subsections, mb-2 for related labels
  
- **Mobile**:
  - Sidebar collapses to drawer with hamburger trigger in top-left
  - Bento grid cards stack vertically (single column)
  - Tables transform to stacked card layout showing key fields only
  - Forms remain single column with full-width inputs
  - Chat interface maintains fixed input at bottom with scroll area for messages
  - Multi-column layouts (like backtest form + results) switch to tabs on mobile
