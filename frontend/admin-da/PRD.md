# Planning Guide

A professional fintech admin dashboard for BioNeuronAI that prioritizes transparency, risk awareness, and operational clarity through minimal, data-first design patterns.

**Experience Qualities**:
1. **Trustworthy** - High contrast, clear typography, and explicit risk indicators create confidence through transparency
2. **Focused** - Strict grid system and progressive disclosure prevent information overload while keeping critical data visible
3. **Professional** - Calm dark mode aesthetic with fintech-grade data presentation establishes serious, institutional credibility

**Complexity Level**: Complex Application (advanced functionality, likely with multiple views)
This dashboard integrates real-time data from FastAPI backend, manages multiple states (testnet/mainnet), displays time-sensitive trading information, provides audit logging, and includes risk management interfaces requiring careful state orchestration.

## Essential Features

**Real-time Data Updates (WebSocket)**
- Functionality: Maintains persistent WebSocket connection for live dashboard updates
- Purpose: Provides instant feedback on risk changes, trade events, and system status without polling
- Trigger: Established on mount, auto-reconnects on disconnection
- Progression: Connect → Show "Live" indicator → Receive updates → Apply to UI → On disconnect, retry
- Success criteria: Connection status visible, data updates within 100ms, automatic reconnection on failure

**Risk Level Monitor**
- Functionality: Displays current portfolio risk exposure with visual indicators
- Purpose: Critical safety feature for futures trading to prevent catastrophic losses
- Trigger: Auto-updates on data fetch from `/api/v1/risk`
- Progression: Data fetch → Risk calculation → Color-coded display → Timestamp update
- Success criteria: Shows percentage/level, updates timestamp, uses clear visual hierarchy

**Max Drawdown Tracker**
- Functionality: Shows maximum peak-to-trough decline placeholder with historical context
- Purpose: Provides key risk metric for trading performance evaluation
- Trigger: Loads on mount, refreshes on interval
- Progression: Fetch → Display percentage → Show time period → Update timestamp
- Success criteria: Displays metric clearly with proper formatting and last update time

**Pre-trade Checklist Summary**
- Functionality: Compact overview of critical pre-trade validation items
- Purpose: Enforces systematic risk management before executing trades
- Trigger: Visible on dashboard, expands on interaction
- Progression: Show summary count → Click to expand → View full checklist → Collapse
- Success criteria: Shows completed/total items, expandable details, clear pass/fail state

**Testnet/Mainnet Mode Indicator**
- Functionality: Explicit, always-visible environment mode display
- Purpose: Prevents accidental real-money trading on wrong environment
- Trigger: Always visible in header/prominent location
- Progression: Reads environment state → Displays with high contrast → Color codes warning
- Success criteria: Impossible to miss, color-coded (testnet safe color, mainnet warning color)

**Futures Trading Risk Warning**
- Functionality: Prominent, persistent warning about futures trading risks
- Purpose: Legal/ethical obligation to inform users of high-risk trading
- Trigger: Visible on initial load and relevant screens
- Progression: Display on mount → User must acknowledge → Can be minimized but remains accessible
- Success criteria: Clear, legally appropriate language, cannot be permanently dismissed

**Audit Log Component**
- Functionality: Clean, chronological log of system actions (backtest runs, trades, chat sessions)
- Purpose: Provides transparency and debugging capability for operations
- Trigger: Auto-updates as new events occur
- Progression: Event occurs → Log entry created → Displayed chronologically → Timestamped
- Success criteria: Shows event type, timestamp, status, supports filtering/search

**Trading Controls Panel**
- Functionality: Centralized controls for executing and managing trades with order type selection
- Purpose: Provides safe, explicit interface for trade execution with clear visual hierarchy
- Trigger: Always visible in dashboard, disabled if pre-trade checklist incomplete
- Progression: Select symbol → Choose order type → Set parameters → Preview → Confirm → Execute
- Success criteria: Clear validation, prevents accidental execution, shows order preview before submission

