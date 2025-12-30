from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from contextlib import asynccontextmanager
import logging

from app.config import config
from app.logging_config import setup_logging
from app.mt5.connection_manager import MT5ConnectionManager
from app.session_manager import SessionManager
from app.reconnection_manager import ReconnectionManager
from app.processors.command_processor import CommandProcessor
from app.tasks.cleanup_task import CleanupTask
from app.database.redis_client import RedisClient
from app.processors.advisor_processor import AdvisorProcessor

# Initialize logging
logger = setup_logging(config.DEBUG)

# Global instances
mt5_manager = None
session_manager = None
reconnection_manager = None
command_processor = None
cleanup_task = None
redis_client = None
advisor_processor = None

from app.sio import sio

from app.events import trading_events
from app.events import advisor_events

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Initialize and cleanup resources
    """
    global mt5_manager, session_manager, reconnection_manager, command_processor, cleanup_task, redis_client, advisor_processor

    logger.info("Starting MT5 Socket.IO Trading Server...")

    # Initialize MT5 connection
    mt5_manager = MT5ConnectionManager(
        check_interval=config.HEALTH_CHECK_INTERVAL, # Kept original config variable
        timeout=config.CONNECTION_TIMEOUT # Kept original config variable
    )

    if not mt5_manager.connect():
        logger.error("Failed to connect to MT5 terminal")
        # In a real scenario, we might want to exit or retry,
        # but for now we'll continue to allow the server to start (for health check access)
        # raise RuntimeError("MT5 connection failed")

    logger.info("MT5 connection attempt finished")

    # Initialize session manager
    session_manager = SessionManager()
    
    # Initialize reconnection manager
    reconnection_manager = ReconnectionManager(session_ttl=300)  # 5 minutes
    logger.info("Reconnection manager initialized")

    # Initialize command processor
    command_processor = CommandProcessor(mt5_manager)

    # Initialize Redis
    redis_client = RedisClient(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB
    )
    if not await redis_client.connect():
        logger.warning("Redis not available - caching disabled")
        redis_client = None

    # Initialize Advisor Processor
    advisor_processor = AdvisorProcessor(mt5_manager, redis_client)

    # Start cleanup task
    cleanup_task = CleanupTask(reconnection_manager, interval=60)
    cleanup_task.start()

    # Inject dependencies into events module
    trading_events.mt5_manager = mt5_manager
    trading_events.session_manager = session_manager
    trading_events.reconnection_manager = reconnection_manager
    trading_events.command_processor = command_processor

    # Inject into advisor events
    advisor_events.advisor_processor = advisor_processor
    advisor_events.redis_client = redis_client

    # Store in app state (only mt5_manager is directly used by health check)
    app.state.mt5_manager = mt5_manager
    app.state.session_manager = session_manager # Kept for consistency, though events module now has it

    yield

    # Shutdown
    logger.info("Shutting down server...")

    if cleanup_task:
        await cleanup_task.stop()

    if redis_client:
        await redis_client.disconnect()

    if mt5_manager:
        mt5_manager.disconnect()
    logger.info("Server shutdown complete")

app = FastAPI(
    title="MT5 Trading Server",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mt5_manager and mt5_manager.is_connected() else "unhealthy",
        "mt5_connected": mt5_manager.is_connected() if mt5_manager else False,
        "redis_connected": await redis_client.is_connected() if redis_client else False,
        "connected_clients": len(session_manager.sessions) if session_manager else 0,
    }

# Wrap with Socket.IO
asgi_app = ASGIApp(sio, app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        asgi_app,
        host=config.SOCKETIO_HOST,
        port=config.SOCKETIO_PORT,
        log_level="debug" if config.DEBUG else "info"
    )
