# Phase 03: Game Sessions & Team Mechanics

**Priority:** P1 (CRITICAL - Enables multiplayer gameplay)
**Status:** Pending
**Effort:** 30 hours (2 weeks)
**Dependencies:** Phase 1 (Leaderboard), Phase 2 (MT5 Integration)

## Context Links

- **Brainstorm:** `/plans/reports/brainstorm-251230-2302-multiplayer-trading-game.md` (Section 1 & 5)
- **Phase 1:** `./phase-01-leaderboard-infrastructure.md`
- **Phase 2:** `./phase-02-mt5-integration-service.md`
- **Existing Command Processor:** `backend/app/processors/command_processor.py`

## Overview

Implement `/csv` and `/jsv` commands for game session creation/joining with automatic team formation. Enables 5-10 players to compete in teams with session lifecycle management and team scoring aggregation.

**Goal:** Working multi-player game sessions with `/csv PanServer` and `/jsv PanServer` commands, team formation (4-6 players/team), and complete session lifecycle.

## Key Insights

1. **Session-Based Isolation** - Each game session independent, scoped by session_id
2. **Automatic Team Formation** - Round-robin allocation to balance teams
3. **Session Lifecycle** - waiting → active → completed states
4. **Team Scoring** - Aggregate P&L from all team members
5. **Command-Driven UX** - Chat commands for frictionless game entry

## Requirements

### Functional
- [ ] `/csv <ServerName>` creates new game session
- [ ] `/jsv <ServerName>` joins existing session
- [ ] Automatic team formation (4-6 players per team)
- [ ] Session lifecycle (waiting → active → completed)
- [ ] Team P&L aggregation for scoring
- [ ] Session start when minimum players joined

### Non-Functional
- [ ] Session creation < 100ms
- [ ] Join session < 200ms (including account allocation)
- [ ] Support 10 concurrent sessions
- [ ] Team auto-assignment < 50ms
- [ ] P&L aggregation < 100ms

## Architecture

### Session Lifecycle

```
┌──────────┐   /csv    ┌──────────┐  min players  ┌──────────┐
│ No       │──────────►│ WAITING  │──────────────►│ ACTIVE   │
│ Session  │           │ (< 4)    │  reached      │ (4+ play)│
└──────────┘           └──────────┘               └────┬─────┘
                                                       │
                                         end time or   │
                                         admin action  │
                                                       ▼
                                                ┌──────────┐
                                                │COMPLETED │
                                                └──────────┘
```

### Team Formation Strategy

```
Auto-Assign Algorithm (Round-Robin):
1. Get all teams in session (sorted by team_size ASC)
2. Find team with fewest members
3. If team_size < max_team_size (6):
     - Add player to that team
4. Else:
     - Create new team
     - Add player to new team

Result: Balanced teams (all teams ±1 member)
```

## Related Code Files

### Files to CREATE

1. **`backend/app/services/game_service.py`** - Session lifecycle
2. **`backend/app/services/team_service.py`** - Team formation & scoring
3. **`backend/app/processors/game_command_processor.py`** - `/csv`, `/jsv` commands

### Files to MODIFY

1. **`backend/app/processors/command_processor.py`** - Add game commands
2. **`backend/app/events/game_events.py`** - Add session events
3. **`backend/app/sio.py`** - Register session rooms

## Implementation Steps

### Week 1: Game Service & Commands (15h)

#### Step 1.1: Game Service (6h)

Create `backend/app/services/game_service.py`:

