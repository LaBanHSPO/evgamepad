"""MT5 Integration Data Models - Phase 02"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountStatus(str, Enum):
    """MT5 account pool status"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    ERROR = "error"
    EXPIRED = "expired"


class HealthStatus(str, Enum):
    """MT5 account health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"


class OrderStatus(str, Enum):
    """MT5 order execution status"""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderType(str, Enum):
    """MT5 order type"""
    BUY = "BUY"
    SELL = "SELL"


class PositionStatus(str, Enum):
    """Position lifecycle status"""
    OPEN = "open"
    CLOSED = "closed"


class MT5Account(BaseModel):
    """MT5 Account Pool Entry"""
    account_id: str
    account_number: int
    broker_server: str
    encrypted_password: str
    status: AccountStatus = AccountStatus.AVAILABLE
    allocated_to_user_id: Optional[str] = None
    allocated_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_status: HealthStatus = HealthStatus.HEALTHY
    expiry_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MT5AccountAllocation(BaseModel):
    """Response for account allocation"""
    account_number: int
    broker_server: str
    decrypted_password: str  # Only in memory, never stored
    allocated_at: datetime


class MT5Order(BaseModel):
    """MT5 Order Execution Record"""
    order_id: str
    session_id: str
    user_id: str
    account_number: int
    ticket: Optional[int] = None  # MT5 ticket (null if failed)
    symbol: str
    order_type: OrderType
    volume: Decimal
    price: Optional[Decimal] = None
    sl: Optional[Decimal] = None
    tp: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    retcode: Optional[int] = None
    comment: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MT5Position(BaseModel):
    """Enhanced Position with MT5 Metadata"""
    position_id: str
    session_id: str
    user_id: str
    account_number: Optional[int] = None
    ticket: int  # MT5 ticket
    symbol: str
    position_type: OrderType
    volume: Decimal
    open_price: Decimal
    close_price: Optional[Decimal] = None
    pnl: Decimal = Decimal("0.00")
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MT5PositionSync(BaseModel):
    """Position sync payload from MT5 terminal"""
    ticket: int
    symbol: str
    position_type: OrderType
    volume: Decimal
    open_price: Decimal
    current_price: Decimal
    pnl: Decimal
    opened_at: datetime


class AccountPoolStats(BaseModel):
    """Account pool statistics"""
    total_accounts: int
    available: int
    in_use: int
    error: int
    expired: int
    healthy: int
    unhealthy: int
    disconnected: int


class MT5HealthCheckResult(BaseModel):
    """Health check result for single account"""
    account_number: int
    is_connected: bool
    health_status: HealthStatus
    last_check: datetime
    error_message: Optional[str] = None
