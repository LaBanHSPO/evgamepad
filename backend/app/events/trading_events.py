import logging
from typing import Dict, Any
from datetime import datetime

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

# Global instances (will be injected from main.py)
from app.sio import sio

mt5_manager = None
session_manager = None
reconnection_manager = None
command_processor = None

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION LIFECYCLE
# ============================================================================

@sio.event
async def connect(sid: str, environ: Dict[str, Any]):
    """Handle client connection with reconnection detection"""
    remote_addr = environ.get('REMOTE_ADDR', 'unknown')
    logger.info(f"Client {sid} connecting from {remote_addr}")

    # Attempt session recovery
    recovered_session = None
    if reconnection_manager:
        recovered_session = reconnection_manager.recover_session(sid)

    if recovered_session:
        # Reconnection detected
        logger.info(f"Reconnection detected for {sid}")

        # Restore session
        session_manager.create_session(sid, recovered_session)

        # Notify client of recovery
        await sio.emit('session_recovered', {
            'message': 'Session recovered',
            'session_id': sid,
            'pending_orders': reconnection_manager.get_pending_orders(sid) if reconnection_manager else [],
            'reconnected_at': datetime.utcnow().isoformat(),
        }, to=sid)
    else:
        # New connection
        logger.info(f"New client {sid} connected from {remote_addr}")

        # Initialize fresh session
        session_manager.create_session(sid, {
            'connected_at': datetime.utcnow(),
            'remote_addr': remote_addr,
            'mt5_logged_in': False,
            'pending_orders': {},
        })

        # Send welcome
        await sio.emit('connected', {
            'message': 'Connected to MT5 Trading Server',
            'session_id': sid,
            'server_time': datetime.utcnow().isoformat(),
        }, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection with session preservation"""
    logger.info(f"Client {sid} disconnected")

    # Get session for preservation
    session = session_manager.get_session(sid)
    if session:
        # Store for recovery
        if reconnection_manager:
            reconnection_manager.store_disconnected_session(sid, session)

        # Log pending orders
        pending = session.get('pending_orders', {})
        if pending:
            logger.warning(
                f"Client {sid} disconnected with {len(pending)} pending orders - "
                f"session stored for recovery"
            )

    # Remove from active sessions
    session_manager.remove_session(sid)

# ============================================================================
# TRADING COMMANDS
# ============================================================================

@sio.event
async def login(sid: str, data: Dict[str, Any]):
    """Handle MT5 login command"""
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

        # Login to MT5 (using connection manager)
        account_info = mt5_manager.login_account(
            data['account'],
            data['password'],
            data['server']
        )
        
        if not account_info:
             raise Exception("Login failed on MT5")

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
    """Handle buy market order"""
    logger.info(f"Buy order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        # Use command processor if available
        if command_processor:
            response = await command_processor.process_buy_order(
                sid, 
                data['symbol'], 
                data['volume'], 
                data.get('sl'), 
                data.get('tp')
            )
            if response.get('success'):
                await sio.emit('order_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Buy failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)

@sio.event
async def sell(sid: str, data: Dict[str, Any]):
    """Handle sell market order"""
    logger.info(f"Sell order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        if command_processor:
            response = await command_processor.process_sell_order(
                sid, 
                data['symbol'], 
                data['volume'], 
                data.get('sl'), 
                data.get('tp')
            )
            if response.get('success'):
                await sio.emit('order_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Sell failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)

@sio.event
async def modify(sid: str, data: Dict[str, Any]):
    """Handle modify position"""
    logger.info(f"Modify request from {sid}: ticket={data.get('ticket')}")

    try:
        is_valid, error_msg = validate_modify_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        if command_processor:
            response = await command_processor.process_modify_position(
                sid,
                data['ticket'],
                data.get('sl'),
                data.get('tp')
            )
            if response.get('success'):
                await sio.emit('modify_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Modify failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)

@sio.event
async def close(sid: str, data: Dict[str, Any]):
    """Handle close position"""
    logger.info(f"Close request from {sid}: ticket={data.get('ticket')}")

    try:
        is_valid, error_msg = validate_close_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        if command_processor:
            response = await command_processor.process_close_position(
                sid,
                data['ticket'],
                data.get('volume')
            )
            if response.get('success'):
                await sio.emit('close_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Close failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)