```python
"""Game session lifecycle management."""
from typing import Optional
import logging
from app.database.postgres_client import postgres_client
from app.models.game_models import GameSession
from app.services.mt5_integration_service import mt5_service

logger = logging.getLogger(__name__)

class GameService:
    """Manage game session lifecycle."""

    async def create_session(
        self,
        name: str,
        creator_id: str,
        max_team_size: int = 6
    ) -> GameSession:
        """
        Create new game session.

        Returns: GameSession
        Raises: Exception if name already exists
        """
        # Check name uniqueness
        existing = await postgres_client.fetchval(
            "SELECT COUNT(*) FROM game_sessions WHERE name = $1", name
        )

        if existing > 0:
            raise Exception(f"Session '{name}' already exists")

        # Create session
        row = await postgres_client.fetchrow("""
            INSERT INTO game_sessions (name, creator_id, max_team_size, status)
            VALUES ($1, $2, $3, 'waiting')
            RETURNING *
        """, name, creator_id, max_team_size)

        session = GameSession(**dict(row))
        logger.info(f"Created session '{name}' by {creator_id}")

        return session

    async def join_session(
        self,
        name: str,
        user_id: str,
        username: str
    ) -> dict:
        """
        Join existing game session.

        Returns: {"session": GameSession, "team": Team}
        Raises: Exception if session not found or full
        """
        # Get session
        session_row = await postgres_client.fetchrow(
            "SELECT * FROM game_sessions WHERE name = $1", name
        )

        if not session_row:
            raise Exception(f"Session '{name}' not found")

        session = GameSession(**dict(session_row))

        if session.status == "completed":
            raise Exception(f"Session '{name}' is completed")

        # Check if user already in session
        existing_membership = await postgres_client.fetchval("""
            SELECT COUNT(*) FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE t.session_id = $1 AND tm.user_id = $2
        """, session.session_id, user_id)

        if existing_membership > 0:
            raise Exception("You are already in this session")

        # Auto-assign to team
        from app.services.team_service import team_service
        team = await team_service.auto_assign_team(
            session.session_id,
            user_id,
            username,
            session.max_team_size
        )

        # Allocate MT5 account
        await mt5_service.allocate_account(user_id, session.session_id)

        # Check if we should start session (min 4 players)
        await self._check_start_session(session.session_id)

        logger.info(f"User {user_id} joined session '{name}', team '{team.team_name}'")

        return {
            "session": session,
            "team": team
        }

    async def leave_session(self, user_id: str):
        """Leave current game session."""
        # Find user's current session
        session_id = await postgres_client.fetchval("""
            SELECT t.session_id FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            JOIN game_sessions gs ON t.session_id = gs.session_id
            WHERE tm.user_id = $1 AND gs.status != 'completed'
        """, user_id)

        if not session_id:
            return

        # Release MT5 account
        await mt5_service.release_account(user_id)

        # Remove from team
        await postgres_client.execute(
            "DELETE FROM team_members WHERE user_id = $1", user_id
        )

        logger.info(f"User {user_id} left session {session_id}")

    async def get_session_by_name(self, name: str) -> Optional[GameSession]:
        """Get session by name."""
        row = await postgres_client.fetchrow(
            "SELECT * FROM game_sessions WHERE name = $1", name
        )
        return GameSession(**dict(row)) if row else None

    async def complete_session(self, session_id: str):
        """Mark session as completed."""
        await postgres_client.execute("""
            UPDATE game_sessions
            SET status = 'completed', end_time = NOW()
            WHERE session_id = $1
        """, session_id)

        logger.info(f"Session {session_id} completed")

    async def _check_start_session(self, session_id: str):
        """Start session if minimum players reached (4)."""
        player_count = await postgres_client.fetchval("""
            SELECT COUNT(DISTINCT tm.user_id)
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE t.session_id = $1
        """, session_id)

        if player_count >= 4:
            # Start session
            await postgres_client.execute("""
                UPDATE game_sessions
                SET status = 'active', start_time = NOW()
                WHERE session_id = $1 AND status = 'waiting'
            """, session_id)

            logger.info(f"Session {session_id} started with {player_count} players")

            # Broadcast session start
            from app.events.game_events import broadcast_session_start
            await broadcast_session_start(session_id)

# Global instance
game_service = GameService()
```

#### Step 1.2: Team Service (5h)

Create `backend/app/services/team_service.py`:

