# WebSocket Real-Time Portfolio Tracking

## Overview

The Analytics page now supports real-time WebSocket updates for live portfolio tracking. This enables instant updates when trades execute or portfolio values change, without requiring manual page refreshes.

## Features

### Real-Time Updates
- **Portfolio Updates**: Instant updates when portfolio positions or values change
- **Trade Execution**: Live notifications when new trades are executed
- **Performance Metrics**: Real-time performance data updates

### Connection Management
- **Auto-Connect**: Optional WebSocket connection with toggle control
- **Auto-Reconnect**: Automatic reconnection attempts (up to 5 times) with 3-second intervals
- **Status Indicator**: Visual indicator showing connection status (Connected/Connecting/Disconnected/Error)
- **Toast Notifications**: User-friendly notifications for connection events

## Usage

### Enabling WebSocket
1. Navigate to the Analytics page
2. Find the "Real-time" toggle in the top controls area
3. Click the toggle to enable WebSocket connection
4. Connection status will be displayed next to the data source badge

### Connection States
- **Connected** (Green pulsing dot + "Live"): WebSocket is connected and receiving updates
- **Connecting** (Yellow pulsing dot + "Connecting"): WebSocket is establishing connection
- **Disconnected** (Red dot + "Disconnected"): WebSocket is not connected
- **Error** (Red dot + "Error"): WebSocket encountered an error

### Visual Indicators
- **Wifi Icon**: Shows WiFi signal icon when enabled, WiFi slash when disabled
- **Status Dot**: Animated color-coded dot indicating connection state
- **Data Source Badge**: Shows "Live Data" or "Mock Data" depending on source
- **Last Updated**: Timestamp showing when data was last refreshed

## Backend Integration

### WebSocket Endpoint
The frontend connects to: `ws://localhost:8000/api/v1/ws/analytics`

For HTTPS backends, it automatically uses: `wss://[domain]/api/v1/ws/analytics`

### Expected Message Format

The WebSocket expects JSON messages with a `type` field:

#### Portfolio Update
```json
{
  "type": "portfolio_update",
  "portfolio": [
    {
      "symbol": "BTC",
      "quantity": 1.5,
      "avg_price": 45000,
      "current_price": 47000,
      "value": 70500,
      "pnl": 3000,
      "pnl_percent": 6.67,
      "allocation": 65.5
    }
  ]
}
```

#### Trade Executed
```json
{
  "type": "trade_executed",
  "trade": {
    "id": "trade_123",
    "timestamp": "2024-01-15T10:30:00Z",
    "symbol": "ETH",
    "type": "buy",
    "quantity": 10,
    "price": 2500,
    "pnl": 0,
    "status": "completed"
  }
}
```

#### Performance Update
```json
{
  "type": "performance_update",
  "performance": [
    {
      "date": "2024-01-15",
      "pnl": 5000,
      "daily_pnl": 250,
      "value": 105000
    }
  ]
}
```

## Implementation Details

### Custom Hook: `useWebSocket`

Located in `/src/hooks/use-websocket.ts`, this hook provides:

- **Automatic connection management**: Handles WebSocket lifecycle
- **Reconnection logic**: Automatic retry with configurable attempts and intervals
- **Message parsing**: Automatic JSON parsing of incoming messages
- **Status tracking**: Returns current connection status
- **Callback handlers**: Supports onMessage, onOpen, onClose, onError callbacks

#### Hook Usage
```typescript
const { status, send, disconnect, reconnect, reconnectAttempts } = useWebSocket('/ws/analytics', {
  enabled: true,
  onMessage: (data) => {
    // Handle incoming data
  },
  onOpen: () => {
    console.log('WebSocket connected')
  },
  onClose: () => {
    console.log('WebSocket disconnected')
  },
  onError: (error) => {
    console.error('WebSocket error:', error)
  },
  reconnectInterval: 3000,      // Reconnect every 3 seconds
  maxReconnectAttempts: 5,       // Try up to 5 times
})
```

### Message Handling

The Analytics page processes three types of WebSocket messages:

1. **portfolio_update**: Updates the entire portfolio state
2. **trade_executed**: Adds a new trade to the trades list and shows a toast notification
3. **performance_update**: Updates the performance metrics data

All updates automatically refresh the "Last Updated" timestamp.

## Configuration

### Environment Variables
The WebSocket URL is derived from the API base URL:
- Set `VITE_API_BASE_URL` in your `.env` file
- Default: `http://localhost:8000`

Example:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Reconnection Settings
To modify reconnection behavior, update the `useWebSocket` call in `analytics-page.tsx`:

```typescript
const { status: wsStatus } = useWebSocket('/ws/analytics', {
  enabled: wsEnabled,
  reconnectInterval: 5000,        // Change to 5 seconds
  maxReconnectAttempts: 10,       // Try up to 10 times
  // ... other options
})
```

## Backend Implementation Guide

To implement the WebSocket server on the backend:

### FastAPI Example

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/api/v1/ws/analytics")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Example: Broadcasting portfolio update
async def broadcast_portfolio_update(portfolio_data):
    await manager.broadcast({
        "type": "portfolio_update",
        "portfolio": portfolio_data
    })
```

## Troubleshooting

### WebSocket Won't Connect
1. Verify backend WebSocket endpoint is running at `/api/v1/ws/analytics`
2. Check browser console for WebSocket errors
3. Ensure CORS is properly configured on backend
4. Verify `VITE_API_BASE_URL` environment variable is correct

### Connection Keeps Dropping
1. Check backend server logs for errors
2. Verify network stability
3. Increase `maxReconnectAttempts` in hook configuration
4. Consider implementing heartbeat/ping-pong mechanism on backend

### Updates Not Appearing
1. Verify WebSocket messages match expected format
2. Check browser console for parsing errors
3. Ensure message `type` field is one of: `portfolio_update`, `trade_executed`, `performance_update`
4. Verify data structure matches expected schema (snake_case or camelCase)

## Performance Considerations

- **Message Frequency**: Avoid sending updates more frequently than once per second to prevent UI thrashing
- **Batch Updates**: Consider batching multiple small updates into a single message
- **State Management**: The component uses functional updates to prevent race conditions
- **Memory**: WebSocket connection is automatically cleaned up when component unmounts or toggle is disabled

## Future Enhancements

Potential improvements for future iterations:

1. **Selective Subscriptions**: Allow users to subscribe to specific symbols or metrics
2. **Historical Playback**: WebSocket-based playback of historical trading data
3. **Order Book Updates**: Real-time order book depth updates
4. **Price Alerts**: WebSocket-based price alert notifications
5. **Heartbeat Monitoring**: Implement ping/pong for connection health
6. **Compression**: Enable WebSocket compression for large data payloads
