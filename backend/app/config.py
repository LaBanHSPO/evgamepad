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
    SOCKETIO_PORT: int = int(os.getenv('SOCKETIO_PORT', '8686'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))

    # LLM API Keys (Phase 04 - AI Recommendations)
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
    ZAI_API_KEY: str = os.getenv('ZAI_API_KEY', '')
    DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'claude')

    # TwelveData API (Volume Validation)
    TWELVEDATA_API_KEY: str = os.getenv('TWELVEDATA_API_KEY', '')
    VOLUME_DIVERGENCE_THRESHOLD: float = float(os.getenv('VOLUME_DIVERGENCE_THRESHOLD', '0.30'))  # 30% divergence threshold

    # Phase 5: Explainability Layer Feature Flags
    ENABLE_EXPLAINABILITY: bool = os.getenv('ENABLE_EXPLAINABILITY', 'false').lower() == 'true'
    ENABLE_PROVENANCE_TRACKING: bool = os.getenv('ENABLE_PROVENANCE_TRACKING', 'false').lower() == 'true'
    ENABLE_ACCURACY_TRACKING: bool = os.getenv('ENABLE_ACCURACY_TRACKING', 'false').lower() == 'true'

    # PostgreSQL Database (Phase 5.2: Accuracy Tracking)
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'ev_gamepad')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_MIN_POOL_SIZE: int = int(os.getenv('DB_MIN_POOL_SIZE', '2'))
    DB_MAX_POOL_SIZE: int = int(os.getenv('DB_MAX_POOL_SIZE', '10'))

config = Config()