**Real-time Position Monitor**
- Functionality: Live display of open positions with P&L, entry price, and current price
- Purpose: Essential for risk management and trade monitoring in real-time
- Trigger: Auto-updates via WebSocket connection when positions change
- Progression: Position opened → Display in table → Update P&L continuously → Show close action → Position closed
- Success criteria: Updates within 100ms, color-coded P&L, sortable by various metrics, quick close action

**Live Price Charts with Candlestick Visualization**
- Functionality: Real-time candlestick charts displaying price movements across multiple timeframes
- Purpose: Provides visual market analysis for informed trading decisions
- Trigger: Auto-loads on mount, updates via WebSocket for selected symbol
- Progression: Select symbol → Choose timeframe (1m/5m/15m/1h/4h/1d) → View chart → Hover for candle details
- Success criteria: Smooth rendering of 50+ candles, hover tooltips with OHLCV data, symbol switcher, real-time updates

**Order History and Trade Analytics Dashboard**
- Functionality: Comprehensive view of past orders and aggregated trading performance metrics
- Purpose: Enables performance tracking and strategy evaluation through historical data
- Trigger: Loads historical data on mount, updates via WebSocket for new orders
- Progression: View analytics overview → Switch to order history table → Filter/sort orders → Review performance metrics
- Success criteria: Displays total P&L, win rate, profit factor, average win/loss, sortable history table with status badges

**Advanced Order Types (Trailing Stop & OCO)**
- Functionality: Support for trailing stop orders (with delta/percentage) and One-Cancels-Other (OCO) orders
- Purpose: Provides sophisticated risk management tools for advanced trading strategies
- Trigger: Selected via order type tabs in trading controls
- Progression: Select order type → Configure parameters (trailing delta/percent or OCO prices) → Preview → Submit
- Success criteria: Tab-based UI for order type selection, clear parameter input fields, validation for required fields, helpful tooltips

## Edge Case Handling

- **WebSocket Connection Failed**: Fall back to initial HTTP fetch, show connection status as "Disconnected", attempt auto-reconnect
- **WebSocket Disconnected Mid-Session**: Display "Connecting" status, attempt reconnection, show toast notification
- **API Unavailable**: Show clear "Connection Lost" state with retry mechanism, disable interactive features, display demo data
- **Stale Data**: Display prominent "Data Outdated" warning if last update exceeds threshold
- **Empty States**: Show helpful onboarding messages for new users with no trading history
- **Network Errors**: Toast notifications for failed requests with actionable retry options
- **Invalid Risk Levels**: Display error state with fallback to last known good value

## Design Direction

The design should evoke institutional trust, precision, and calm focus - like a Bloomberg terminal but modern and minimal. Users should feel in control, informed, and protected from hasty decisions through clear information architecture.

## Color Selection

A professional dark mode palette with high contrast ratios for critical data visibility, using cool neutrals as foundation with strategic accent colors for risk states.

- **Primary Color**: Deep electric blue (oklch(0.55 0.18 250)) - Represents technology and trust, used for interactive elements and data highlights
- **Secondary Colors**: Cool slate grays (oklch(0.25 0.01 250) to oklch(0.35 0.01 250)) for cards and containers, creating depth without distraction
- **Accent Color**: Bright cyan (oklch(0.75 0.15 200)) for CTAs and important interactive elements, provides high visibility
- **Risk State Colors**: 
  - Safe/Testnet: Muted green (oklch(0.65 0.12 145))
  - Warning/Medium Risk: Amber (oklch(0.75 0.15 85))
  - Danger/Mainnet: Vivid red (oklch(0.60 0.22 25))
- **Foreground/Background Pairings**:
  - Background (Dark slate oklch(0.12 0.01 250)): Light text (oklch(0.98 0 0)) - Ratio 16.8:1 ✓
  - Primary (Electric blue oklch(0.55 0.18 250)): White text (oklch(1 0 0)) - Ratio 5.2:1 ✓
  - Accent (Bright cyan oklch(0.75 0.15 200)): Dark text (oklch(0.12 0.01 250)) - Ratio 12.1:1 ✓
  - Card (Cool slate oklch(0.18 0.01 250)): Light text (oklch(0.98 0 0)) - Ratio 13.4:1 ✓

