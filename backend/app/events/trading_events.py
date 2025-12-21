import logging
from typing import Dict, Any
from datetime import datetime

from app.main import sio, mt5_manager, session_manager
from app.validation import (
    validate_login_command,
    validate_order_command,
    validate_modify_command,
    validate_close_command,
)
from app.models.responses import (
    success_response,
    error_response,
    ErrorCode,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION LIFECYCLE
# ============================================================================

@sio.event
async def connect(sid: str, environ: Dict[str, Any]):
    """Handle client connection"""
    remote_addr = environ.get('REMOTE_ADDR', 'unknown')
    logger.info(f"Client {sid} connected from {remote_addr}")

    # Initialize session
    session_manager.create_session(sid, {
        'connected_at': datetime.utcnow(),
        'remote_addr': remote_addr,
        'mt5_logged_in': False,
        'pending_orders': {},
    })

    # Send welcome message
    await sio.emit('connected', {
        'message': 'Connected to MT5 Trading Server',
        'session_id': sid,
        'server_time': datetime.utcnow().isoformat(),
    }, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    logger.info(f"Client {sid} disconnected")

    # Cleanup session
    session = session_manager.get_session(sid)
    if session:
        pending = session.get('pending_orders', {})
        if pending:
            logger.warning(f"Client {sid} disconnected with {len(pending)} pending orders")

    session_manager.remove_session(sid)

# ============================================================================
# TRADING COMMANDS
# ============================================================================

@sio.event
async def login(sid: str, data: Dict[str, Any]):
    """
    Handle MT5 login command

    Payload:
        {
            "account": 12345678,
            "password": "password",
            "server": "BrokerServer-Demo"
        }
    """
    logger.info(f"Login request from {sid}")

    try:
        # Validate
        is_valid, error_msg = validate_login_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Login to MT5
        # Note: In a real scenario, this would dynamically login the MT5 terminal to the specified account.
        # But MT5 terminal can only be logged into one account at a time.
        # For now, we assume this re-initializes or checks based on connection manager capability.
        # If the manager supports switching accounts, we use it.
        # But connection_manager.login_account doesn't exist yet in the Phase 1 file I saw.
        # The ConnectionManager has connect() which uses config credentials.
        # I should probably just check if the credentials match or if I should implement `login_account` in the manager.
        # For this phase 2, I will check against config or assume success if connected.
        # WAIT, the plan says: "Login to MT5 ... mt5_manager.login_account(...)"
        # But `MT5ConnectionManager` in `connection_manager.py` does NOT have `login_account`.
        # I need to implement it or use what's available.
        # The `connect()` method does `mt5.login`.
        # I will IMPLEMENT `login_account` in `MT5ConnectionManager` later or now.
        # Phase 2 plan assumes responsibilities for MT5 Manager were handled in Phase 1 or will be used here.
        # Since I'm in Phase 2, I should probably update MT5ConnectionManager or just call mt5 directly
        # but `mt5` is inside the manager logic usually.
        # I will access `mt5` directly or add the method.
        # Since I am responsible for "Socket.IO Server", I should probably stick to the plan which calls `mt5_manager.login_account`.
        # I will try to call it, but it will fail if it doesn't exist.
        # I'll check `connection_manager.py` again. It has `connect()`.
        # I will try to use `mt5.login` directly here via `mt5_manager` if I can access the module,
        # but better to add the method to `MT5ConnectionManager` to keep it encapsulated.
        # I will update `connection_manager.py` to add `login_account`.
        
        # NOTE: For now, I will write this code assuming `login_account` logic. 
        # But I need to update `connection_manager.py` first or concurrently.
        # I will address this after writing this file.
        
        account_info = mt5_manager.login_account(
            data['account'],
            data['password'],
            data['server']
        )
        
        # If login_account raises error or returns None/False
        if not account_info:
             raise Exception("Login failed")

        # Update session
        session = session_manager.get_session(sid)
        if session:
            session['mt5_logged_in'] = True
            session['account'] = data['account']

        # Send success
        await sio.emit('login_result', success_response({
            'account_info': {
                'login': account_info['login'],
                'name': account_info['name'],
                'server': account_info['server'],
                'currency': account_info['currency'],
                'balance': account_info['balance'],
                'equity': account_info['equity'],
                'leverage': account_info['leverage'],
            }
        }), to=sid)

        logger.info(f"Client {sid} logged in as {data['account']}")

    except Exception as e:
        logger.exception(f"Login failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Login failed: {str(e)}"
        ), to=sid)

@sio.event
async def buy(sid: str, data: Dict[str, Any]):
    """
    Handle buy market order

    Payload:
        {
            "symbol": "EURUSD",
            "volume": 0.01,
            "sl": 1.0800,  // optional
            "tp": 1.0900   // optional
        }
    """
    logger.info(f"Buy order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        # Validate
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Check MT5 login
        session = session_manager.get_session(sid)
        if not session or not session.get('mt5_logged_in'):
            await sio.emit('error', error_response(
                ErrorCode.MT5_NOT_CONNECTED,
                "Not logged in to MT5"
            ), to=sid)
            return

        # Place order via MT5 manager
        # (Will be implemented in Phase 3 - Command Integration)
        # For now, emit placeholder response
        await sio.emit('order_result', success_response({
            'ticket': 0,  # Placeholder
        # Placeholder (Phase 3)
        await sio.emit('modify_result', success_response({
            'ticket': data['ticket'],
            'sl': data.get('sl'),
            'tp': data.get('tp'),
            'message': 'Phase 2: Event handler registered'
        }), to=sid)

    except Exception as e:
        logger.exception(f"Modify failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Modify failed: {str(e)}"
        ), to=sid)

@sio.event
async def close(sid: str, data: Dict[str, Any]):
    """
    Handle close position

    Payload:
        {
            "ticket": 123456,
            "volume": 0.01  // optional, full close if omitted
        }
    """
    logger.info(f"Close request from {sid}: ticket={data.get('ticket')}")

    try:
        # Validate
        is_valid, error_msg = validate_close_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Placeholder (Phase 3)
        await sio.emit('close_result', success_response({
            'ticket': data['ticket'],
            'volume': data.get('volume', 'full'),
            'message': 'Phase 2: Event handler registered'
        }), to=sid)

    except Exception as e:
        logger.exception(f"Close failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Close failed: {str(e)}"
        ), to=sid)
