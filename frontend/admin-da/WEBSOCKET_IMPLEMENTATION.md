# WebSocket Implementation

This dashboard now includes real-time data updates via WebSocket connection to the FastAPI backend.

## WebSocket Endpoint

The dashboard connects to: `ws://localhost:8000/ws/dashboard`

## Features

### Real-time Updates
- Dashboard data automatically updates when changes occur on the server
- No need for polling or manual refresh
- Immediate reflection of risk levels, drawdown metrics, checklist status, and audit log entries

### Connection Management
- **Automatic Reconnection**: If the connection drops, the client will automatically attempt to reconnect up to 5 times with a 3-second interval
- **Connection Status Indicator**: Visual badge in the header showing current connection state:
  - **Live** (Green): WebSocket connected and receiving real-time updates
  - **Connecting** (Yellow): Attempting to establish connection
  - **Disconnected** (Gray): Connection lost, attempting reconnect
  - **Error** (Red): Connection error occurred

### Fallback Behavior
- If WebSocket connection fails, the dashboard falls back to HTTP REST API
- If both WebSocket and HTTP fail, demo data is displayed
- Toast notifications inform users of connection state changes

## Expected WebSocket Message Format

The backend should send dashboard updates in the following JSON format:

```json
{
  "environment": "testnet" | "mainnet",
  "risk": {
    "level": "low" | "medium" | "high" | "critical",
    "percentage": 34.5,
    "lastUpdated": "2024-01-15T10:30:00Z"
  },
  "maxDrawdown": {
    "current": 12.3,
    "historical": 18.7,
    "period": "90 days",
    "lastUpdated": "2024-01-15T10:30:00Z"
  },
  "pretradeChecklist": {
    "items": [
      {
        "id": "1",
        "label": "Risk limits configured",
        "completed": true,
        "required": true
      }
    ],
    "completedCount": 3,
    "totalCount": 5,
    "lastUpdated": "2024-01-15T10:30:00Z"
  },
  "auditLog": [
    {
      "id": "1",
      "timestamp": "2024-01-15T10:25:00Z",
      "eventType": "backtest" | "trade_start" | "trade_stop" | "chat_session" | "config_change",
      "description": "Completed backtest run for BTC/USDT strategy",
      "status": "success" | "error" | "pending" | "info"
    }
  ]
}
```

## Backend Implementation Example (FastAPI)

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections: list[WebSocket] = []

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send dashboard updates when data changes
            # This example sends an update every 5 seconds
            data = {
                "environment": "testnet",
                "risk": {
                    "level": "medium",
                    "percentage": 34.5,
                    "lastUpdated": datetime.now().isoformat()
                },
                # ... rest of dashboard data
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Broadcast function to notify all connected clients
async def broadcast_dashboard_update(data: dict):
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(data))
        except:
            active_connections.remove(connection)
```

## Client Usage

The WebSocket connection is managed by the `useWebSocket` hook, which is already integrated into the `DashboardView` component. No additional configuration needed for basic usage.

### Custom WebSocket Hook Options

```typescript
const { status, lastMessage, sendMessage, connect, disconnect } = useWebSocket({
  url: 'ws://localhost:8000/ws/dashboard',
  reconnect: true,                    // Enable auto-reconnect
  reconnectInterval: 3000,            // Wait 3s between reconnect attempts
  reconnectAttempts: 5,               // Try 5 times before giving up
  onMessage: (data) => console.log(data),
  onOpen: () => console.log('Connected'),
  onClose: () => console.log('Disconnected'),
  onError: (error) => console.error(error)
})
```

## Benefits

1. **Lower Latency**: Changes appear instantly without polling delays
2. **Reduced Server Load**: No need for repeated HTTP requests
3. **Better UX**: Real-time feedback creates a more responsive feel
4. **Efficient**: Only sends data when changes occur
5. **Reliable**: Automatic reconnection handles network issues gracefully
