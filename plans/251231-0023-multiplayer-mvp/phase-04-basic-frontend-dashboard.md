# Phase 04: Basic Frontend Dashboard

**Priority:** P2 (Post-MVP Enhancement)
**Status:** Pending
**Effort:** 20 hours (1-2 weeks sprint)
**Dependencies:** Phase 01 (Leaderboard), Phase 02 (MT5), Phase 03 (Game Sessions)

## Context Links

- **Phase 01:** `./phase-01-leaderboard-infrastructure.md`
- **Phase 02:** `./phase-02-mt5-integration-service.md`
- **Phase 03:** `./phase-03-game-sessions-teams.md`
- **Socket.IO Events:** `backend/app/events/game_events.py`

## Overview

Create minimal React dashboard for session management and real-time leaderboard visualization. **Focus: Essential UI only**, polish deferred to Phase 05.

**Goal:** Users can view sessions, join games, and see live leaderboard without CLI commands.

## Scope (Sprint-Focused)

### In Scope (MVP UI)
- ✅ Real-time leaderboard table
- ✅ Active sessions list
- ✅ Join session flow
- ✅ Session details view
- ✅ Socket.IO integration

### Out of Scope (Phase 05)
- ❌ Session creation UI (use /csv CLI)
- ❌ User authentication
- ❌ Team management UI
- ❌ Charts/graphs
- ❌ Achievement badges
- ❌ Responsive mobile design
- ❌ Animations/polish

## Key Features

### 1. Leaderboard Component

**Display:**
- Team rankings (rank, name, P&L, size)
- Current user's team highlighted
- Auto-updates via Socket.IO
- Simple table layout (no charts)

**Events:**
- `leaderboard:get` on mount
- `leaderboard:subscribe` for updates
- `leaderboard:update` real-time refresh

### 2. Session List Component

**Display:**
- Active sessions (name, status, player count)
- "Join" button per session
- Session status badges (waiting/active)

**Actions:**
- Click join → /jsv command
- View details → Session info modal

### 3. Session Details View

**Display:**
- Session name, status, creator
- Teams list with members
- Player count / max capacity

**Data Source:**
- `session:info` Socket.IO event

## Technical Stack

**Frontend:**
- React 18 (functional components)
- Socket.IO Client
- CSS Modules (no Tailwind/MUI for MVP)
- React hooks (useState, useEffect)

**Build:**
- Vite (fast dev server)
- No bundler optimization (defer to Phase 05)

**Integration:**
- Socket.IO: `http://localhost:8000`
- Event handlers: Reuse backend events

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Leaderboard.jsx
│   │   ├── SessionList.jsx
│   │   └── SessionDetails.jsx
│   ├── hooks/
│   │   └── useSocketIO.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── public/
├── package.json
└── vite.config.js
```

## Implementation Steps

### Week 1: Core Components (12h)

#### Step 1.1: Project Setup (2h)

```bash
# Create frontend directory
npm create vite@latest frontend -- --template react
cd frontend
npm install socket.io-client

# Configure Vite proxy to backend
```

**vite.config.js:**
```js
export default {
  server: {
    proxy: {
      '/socket.io': 'http://localhost:8000'
    }
  }
}
```

#### Step 1.2: Socket.IO Hook (2h)

**`src/hooks/useSocketIO.js`:**
```js
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export const useSocketIO = (url = 'http://localhost:8000') => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(url);

    socketInstance.on('connect', () => {
      setConnected(true);
    });

    socketInstance.on('disconnect', () => {
      setConnected(false);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [url]);

  return { socket, connected };
};
```

#### Step 1.3: Leaderboard Component (4h)

**`src/components/Leaderboard.jsx`:**
```jsx
import { useState, useEffect } from 'react';
import { useSocketIO } from '../hooks/useSocketIO';

