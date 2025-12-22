import logging
from socketio import AsyncServer
from app.config import config

logger = logging.getLogger(__name__)

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
