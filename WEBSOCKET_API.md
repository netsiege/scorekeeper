# WebSocket API Documentation

The scorekeeper API has been converted from REST endpoints to WebSocket events. The server automatically maps client IP addresses to hostnames based on the phase configuration.

## Connection

Connect to the WebSocket server at: `ws://server:8000`

Upon connection, you'll receive a `connection_established` event with your hostname mapping.

## IP-to-Hostname Mapping

The server automatically determines your hostname based on your IP address by looking it up in the phase configuration file (e.g., `config/phase1.yml`). No need to specify your hostname in most requests!

## Events

### Client → Server Events

#### `get_boxes`
Get all boxes information.
```javascript
socket.emit('get_boxes');
```
Response: `boxes_data` event with array of box objects

#### `get_teams`
Get all teams information.
```javascript
socket.emit('get_teams');
```
Response: `teams_data` event with array of team objects

#### `get_tasks`
Get pending tasks for your box (determined by your IP).
```javascript
socket.emit('get_tasks');
// Or optionally override with explicit hostname:
socket.emit('get_tasks', { hostname: 'hera' });
```
Response: `tasks_data` event with:
```json
{
  "hostname": "hera",
  "ip": "10.77.77.54",
  "tasks": [...]
}
```

#### `rotate_key`
Queue a rotate_key task for your box (determined by your IP).
```javascript
socket.emit('rotate_key');
// Or optionally override with explicit hostname:
socket.emit('rotate_key', { hostname: 'hera' });
```
Response: `rotate_key_response` event

#### `submit_claim`
Submit a claim and award points (box determined by your IP).
```javascript
socket.emit('submit_claim', {
  token: 'team_token_here',
  file_path: '/root/claim.txt',  // Optional: specific file path
  task_type: 'check_control'     // Optional: task type
});
```
Response: `claim_response` event with:
```json
{
  "message": "Claim submitted successfully",
  "hostname": "hera",
  "ip": "10.77.77.54",
  "team_id": 1,
  "claim": {...},
  "task_removed": true,
  "points_awarded": 3
}
```

#### `get_all_tasks`
Get all task queues for all boxes (admin use).
```javascript
socket.emit('get_all_tasks');
```
Response: `all_tasks_data` event with all queues

### Server → Client Events

- `connection_established` - Sent when client connects
- `boxes_data` - Response to `get_boxes`
- `teams_data` - Response to `get_teams`
- `tasks_data` - Response to `get_tasks`
- `rotate_key_response` - Response to `rotate_key`
- `claim_response` - Response to `submit_claim`
- `all_tasks_data` - Response to `get_all_tasks`
- `error` - Error messages

## Python Client Example

```python
import socketio

sio = socketio.Client()

@sio.on('connection_established')
def on_connect(data):
    print(f"Connected as {data['hostname']} from IP {data['ip']}")

@sio.on('tasks_data')
def on_tasks(data):
    print(f"Tasks for {data['hostname']}: {data['tasks']}")

@sio.on('claim_response')
def on_claim_response(data):
    print(f"Claim result: {data['message']}, Points: {data['points_awarded']}")

@sio.on('error')
def on_error(data):
    print(f"Error: {data['message']}")

# Connect to server
sio.connect('http://server:8000')

# Get tasks for this box
sio.emit('get_tasks')

# Submit a claim
sio.emit('submit_claim', {
    'token': 'your_team_token',
    'file_path': '/root/claim.txt'
})

# Keep connection alive
sio.wait()
```

## Migration from REST API

| Old REST Endpoint | New WebSocket Event | Notes |
|-------------------|---------------------|-------|
| `GET /api/boxes` | `get_boxes` | Same response format |
| `GET /api/teams` | `get_teams` | Same response format |
| `GET /api/tasks?hostname=X` | `get_tasks` | Hostname now auto-detected from IP |
| `POST /api/rotate_key?hostname=X` | `rotate_key` | Hostname now auto-detected from IP |
| `POST /api/claim?hostname=X` | `submit_claim` | Hostname now auto-detected from IP |
| `GET /api/tasks/all` | `get_all_tasks` | Same response format |

## Key Changes

1. **No hostname parameter required**: The server automatically determines your hostname from your IP address
2. **Event-based communication**: Instead of HTTP requests/responses, use emit/on pattern
3. **Persistent connection**: Maintains a WebSocket connection instead of creating new HTTP connections
4. **Real-time updates possible**: Server can push updates to clients without polling