```python
"""Team formation and scoring."""
from typing import List
import logging
from decimal import Decimal
from app.database.postgres_client import postgres_client
from app.models.game_models import Team, TeamMember

logger = logging.getLogger(__name__)

class TeamService:
    """Team formation and scoring logic."""

    async def auto_assign_team(
        self,
        session_id: str,
        user_id: str,
        username: str,
        max_team_size: int
    ) -> Team:
        """
        Auto-assign user to team using round-robin.

        Strategy:
        1. Find team with fewest members
        2. If team_size < max, add to that team
        3. Else, create new team

        Returns: Team
        """
        # Find team with fewest members
        team_row = await postgres_client.fetchrow("""
            SELECT t.team_id, t.team_name, COUNT(tm.member_id) as member_count
            FROM teams t
            LEFT JOIN team_members tm ON t.team_id = tm.team_id
            WHERE t.session_id = $1
            GROUP BY t.team_id, t.team_name
            ORDER BY member_count ASC, t.created_at ASC
            LIMIT 1
        """, session_id)

        if team_row and team_row["member_count"] < max_team_size:
            # Add to existing team
            team_id = team_row["team_id"]
            team_name = team_row["team_name"]
        else:
            # Create new team
            team_count = await postgres_client.fetchval(
                "SELECT COUNT(*) FROM teams WHERE session_id = $1", session_id
            )

            # Get session name for team naming
            session_name = await postgres_client.fetchval(
                "SELECT name FROM game_sessions WHERE session_id = $1", session_id
            )

            # Team name = ServerName-Alpha, ServerName-Bravo, ...
            team_suffix = chr(65 + team_count)  # A, B, C...
            team_name = f"{session_name}-{team_suffix}"

            team_row = await postgres_client.fetchrow("""
                INSERT INTO teams (session_id, team_name)
                VALUES ($1, $2)
                RETURNING team_id, team_name
            """, session_id, team_name)

            team_id = team_row["team_id"]
            team_name = team_row["team_name"]

        # Add user to team
        await postgres_client.execute("""
            INSERT INTO team_members (team_id, user_id, username)
            VALUES ($1, $2, $3)
        """, team_id, user_id, username)

        logger.info(f"Assigned {username} to {team_name} in session {session_id}")

        return Team(
            team_id=str(team_id),
            session_id=session_id,
            team_name=team_name,
            total_pnl=Decimal("0"),
            created_at=team_row.get("created_at")
        )

    async def calculate_team_pnl(self, team_id: str) -> Decimal:
        """Calculate total P&L for team."""
        total = await postgres_client.fetchval("""
            SELECT COALESCE(SUM(p.pnl), 0)
            FROM positions p
            JOIN team_members tm ON p.user_id = tm.user_id
            WHERE tm.team_id = $1 AND p.closed_at IS NULL
        """, team_id)

        return Decimal(str(total))

    async def get_team_members(self, team_id: str) -> List[TeamMember]:
        """Get all team members."""
        rows = await postgres_client.fetch(
            "SELECT * FROM team_members WHERE team_id = $1", team_id
        )
        return [TeamMember(**dict(row)) for row in rows]

# Global instance
team_service = TeamService()
```

#### Step 1.3: Command Processor (4h)

Update `backend/app/processors/command_processor.py`:

