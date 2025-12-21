import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # MT5 Credentials
    ACCOUNT_NUMBER: int = int(os.getenv("MT5_ACCOUNT", "0"))
    ACCOUNT_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    BROKER_SERVER: str = os.getenv("MT5_SERVER", "")

    # Connection
    CONNECTION_TIMEOUT: float = float(os.getenv("MT5_CONN_TIMEOUT", "30.0"))
    HEALTH_CHECK_INTERVAL: float = float(os.getenv("MT5_HEALTH_INTERVAL", "5.0"))

    # Retry
    MAX_ORDER_RETRIES: int = int(os.getenv("MT5_MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("MT5_RETRY_DELAY", "1.0"))

    # Trading
    DEFAULT_SLIPPAGE: float = float(os.getenv("MT5_SLIPPAGE", "20.0")) 
    ORDER_FILLING_TYPE: str = os.getenv("MT5_FILLING", "IOC")

    # Socket.IO Server
    SOCKETIO_HOST: str = os.getenv('SOCKETIO_HOST', '0.0.0.0')
    SOCKETIO_PORT: int = int(os.getenv('SOCKETIO_PORT', '5000'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

config = Config()
