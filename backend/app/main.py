from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from contextlib import asynccontextmanager
import logging
import asyncio

from app.config import config
from app.logging_config import setup_logging
from app.database.redis_client import RedisClient
from app.database.postgres_client import postgres_client
from app.mt5.connection_manager import MT5ConnectionManager

from app.session_manager import SessionManager
from app.reconnection_manager import ReconnectionManager
from app.processors.command_processor import CommandProcessor
from app.tasks.cleanup_task import CleanupTask

from app.processors.advisor_processor import AdvisorProcessor
from app.tasks.leaderboard_refresh_task import leaderboard_refresh_task
from app.services.leaderboard_service import leaderboard_service
from app.services.mt5_integration_service import mt5_integration_service
from app.tasks.mt5_position_sync_task import mt5_position_sync_task
from app.tasks.mt5_health_check_task import mt5_health_check_task
from app.database.pool_manager import DatabasePoolManager
from app.processors.advisor_processor import AdvisorProcessor
from app.processors.kol_processor import KOLProcessor
from app.advisor.accuracy_tracker import AccuracyTracker
from app.advisor.mt5_history_parser import MT5HistoryParser

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
db_pool_manager = None  # Phase 5.2: PostgreSQL pool
accuracy_tracker = None  # Phase 5.2: Accuracy tracking
mt5_history_parser = None  # Phase 5.2: MT5 auto-detection
mt5_sync_task = None  # Phase 5.2: Background sync task
kol_processor = None  # Phase 6: KOL message processor

from app.sio import sio

from app.events import trading_events
from app.events import advisor_events
from app.events import game_events

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Initialize and cleanup resources
    """
    global mt5_manager, session_manager, reconnection_manager, command_processor, cleanup_task, redis_client, advisor_processor, db_pool_manager, accuracy_tracker, mt5_history_parser, mt5_sync_task, kol_processor

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

    # Initialize PostgreSQL (Phase 01 - Leaderboard Infrastructure)
    try:
        await postgres_client.initialize()
        # Initialize leaderboard service with Redis client
        leaderboard_service.redis_client = redis_client
        # Start leaderboard refresh task
        asyncio.create_task(leaderboard_refresh_task.start())
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")
        logger.warning("Leaderboard features will be unavailable")

    # Initialize MT5 Integration Service (Phase 02 - MT5 Integration Service)
    try:
        await mt5_integration_service.initialize()
        # Start position sync task (5s interval)
        asyncio.create_task(mt5_position_sync_task.start())
        # Start health check task (10s interval)
        asyncio.create_task(mt5_health_check_task.start())
        logger.info("MT5 integration service and background tasks started")
    except Exception as e:
        logger.error(f"MT5 integration service initialization failed: {e}")
        logger.warning("MT5 trading features will be unavailable")
    # Initialize PostgreSQL pool (Phase 5.2)
    if config.ENABLE_ACCURACY_TRACKING:
        db_pool_manager = DatabasePoolManager(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            min_size=config.POSTGRES_MIN_POOL_SIZE,
            max_size=config.POSTGRES_MAX_POOL_SIZE
        )
        if await db_pool_manager.connect():
            logger.info("PostgreSQL pool initialized for accuracy tracking")

            # Initialize accuracy tracker
            accuracy_tracker = AccuracyTracker(db_pool_manager.get_pool())
            logger.info("Accuracy tracker initialized")

            # Initialize MT5 history parser
            mt5_history_parser = MT5HistoryParser(
                mt5_manager,
                accuracy_tracker,
                db_pool_manager.get_pool()
            )
            logger.info("MT5 history parser initialized")

            # Start background MT5 sync task
            async def mt5_sync_loop():
                """Background task to sync MT5 closed positions every 5 minutes."""
                while True:
                    try:
                        await asyncio.sleep(300)  # 5 minutes
                        result = await mt5_history_parser.sync_closed_positions(days_back=7)
                        logger.info(f"MT5 sync completed: {result}")
                    except Exception as e:
                        logger.exception(f"MT5 sync failed: {e}")

            mt5_sync_task = asyncio.create_task(mt5_sync_loop())
            logger.info("MT5 sync background task started (5-minute interval)")
        else:
            logger.warning("PostgreSQL connection failed - accuracy tracking disabled")
            db_pool_manager = None
    else:
        logger.info("Accuracy tracking disabled (ENABLE_ACCURACY_TRACKING=false)")

    # Initialize KOL Processor (Phase 6: KOL Updates MVP)
    if db_pool_manager:
        kol_processor = KOLProcessor(db_pool_manager, sio)
        logger.info("KOL processor initialized")

        # Inject processor into router
        from app.routers import kol_router
        kol_router.set_kol_processor(kol_processor)
    else:
        logger.warning("KOL processor disabled - database not available")

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
    advisor_events.accuracy_tracker = accuracy_tracker  # Phase 5.2

    # Store in app state (only mt5_manager is directly used by health check)
    app.state.mt5_manager = mt5_manager
    app.state.session_manager = session_manager # Kept for consistency, though events module now has it

    yield

    # Shutdown
    logger.info("Shutting down server...")

    # Cancel MT5 sync task (Phase 5.2)
    if mt5_sync_task:
        mt5_sync_task.cancel()
        try:
            await mt5_sync_task
        except asyncio.CancelledError:
            logger.info("MT5 sync task cancelled")

    if cleanup_task:
        await cleanup_task.stop()

    # Stop leaderboard refresh (Phase 01)
    await leaderboard_refresh_task.stop()

    # Stop MT5 background tasks (Phase 02)
    await mt5_position_sync_task.stop()
    await mt5_health_check_task.stop()
    # Disconnect PostgreSQL pool (Phase 5.2)
    if db_pool_manager:
        await db_pool_manager.disconnect()

    if redis_client:
        await redis_client.disconnect()

    # Close PostgreSQL pool (Phase 01)
    await postgres_client.close()

    if mt5_manager:
        mt5_manager.disconnect()
    logger.info("Server shutdown complete")

app = FastAPI(
    title="MT5 Trading Server",
    version="1.0.0",
    lifespan=lifespan
)

# Register API routers
from app.routers import kol_router
app.include_router(kol_router.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mt5_manager and mt5_manager.is_connected() else "unhealthy",
        "mt5_connected": mt5_manager.is_connected() if mt5_manager else False,
        "redis_connected": await redis_client.is_connected() if redis_client else False,
        "db_connected": await db_pool_manager.is_connected() if db_pool_manager else False,  # Phase 5.2
        "accuracy_tracking_enabled": accuracy_tracker is not None,  # Phase 5.2
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
