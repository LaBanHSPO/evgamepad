"""Socket.IO event handlers for game sessions and leaderboard."""
import logging
from app.sio import sio
from app.services.leaderboard_service import leaderboard_service
from app.services.mt5_integration_service import mt5_integration_service
from app.database.postgres_client import postgres_client
from app.models.mt5_models import OrderType
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

@sio.on("leaderboard:get")
async def handle_get_leaderboard(sid, data):
    """
    Client requests leaderboard via /top command.

    Request:
    {
        "session_id": "uuid",
        "limit": 10,  # optional, default 10
        "user_id": "user_identifier"
    }

    Response:
    {
        "rankings": [
            {"rank": 1, "team_name": "Team Alpha", "total_pnl": 2500.00, ...},
            ...
        ],
        "my_rank": {"rank": 3, "team_name": "My Team", ...},
        "total_teams": 5
    }
    """
    try:
        session_id = data.get("session_id")
        limit = data.get("limit", 10)
        user_id = data.get("user_id")

        # Get rankings
        rankings = await leaderboard_service.get_leaderboard(session_id, limit)

        # Get my rank
        my_rank = await leaderboard_service.get_my_rank(session_id, user_id) if user_id else None

        # Total teams
        total_teams = await leaderboard_service.get_total_teams(session_id)

        await sio.emit("leaderboard:result", {
            "rankings": [r.dict() for r in rankings],
            "my_rank": my_rank.dict() if my_rank else None,
            "total_teams": total_teams
        }, room=sid)

        logger.info(f"Leaderboard sent to {sid} for session {session_id}")

    except Exception as e:
        logger.error(f"Error handling leaderboard:get: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.on("leaderboard:subscribe")
async def handle_subscribe_leaderboard(sid, data):
    """Subscribe to real-time leaderboard updates for a session."""
    try:
        session_id = data.get("session_id")

        # Join session room for broadcasts
        sio.enter_room(sid, f"session:{session_id}")

        logger.info(f"Client {sid} subscribed to session {session_id}")

        await sio.emit("leaderboard:subscribed", {
            "session_id": session_id,
            "message": "Subscribed to real-time updates"
        }, room=sid)

    except Exception as e:
        logger.error(f"Error handling leaderboard:subscribe: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

async def broadcast_leaderboard_update(session_id: str, team_id: str, new_pnl: Decimal):
    """
    Broadcast leaderboard update to all clients in session.
    Called after P&L change.
    """
    try:
        # Get updated rank
        rankings = await leaderboard_service.get_leaderboard(session_id, limit=1)

        if rankings and rankings[0].team_id == team_id:
            # Team is now #1
            await sio.emit("leaderboard:update", {
                "session_id": session_id,
                "team_id": team_id,
                "new_pnl": float(new_pnl),
                "new_rank": 1,
                "message": f"{rankings[0].team_name} is now #1!"
            }, room=f"session:{session_id}")
        else:
            # Regular update
            await sio.emit("leaderboard:update", {
                "session_id": session_id,
                "team_id": team_id,
                "new_pnl": float(new_pnl)
            }, room=f"session:{session_id}")

        logger.debug(f"Broadcasted leaderboard update for session {session_id}")

    except Exception as e:
        logger.error(f"Error broadcasting leaderboard update: {e}")

# ============= GAME SESSION MANAGEMENT (Phase 02) =============

@sio.on("game:create_session")
async def handle_create_session(sid, data):
    """
    Create new game session via /csv command.

    Request:
    {
        "session_name": "MyGameSession",
        "user_id": "user_123",
        "team_name": "Team Alpha",
        "max_team_size": 6  # optional
    }

    Response:
    {
        "success": true,
        "session_id": "uuid",
        "team_id": "uuid",
        "account_allocated": {
            "account_number": 12345,
            "broker_server": "BrokerDemo"
        }
    }
    """
    try:
        session_name = data.get("session_name")
        user_id = data.get("user_id")
        team_name = data.get("team_name")
        max_team_size = data.get("max_team_size", 6)

        # Validate inputs
        if not session_name or not user_id or not team_name:
            await sio.emit("error", {
                "message": "Missing required fields: session_name, user_id, team_name"
            }, room=sid)
            return

        # Create game session
        session_query = """
            INSERT INTO game_sessions (name, creator_id, status, max_team_size)
            VALUES ($1, $2, 'waiting', $3)
            RETURNING session_id
        """

        session_result = await postgres_client.fetchrow(
            session_query,
            session_name,
            user_id,
            max_team_size
        )

        if not session_result:
            await sio.emit("error", {"message": "Failed to create session"}, room=sid)
            return

        session_id = str(session_result['session_id'])

        # Create team
        team_query = """
            INSERT INTO teams (session_id, name)
            VALUES ($1, $2)
            RETURNING team_id
        """

        team_result = await postgres_client.fetchrow(team_query, session_id, team_name)
        team_id = str(team_result['team_id'])

        # Add user to team
        member_query = """
            INSERT INTO team_members (team_id, user_id)
            VALUES ($1, $2)
        """

        await postgres_client.execute(member_query, team_id, user_id)

        # Allocate MT5 account to user (Phase 02)
        account_allocation = await mt5_integration_service.allocate_account(user_id)

        if not account_allocation:
            await sio.emit("game:session_created", {
                "success": True,
                "session_id": session_id,
                "team_id": team_id,
                "warning": "No MT5 account available - pool exhausted"
            }, room=sid)
            logger.warning(f"Session created but account pool exhausted for {user_id}")
            return

        # CRITICAL FIX: Ensure account is released if anything fails
        try:
            # Join session room for broadcasts
            sio.enter_room(sid, f"session:{session_id}")

            await sio.emit("game:session_created", {
                "success": True,
                "session_id": session_id,
                "team_id": team_id,
                "account_allocated": {
                    "account_number": account_allocation.account_number,
                    "broker_server": account_allocation.broker_server
                }
            }, room=sid)

            logger.info(f"Session {session_id} created by {user_id}, account {account_allocation.account_number} allocated")

        except Exception as emit_error:
            # Release account if emission failed to prevent leak
            await mt5_integration_service.release_account(user_id)
            logger.error(f"Failed to emit session_created, account released: {emit_error}")
            raise

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.on("game:join_session")
async def handle_join_session(sid, data):
    """
    Join existing game session via /jsv command.

    Request:
    {
        "session_name": "MyGameSession",
        "user_id": "user_456",
        "team_name": "Team Beta"  # optional - join existing or create new
    }

    Response:
    {
        "success": true,
        "session_id": "uuid",
        "team_id": "uuid",
        "account_allocated": {...}
    }
    """
    try:
        session_name = data.get("session_name")
        user_id = data.get("user_id")
        team_name = data.get("team_name")  # Optional

        if not session_name or not user_id:
            await sio.emit("error", {
                "message": "Missing required fields: session_name, user_id"
            }, room=sid)
            return

        # Find session
        session_query = """
            SELECT session_id, status
            FROM game_sessions
            WHERE name = $1
        """

        session_result = await postgres_client.fetchrow(session_query, session_name)

        if not session_result:
            await sio.emit("error", {"message": f"Session '{session_name}' not found"}, room=sid)
            return

        session_id = str(session_result['session_id'])
        session_status = session_result['status']

        if session_status == 'completed':
            await sio.emit("error", {"message": "Session already completed"}, room=sid)
            return

        # Find or create team
        if team_name:
            # Try to find existing team
            team_query = """
                SELECT team_id FROM teams
                WHERE session_id = $1 AND name = $2
            """
            team_result = await postgres_client.fetchrow(team_query, session_id, team_name)

            if team_result:
                team_id = str(team_result['team_id'])
            else:
                # Create new team
                create_team_query = """
                    INSERT INTO teams (session_id, name)
                    VALUES ($1, $2)
                    RETURNING team_id
                """
                new_team = await postgres_client.fetchrow(create_team_query, session_id, team_name)
                team_id = str(new_team['team_id'])
        else:
            # Join first available team with space
            team_query = """
                SELECT t.team_id
                FROM teams t
                LEFT JOIN team_members tm ON t.team_id = tm.team_id
                WHERE t.session_id = $1
                GROUP BY t.team_id
                HAVING COUNT(tm.user_id) < (
                    SELECT max_team_size FROM game_sessions WHERE session_id = $1
                )
                LIMIT 1
            """
            team_result = await postgres_client.fetchrow(team_query, session_id)

            if team_result:
                team_id = str(team_result['team_id'])
            else:
                await sio.emit("error", {"message": "All teams full"}, room=sid)
                return

        # Add user to team
        member_query = """
            INSERT INTO team_members (team_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """
        await postgres_client.execute(member_query, team_id, user_id)

        # Allocate MT5 account (Phase 02)
        account_allocation = await mt5_integration_service.allocate_account(user_id)

        if not account_allocation:
            await sio.emit("game:session_joined", {
                "success": True,
                "session_id": session_id,
                "team_id": team_id,
                "warning": "No MT5 account available"
            }, room=sid)
            return

        # CRITICAL FIX: Ensure account is released if anything fails
        try:
            # Join session room
            sio.enter_room(sid, f"session:{session_id}")

            await sio.emit("game:session_joined", {
                "success": True,
                "session_id": session_id,
                "team_id": team_id,
                "account_allocated": {
                    "account_number": account_allocation.account_number,
                    "broker_server": account_allocation.broker_server
                }
            }, room=sid)

            logger.info(f"User {user_id} joined session {session_id}, account {account_allocation.account_number} allocated")

        except Exception as emit_error:
            # Release account if emission failed to prevent leak
            await mt5_integration_service.release_account(user_id)
            logger.error(f"Failed to emit session_joined, account released: {emit_error}")
            raise

    except Exception as e:
        logger.error(f"Error joining session: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.on("game:leave_session")
async def handle_leave_session(sid, data):
    """
    Leave game session and release MT5 account.

    Request:
    {
        "user_id": "user_123"
    }
    """
    try:
        user_id = data.get("user_id")

        if not user_id:
            await sio.emit("error", {"message": "Missing user_id"}, room=sid)
            return

        # Release MT5 account (Phase 02)
        released = await mt5_integration_service.release_account(user_id)

        if released:
            await sio.emit("game:session_left", {
                "success": True,
                "message": "MT5 account released"
            }, room=sid)
            logger.info(f"User {user_id} left session, account released")
        else:
            await sio.emit("game:session_left", {
                "success": True,
                "message": "No account to release"
            }, room=sid)

    except Exception as e:
        logger.error(f"Error leaving session: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

# ============= TRADING EXECUTION (Phase 02) =============

@sio.on("trade:execute")
async def handle_execute_trade(sid, data):
    """
    Execute trade on MT5 via allocated account.

    Request:
    {
        "user_id": "user_123",
        "symbol": "EURUSD",
        "side": "BUY" | "SELL",
        "volume": 0.1,
        "sl": 1.0500,  # optional
        "tp": 1.1000   # optional
    }

    Response:
    {
        "order_id": 123456,
        "symbol": "EURUSD",
        "side": "BUY",
        "volume": 0.1,
        "price": 1.0850,
        "retcode": 10009,
        "comment": "Done"
    }
    """
    try:
        user_id = data.get("user_id")
        symbol = data.get("symbol")
        side = data.get("side", "BUY").upper()
        volume = data.get("volume")
        sl = data.get("sl")
        tp = data.get("tp")

        # Validate required fields
        if not all([user_id, symbol, side, volume]):
            await sio.emit("error", {
                "message": "Missing required fields: user_id, symbol, side, volume"
            }, room=sid)
            return

        # Convert volume to Decimal
        try:
            volume = Decimal(str(volume))
            sl = Decimal(str(sl)) if sl else None
            tp = Decimal(str(tp)) if tp else None
        except (ValueError, TypeError):
            await sio.emit("trade:error", {
                "message": "Invalid numeric values for volume/sl/tp"
            }, room=sid)
            return

        # Get user's session
        session_query = """
            SELECT gs.session_id
            FROM game_sessions gs
            JOIN teams t ON t.session_id = gs.session_id
            JOIN team_members tm ON tm.team_id = t.team_id
            WHERE tm.user_id = $1 AND gs.status = 'active'
            LIMIT 1
        """
        session_result = await postgres_client.fetchrow(session_query, user_id)

        if not session_result:
            await sio.emit("trade:error", {
                "message": "Not in active game session"
            }, room=sid)
            return

        session_id = str(session_result['session_id'])

        # Execute order
        order_type = OrderType.BUY if side == "BUY" else OrderType.SELL
        result = await mt5_integration_service.execute_order(
            session_id=session_id,
            user_id=user_id,
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            sl=sl,
            tp=tp
        )

        if result.get('success'):
            await sio.emit("trade:executed", {
                "order_id": result.get('order'),
                "symbol": symbol,
                "side": side,
                "volume": float(volume),
                "price": result.get('price'),
                "retcode": result.get('retcode'),
                "comment": result.get('comment')
            }, room=sid)

            # Broadcast to session for real-time leaderboard update
            await sio.emit("trade:broadcast", {
                "user_id": user_id,
                "symbol": symbol,
                "side": side,
                "volume": float(volume)
            }, room=f"session:{session_id}")

            logger.info(f"Trade executed: {user_id} {side} {volume} {symbol}")
        else:
            await sio.emit("trade:error", {
                "message": result.get('error', 'Order execution failed'),
                "retcode": result.get('retcode')
            }, room=sid)

    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        await sio.emit("trade:error", {"message": str(e)}, room=sid)