```python
from app.services.game_service import game_service

class CommandProcessor:
    """Parse and execute chat commands."""

    COMMANDS = {
        "csv": "create_server",
        "jsv": "join_server",
        "close": "close_server",
        "top": "show_leaderboard"
    }

    async def create_server(self, user_id: str, args: str):
        """
        Handle /csv <ServerName>

        Example: /csv PanServer
        """
        if not args or len(args.strip()) == 0:
            return {
                "type": "error",
                "message": "Usage: /csv <ServerName>"
            }

        server_name = args.strip()

        try:
            session = await game_service.create_session(server_name, user_id)

            return {
                "type": "session_created",
                "session": session.dict(),
                "message": f"✅ Server '{server_name}' created! Share with friends: /jsv {server_name}"
            }

        except Exception as e:
            return {
                "type": "error",
                "message": str(e)
            }

    async def join_server(self, user_id: str, args: str):
        """
        Handle /jsv <ServerName>

        Example: /jsv PanServer
        """
        if not args or len(args.strip()) == 0:
            return {
                "type": "error",
                "message": "Usage: /jsv <ServerName>"
            }

        server_name = args.strip()
        username = await self._get_username(user_id)

        try:
            result = await game_service.join_session(
                server_name, user_id, username
            )

            return {
                "type": "session_joined",
                "session": result["session"].dict(),
                "team": result["team"].dict(),
                "message": f"✅ Joined '{server_name}'! Team: {result['team'].team_name}"
            }

        except Exception as e:
            return {
                "type": "error",
                "message": str(e)
            }

    async def close_server(self, user_id: str, args: str):
        """
        Handle /close command - Owner closes session.

        Example: /close
        """
        # Get user's current session
        session = await postgres_client.fetchrow("""
            SELECT gs.* FROM game_sessions gs
            JOIN teams t ON gs.session_id = t.session_id
            JOIN team_members tm ON t.team_id = tm.team_id
            WHERE tm.user_id = $1 AND gs.status != 'completed'
        """, user_id)

        if not session:
            return {
                "type": "error",
                "message": "You are not in an active session"
            }

        # Check if user is the creator
        if session["creator_id"] != user_id:
            return {
                "type": "error",
                "message": "Only the session creator can close the server"
            }

        # Close session
        await game_service.complete_session(str(session["session_id"]))

        return {
            "type": "session_closed",
            "session_id": str(session["session_id"]),
            "message": f"✅ Server '{session['name']}' closed! Final rankings saved."
        }

    async def _get_username(self, user_id: str) -> str:
        """Get username from user profile."""
        # TODO: Implement user profile lookup
        return user_id[:8]
```

### Week 2: Testing & Polish (15h)

#### Step 2.1: Socket.IO Session Events (4h)

Update `backend/app/events/game_events.py`:

```python
"""Game session Socket.IO events."""

async def broadcast_session_start(session_id: str):
    """Notify all players session has started."""
    await sio.emit("session:started", {
        "session_id": session_id,
        "message": "Game started! Trading is now active."
    }, room=f"session:{session_id}")

    logger.info(f"Broadcasted session start for {session_id}")

@sio.on("session:info")
async def handle_session_info(sid, data):
    """Get session information."""
    session_id = data.get("session_id")

    # Get session details
    session = await game_service.get_session_by_name(data.get("session_name"))

    if not session:
        await sio.emit("error", {"message": "Session not found"}, room=sid)
        return

    # Get teams
    teams = await postgres_client.fetch(
        "SELECT * FROM teams WHERE session_id = $1", session.session_id
    )

    await sio.emit("session:info_result", {
        "session": session.dict(),
        "teams": [dict(t) for t in teams],
        "player_count": len(teams) * 6  # Approx
    }, room=sid)
```

#### Step 2.2: Integration Tests (6h)

Create `backend/tests/test_game_session_flow.py`:

```python
"""End-to-end game session tests."""
import pytest

@pytest.mark.asyncio
async def test_create_and_join_session():
    """Test complete session creation and join flow."""
    # Create session
    result = await command_processor.parse_message(
        "user-1", "/csv TestServer"
    )

    assert result["type"] == "session_created"
    assert "TestServer" in result["message"]

    # Join session
    result = await command_processor.parse_message(
        "user-2", "/jsv TestServer"
    )

    assert result["type"] == "session_joined"
    assert result["team"]["team_name"] == "TestServer-A"

    # Join again (should create TestServer-B when TestServer-A full)
    for i in range(3, 8):  # Fill TestServer-A (6 players)
        await command_processor.parse_message(
            f"user-{i}", "/jsv TestServer"
        )

    # 8th player should get TestServer-B
    result = await command_processor.parse_message(
        "user-8", "/jsv TestServer"
    )
    assert result["team"]["team_name"] == "TestServer-B"

@pytest.mark.asyncio
async def test_session_auto_start():
    """Test session auto-starts at 4 players."""
    # Create and join
    await command_processor.parse_message("user-1", "/csv AutoStart")

    for i in range(2, 6):
        await command_processor.parse_message(f"user-{i}", "/jsv AutoStart")

    # Check session status
    session = await game_service.get_session_by_name("AutoStart")
    assert session.status == "active"
```

