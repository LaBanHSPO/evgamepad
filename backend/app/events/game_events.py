"""Socket.IO event handlers for game sessions and leaderboard."""
import logging
from app.sio import sio
from app.services.leaderboard_service import leaderboard_service
from decimal import Decimal

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