export default function Leaderboard({ sessionId, userId }) {
  const { socket, connected } = useSocketIO();
  const [rankings, setRankings] = useState([]);
  const [myRank, setMyRank] = useState(null);

  useEffect(() => {
    if (!socket || !connected) return;

    // Get initial leaderboard
    socket.emit('leaderboard:get', {
      session_id: sessionId,
      limit: 10,
      user_id: userId
    });

    // Subscribe to updates
    socket.emit('leaderboard:subscribe', { session_id: sessionId });

    // Listen for results
    socket.on('leaderboard:result', (data) => {
      setRankings(data.rankings);
      setMyRank(data.my_rank);
    });

    // Listen for real-time updates
    socket.on('leaderboard:update', () => {
      // Refetch leaderboard
      socket.emit('leaderboard:get', {
        session_id: sessionId,
        limit: 10,
        user_id: userId
      });
    });

    return () => {
      socket.off('leaderboard:result');
      socket.off('leaderboard:update');
    };
  }, [socket, connected, sessionId, userId]);

  if (!connected) return <div>Connecting...</div>;

  return (
    <div className="leaderboard">
      <h2>Leaderboard</h2>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Team</th>
            <th>P&L</th>
            <th>Players</th>
          </tr>
        </thead>
        <tbody>
          {rankings.map((entry) => (
            <tr
              key={entry.team_id}
              className={myRank?.team_id === entry.team_id ? 'my-team' : ''}
            >
              <td>{entry.rank}</td>
              <td>{entry.team_name}</td>
              <td>${entry.total_pnl.toFixed(2)}</td>
              <td>{entry.team_size}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {myRank && (
        <div className="my-rank">
          Your Team: #{myRank.rank} - ${myRank.total_pnl.toFixed(2)}
        </div>
      )}
    </div>
  );
}
```

#### Step 1.4: Session List Component (4h)

**`src/components/SessionList.jsx`:**
```jsx
import { useState, useEffect } from 'react';
import { useSocketIO } from '../hooks/useSocketIO';

export default function SessionList({ userId, onJoinSession }) {
  const { socket, connected } = useSocketIO();
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    if (!socket || !connected) return;

    // TODO: Backend needs to implement list_sessions event
    // For MVP, hardcode session discovery via manual entry
  }, [socket, connected]);

  const handleJoin = (sessionName) => {
    if (!socket) return;

    socket.emit('game:join_session', {
      session_name: sessionName,
      user_id: userId
    });

    socket.once('game:session_joined', (data) => {
      if (data.success) {
        onJoinSession(data.session_id, sessionName);
      }
    });

    socket.once('error', (error) => {
      alert(`Join failed: ${error.message}`);
    });
  };

  return (
    <div className="session-list">
      <h2>Active Sessions</h2>
      <div className="session-entry">
        <input
          type="text"
          placeholder="Enter session name..."
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleJoin(e.target.value);
            }
          }}
        />
        <button onClick={(e) => {
          const input = e.target.previousElementSibling;
          handleJoin(input.value);
        }}>
          Join
        </button>
      </div>
    </div>
  );
}
```

### Week 2: Integration & Polish (8h)

#### Step 2.1: Main App Component (2h)

**`src/App.jsx`:**
```jsx
import { useState } from 'react';
import Leaderboard from './components/Leaderboard';
import SessionList from './components/SessionList';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [sessionName, setSessionName] = useState(null);
  const userId = 'demo-user-123'; // Hardcoded for MVP

  const handleJoinSession = (id, name) => {
    setSessionId(id);
    setSessionName(name);
  };

  return (
    <div className="app">
      <header>
        <h1>EV GamePad - Multi-Player Trading</h1>
        {sessionName && <div className="session-name">Session: {sessionName}</div>}
      </header>

      <div className="content">
        {sessionId ? (
          <Leaderboard sessionId={sessionId} userId={userId} />
        ) : (
          <SessionList userId={userId} onJoinSession={handleJoinSession} />
        )}
      </div>
    </div>
  );
}

export default App;
```

#### Step 2.2: Basic Styling (2h)

**`src/App.css`:**
```css
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, sans-serif;
}

header {
  border-bottom: 2px solid #333;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.leaderboard table {
  width: 100%;
  border-collapse: collapse;
}

.leaderboard th,
.leaderboard td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.leaderboard .my-team {
  background-color: #ffffcc;
  font-weight: bold;
}

.my-rank {
  margin-top: 20px;
  padding: 10px;
  background-color: #e7f3ff;
  border-left: 4px solid #2196F3;
}

.session-entry {
  display: flex;
  gap: 10px;
}

.session-entry input {
  flex: 1;
  padding: 10px;
  font-size: 16px;
}

.session-entry button {
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
}
```

#### Step 2.3: Error Handling (2h)

Add error states:
- Connection lost indicator
- Join session errors
- Empty state messages

#### Step 2.4: Testing & Documentation (2h)

**Manual Testing:**
1. Start backend server
2. Create session via CLI: `/csv TestSession`
3. Open dashboard: `npm run dev`
4. Join session via UI
5. Verify leaderboard updates

**Update README:**
```markdown
# Frontend Dashboard

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Usage

1. Enter session name (created via CLI)
2. Click "Join"
3. View real-time leaderboard
```

## Success Criteria

### Functional
- [ ] Leaderboard displays top 10 teams
- [ ] Real-time updates on P&L change
- [ ] Join session via UI
- [ ] Current user's team highlighted
- [ ] Socket.IO connection status visible

### Performance
- [ ] Initial render < 1s
- [ ] Leaderboard update < 100ms
- [ ] No memory leaks (Socket.IO cleanup)

### Quality
- [ ] No console errors
- [ ] Socket.IO events properly unsubscribed
- [ ] Basic error handling (join failures)

## Out of Scope (Deferred)

1. **Session Creation UI** - Use CLI `/csv` command
2. **User Authentication** - Hardcoded user ID
3. **Mobile Responsive** - Desktop only
4. **Team Management** - View only, no controls
5. **Charts/Graphs** - Table display only
6. **Session Discovery** - Manual name entry

## Next Steps (Phase 05)

1. Add session creation form
2. Implement user authentication
3. Add charts (P&L over time)
4. Mobile responsive design
5. Achievement badges
6. Session discovery/search

## Risk Assessment

**Low Complexity** - Minimal UI, leverages existing backend
**Timeline Risk** - 1-2 weeks achievable for basic dashboard
**Blocker** - Backend must be running for frontend to work

## Unresolved Questions

1. **User ID** - How to get real user ID? (Hardcoded for MVP)
2. **Session Discovery** - Manual entry sufficient? (Yes for MVP)
3. **Deployment** - Separate frontend server or serve from backend? (Separate for now)
