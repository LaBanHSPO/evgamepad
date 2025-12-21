from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from contextlib import asynccontextmanager
import logging

from app.config import config
from app.logging_config import setup_logging
from app.mt5.connection_manager import MT5ConnectionManager
from app.session_manager import SessionManager

# Initialize logging
logger = setup_logging(config.DEBUG)

# Global instances
mt5_manager = None
session_manager = None

# Socket.IO Server Configuration
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # VPN network - adjust for production
    ping_interval=25,          # Heartbeat every 25s
    ping_timeout=60,           # Disconnect after 60s no response
    max_http_buffer_size=1000000,  # 1MB max message size (1e6)
    logger=logger,
    engineio_logger=logger if config.DEBUG else False,
)

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global mt5_manager, session_manager

    logger.info("Starting MT5 Socket.IO Trading Server...")

    # Initialize MT5 connection
    mt5_manager = MT5ConnectionManager(
        check_interval=config.HEALTH_CHECK_INTERVAL,
        timeout=config.CONNECTION_TIMEOUT
    )

    if not mt5_manager.connect():
        logger.error("Failed to connect to MT5 terminal")
        # Ensure we don't crash the server loop if MT5 isn't there, 
        # but in production we might want to.
        # Allowing it to start so we can see health status.
        # raise RuntimeError("MT5 connection failed") 

    logger.info("MT5 connection attempt finished")

    # Initialize session manager
    session_manager = SessionManager()

    # Store in app state
    app.state.mt5_manager = mt5_manager
    app.state.session_manager = session_manager
    
    # Import events to register handlers
    import app.events.trading_events

    yield

    # Shutdown
    logger.info("Shutting down server...")
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