#### Step 2.3: Performance Tests (2h)

```python
"""Load tests for session creation."""
import asyncio

async def test_concurrent_session_creation():
    """Test 10 concurrent session creates."""
    tasks = [
        game_service.create_session(f"Session{i}", f"creator-{i}")
        for i in range(10)
    ]

    sessions = await asyncio.gather(*tasks)
    assert len(sessions) == 10

async def test_concurrent_joins():
    """Test 50 players joining same session."""
    await game_service.create_session("ConcurrentTest", "creator")

    tasks = [
        game_service.join_session("ConcurrentTest", f"user-{i}", f"User{i}")
        for i in range(50)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # First 10 should succeed (account pool limit)
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 10
```

#### Step 2.4: Documentation (3h)

Create `docs/game-session-guide.md`:

```markdown
# Game Session Guide

## Commands

### Create Server
```
/csv <ServerName>
```
Creates new game session. You become the creator.

### Join Server
```
/jsv <ServerName>
```
Joins existing session. Auto-assigned to balanced team.

### View Leaderboard
```
/top [limit]
```
Shows team rankings and your position.

## Session Lifecycle

1. **Waiting** - Fewer than 4 players
2. **Active** - 4+ players, trading enabled
3. **Completed** - Session ended

## Team Formation

- Automatic round-robin assignment
- 4-6 players per team
- Teams balanced by player count
- Team names: `ServerName-A`, `ServerName-B`, etc.

## Scoring

Team score = Sum of all member P&L (open positions)
```

## Todo Checklist

### Week 1: Services & Commands
- [ ] Implement GameService (create, join, leave)
- [ ] Implement TeamService (auto-assign, scoring)
- [ ] Add /csv command to CommandProcessor
- [ ] Add /jsv command to CommandProcessor
- [ ] Integrate MT5 account allocation on join
- [ ] Implement auto-start logic (4 players)

### Week 2: Testing & Polish
- [ ] Add Socket.IO session events
- [ ] Implement session:started broadcast
- [ ] Write integration tests
- [ ] Write performance tests
- [ ] Create user documentation
- [ ] Test full flow with real MT5 accounts

## Success Criteria

### Functional
- [ ] `/csv` creates new session
- [ ] `/jsv` joins and allocates MT5 account
- [ ] Teams balanced (all ±1 member)
- [ ] Session auto-starts at 4 players
- [ ] Team P&L aggregates correctly
- [ ] Session persists across restarts

### Performance
- [ ] Session creation < 100ms
- [ ] Join + allocate < 200ms
- [ ] Support 10 concurrent sessions
- [ ] Team assignment < 50ms

## Risk Assessment

**Session Name Collision** (LOW)
- Mitigation: Unique constraint on name
- Recovery: Error message to user

**Unbalanced Teams** (LOW)
- Mitigation: Round-robin algorithm
- Recovery: Manual rebalance (future)

**Session Orphaned** (MEDIUM)
- Mitigation: Cleanup task for old sessions
- Recovery: Manual completion

## Security

- **Session Isolation** - Users only see their session
- **Name Validation** - Alphanumeric + underscore only
- **Creator Privileges** - Only creator can end session (future)

## Next Steps

1. **Phase 4:** Achievement System (deferred from MVP)
2. **Phase 5:** Testing & Production Hardening
3. **Frontend:** React dashboard for session visualization

## Resolved Decisions

1. ✅ **Session Duration** - Owner manually closes session (no auto-complete)
2. ✅ **Team Naming** - Team name = Server name (all players one team per server)

## Unresolved Questions

1. **Session Privacy:** Public or invite-only sessions?
2. **Spectators:** Allow non-playing observers?
3. **Team Captain:** Assign team leader role?
