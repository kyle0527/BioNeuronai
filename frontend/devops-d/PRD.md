# Planning Guide

A high-performance developer operations dashboard for BioNeuronAI that enables rapid API testing, monitoring, and data inspection with minimal overhead and maximum efficiency.

**Experience Qualities**:
1. **Fast** - Instant feedback, minimal animations, optimized rendering for large datasets
2. **Technical** - Raw JSON visibility, copy-to-clipboard functionality, developer-focused UX
3. **Functional** - No-nonsense interface prioritizing speed and information density over aesthetics

**Complexity Level**: Light Application (multiple features with basic state)
- Multiple API endpoints to manage with request/response handling, but primarily focused on data display and simple interactions rather than complex state management or workflows

## Essential Features

### System Status Monitor
- **Functionality**: Displays real-time system health from /status endpoint
- **Purpose**: Quick visibility into system operational state
- **Trigger**: Auto-loads on dashboard mount, manual refresh button
- **Progression**: Click refresh → API call → Display status with timestamp → Show raw JSON in collapsible panel
- **Success criteria**: Status updates within 500ms, clear visual indicators for system health

### Backtest Operations Panel
- **Functionality**: Interface for backtest endpoints (/backtest/*)
- **Purpose**: Execute and monitor backtesting operations
- **Trigger**: User selects backtest action from dropdown
- **Progression**: Select endpoint → Enter parameters (if needed) → Execute → Display results in table + raw JSON
- **Success criteria**: Results render instantly, JSON is copyable, table handles 100+ rows smoothly

### News Feed Viewer
- **Functionality**: Fetches and displays news from /news endpoint
- **Purpose**: Monitor relevant news data
- **Trigger**: Auto-loads on tab selection, manual refresh
- **Progression**: Load news → Parse response → Display in compact list → Expand for details + JSON
- **Success criteria**: News items load in <1s, list scrolls smoothly

### Pre-Trade Analysis
- **Functionality**: Calls /pretrade endpoint and displays analysis results
- **Purpose**: Review pre-trade checks and analysis
- **Trigger**: User clicks "Run Pre-Trade Analysis"
- **Progression**: Click → API call → Display structured results + raw JSON → Copy button available
- **Success criteria**: Clear presentation of analysis data, instant copy feedback

### Chat Interface
- **Functionality**: Simple chat interface for /chat endpoint
- **Purpose**: Interact with AI chat functionality
- **Trigger**: User types message and sends
- **Progression**: Type message → Send → Display in chat history → Show raw request/response in inspector
- **Success criteria**: Messages appear immediately, history persists during session

### Trade Control Panel
- **Functionality**: Start/stop trading via /trade/start and /trade/stop
- **Purpose**: Control trading operations
- **Trigger**: User clicks start or stop button
- **Progression**: Click button → Confirm action → API call → Show response → Update UI state
- **Success criteria**: Immediate visual feedback, clear success/error states

### API Playground
- **Functionality**: Universal API testing interface - call any endpoint with custom JSON body
- **Purpose**: Debug and test any API endpoint flexibly
- **Trigger**: User navigates to playground tab
- **Progression**: Select/enter endpoint → Edit JSON body → Send request → View formatted response + headers → Copy JSON
- **Success criteria**: JSON editor validates syntax, response displays within 100ms of receipt

### Request History Viewer
- **Functionality**: Logs all API requests/responses with exportable history
- **Purpose**: Track API usage, debug issues, analyze performance, export audit logs
- **Trigger**: Automatically logs all requests, user navigates to history tab
- **Progression**: View logged requests → Filter by method/status → Select request → View full details (headers, body, timing) → Export as JSON/CSV
- **Success criteria**: All requests logged with <10ms overhead, history persists across sessions, export includes full request/response data

## Edge Case Handling
- **Network Failures**: Display clear error messages with retry button and error details in JSON inspector, log failures in request history
- **Malformed JSON Responses**: Show raw response text with warning, don't crash the UI, log malformed responses
- **Large Datasets**: Virtualize tables beyond 100 rows, paginate if needed, limit request history to 500 most recent entries
- **Empty Responses**: Show "No data available" state with timestamp of last successful call
- **Concurrent Requests**: Show loading states per-panel, don't block other operations, log all concurrent requests independently
- **Storage Limits**: Request history automatically prunes oldest entries beyond 500, export option available before pruning
- **Filter Results**: Show appropriate empty state when filters produce no results in request history

## Design Direction
The design should feel like a professional internal tool - utilitarian, information-dense, and optimized for developer workflows. Think DataDog, Grafana, or Postman rather than consumer apps. Emphasize clarity, speed, and data visibility over visual flourish.

## Color Selection
A neutral, high-contrast developer tool aesthetic with subtle color coding for status states.

- **Primary Color**: Deep slate blue `oklch(0.25 0.02 250)` - Professional and technical without being stark
- **Secondary Colors**: 
  - Muted gray `oklch(0.45 0.01 250)` for secondary UI elements
  - Warm gray `oklch(0.85 0.01 250)` for subtle backgrounds
- **Accent Color**: Bright cyan `oklch(0.75 0.15 200)` - High visibility for CTAs and active states
- **Foreground/Background Pairings**:
  - Background (Off-white #FAFAFA `oklch(0.98 0 0)`): Dark text `oklch(0.2 0 0)` - Ratio 14.7:1 ✓
  - Card (White `oklch(1 0 0)`): Dark text `oklch(0.2 0 0)` - Ratio 16.1:1 ✓
  - Primary (Slate Blue `oklch(0.25 0.02 250)`): White text `oklch(0.98 0 0)` - Ratio 11.2:1 ✓
  - Accent (Cyan `oklch(0.75 0.15 200)`): Dark text `oklch(0.2 0 0)` - Ratio 7.8:1 ✓
  - Success (Green `oklch(0.55 0.15 145)`): White text `oklch(1 0 0)` - Ratio 4.8:1 ✓
  - Error (Red `oklch(0.55 0.22 25)`): White text `oklch(1 0 0)` - Ratio 5.1:1 ✓

## Font Selection
Monospace for technical precision and readability of code/JSON, sans-serif for UI labels.

- **Typographic Hierarchy**:
  - H1 (Page Title): JetBrains Mono Medium/24px/tight letter-spacing (-0.02em)
  - H2 (Section Headers): JetBrains Mono Medium/18px/normal letter-spacing
  - H3 (Card Titles): JetBrains Mono Medium/14px/normal letter-spacing
  - Body (Labels/Text): Inter Regular/14px/normal letter-spacing
  - Code/JSON: JetBrains Mono Regular/13px/normal letter-spacing, line-height 1.6
  - Small (Timestamps): Inter Regular/12px/letter-spacing 0.01em

## Animations
Animations should be extremely minimal - only for essential feedback. No page transitions, no elaborate hover effects. Priority is speed.

- Hover states: Instant color change, no transitions
- Loading spinners: Simple rotate animation, no elaborate loaders
- Toast notifications: Slide in from top-right, 200ms duration
- Collapsible panels: Instant toggle, no accordion animation (override defaults)
- Copy feedback: Instant icon swap (clipboard → checkmark)

## Component Selection
- **Components**:
  - `Card` - Primary container for all dashboard panels
  - `Button` - All actions, with variants (default, outline, ghost, destructive)
  - `Tabs` - Navigate between different dashboard views (Dashboard, API Playground, Request History, Chat)
  - `Table` - Display structured data from API responses
  - `ScrollArea` - For JSON inspector, request history list, and long content lists
  - `Alert` - Error messages and system notifications
  - `Badge` - Status indicators (online/offline, success/error), HTTP methods, status codes
  - `Separator` - Visual dividers between sections
  - `Select` - Dropdown for endpoint selection in backtest panel and filters in request history
  - `Textarea` - JSON body input in API playground
  - `Label` - Form labels
- **Customizations**:
  - Custom JSON viewer component with syntax highlighting and copy button
  - Custom code block component using `<pre>` with monospace font
  - Fast table component (no sorting/filtering overhead unless needed)
  - Copy-to-clipboard button component with instant feedback
  - Request log viewer with split-pane layout (list + details)
- **States**:
  - Buttons: Minimal hover (slight background change), active (pressed state), disabled (reduced opacity)
  - Inputs: Focus ring in accent color, error state in red
  - Cards: Subtle border, no hover effects
  - Tables: Zebra striping for readability, no row hover animations
  - Request list items: Hover background, selected state background
- **Icon Selection**:
  - Phosphor icons throughout
  - Copy: `Copy` icon, switches to `Check` on success
  - Refresh: `ArrowClockwise`
  - Play/Stop: `Play`, `Stop` for trade controls
  - Error: `WarningCircle`
  - Success: `CheckCircle`
  - JSON: `Code`
  - Send: `PaperPlaneRight`
  - Export: `Download`
  - Delete: `Trash`
  - Filter: `FunnelSimple`
  - Pending: `Clock`
- **Spacing**:
  - Card padding: `p-6`
  - Grid gap: `gap-4`
  - Section spacing: `space-y-4`
  - Inline elements: `gap-2`
  - Page padding: `p-6`
- **Mobile**:
  - Single column card layout on mobile
  - Tabs convert to dropdown/select on small screens
  - Tables scroll horizontally with sticky first column
  - Reduce card padding to `p-4` on mobile
  - JSON inspector full-width with horizontal scroll
  - Request history stacks vertically (full list, then details below when selected)