## Font Selection

Typography should communicate precision and professionalism while maintaining excellent readability for data-heavy interfaces. JetBrains Mono for numerical data provides clarity, while Space Grotesk offers modern geometric crispness for UI text.

- **Typographic Hierarchy**:
  - H1 (Page Title): Space Grotesk Bold/32px/tight letter spacing (-0.02em)
  - H2 (Section Headers): Space Grotesk SemiBold/24px/tight letter spacing (-0.01em)
  - H3 (Widget Titles): Space Grotesk Medium/18px/normal letter spacing
  - Body (Interface Text): Space Grotesk Regular/14px/normal letter spacing/1.5 line height
  - Data/Metrics: JetBrains Mono Medium/16-24px/tabular numbers enabled
  - Small/Timestamps: Space Grotesk Regular/12px/muted color/1.4 line height
  - Monospace Code: JetBrains Mono Regular/13px for API endpoints and technical details

## Animations

Animations should be subtle and purposeful, reinforcing state changes and guiding attention without adding cognitive load. Use quick, snappy transitions (150-200ms) for data updates to feel responsive, and gentle fades for progressive disclosure to maintain focus.

- Data refresh: Quick fade transition (150ms) when updating metrics
- Progressive disclosure: Smooth height expansion (250ms ease-out) for accordion-style details
- Risk level changes: Attention-drawing pulse (300ms) on state transition, then settle
- Hover states: Instant background shift (100ms) on interactive elements
- Loading states: Gentle pulse on skeleton loaders, no spinning wheels

## Component Selection

- **Components**: 
  - Card: Primary container for all widgets, with subtle border and dark background
  - Badge: For testnet/mainnet indicator, risk levels, status tags, and WebSocket connection status
  - Accordion: For pre-trade checklist progressive disclosure
  - Table: For audit log with sortable columns
  - Separator: To create visual hierarchy between sections
  - Skeleton: For loading states on data-heavy widgets
  - Alert: For futures trading risk warning banner
  - Tooltip: For additional context on hover without cluttering interface
  - Progress: For checklist completion visualization
  - Tabs: If multiple view modes needed (dashboard/settings/logs)

- **Customizations**:
  - Custom MetricCard component: Large numeric display with label, timestamp, and optional trend indicator
  - Custom AuditLogRow component: Timestamp, event type icon, description, status badge
  - Custom RiskIndicator component: Visual level display with color coding and percentage
  - Custom EnvironmentBadge component: Highly visible testnet/mainnet switcher with icon
  - Custom ConnectionStatus component: Real-time WebSocket status with color-coded icons (Live/Connecting/Disconnected/Error)

- **States**:
  - Buttons: Subtle bg shift on hover, pressed state with slight scale, disabled with reduced opacity
  - Cards: Faint border glow on hover for interactive cards, no effect for static displays
  - Inputs: Focused state with accent color border and subtle shadow
  - Data widgets: Loading skeleton, error state with retry action, stale data warning overlay

- **Icon Selection**: 
  - Warning: For risk warnings and alerts
  - ChartLine: For trading and performance metrics
  - CheckSquare: For checklist items
  - Clock: For timestamps and last updated
  - Activity: For audit log entries
  - ShieldWarning: For testnet/mainnet mode
  - TrendUp/TrendDown: For performance indicators
  - WifiHigh/WifiSlash/WifiX: For WebSocket connection status
  
- **Spacing**: 
  - Container padding: p-6 for cards, p-8 for main layout
  - Section gaps: gap-6 for widget grid
  - Content spacing: gap-4 within cards, gap-2 for tight groupings
  - Grid margins: mx-auto max-w-7xl for content constraint

- **Mobile**: 
  - Single column layout stacking widgets vertically
  - Testnet/mainnet indicator remains pinned to top
  - Condensed metric cards with smaller typography
  - Audit log switches to compact card view instead of table
  - Maintain all critical information but reduce whitespace and scale
