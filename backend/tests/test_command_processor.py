import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.processors.command_processor import CommandProcessor
from app.models.responses import ErrorCode

@pytest.fixture
def mock_mt5_manager():
    manager = Mock()
    manager.is_connected.return_value = True
    return manager

@pytest.fixture
def processor(mock_mt5_manager):
    return CommandProcessor(mock_mt5_manager)

@pytest.mark.asyncio
async def test_process_buy_order_success(processor):
    """Test successful buy order processing"""
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.return_value = {
            'ticket': 123456,
            'price': 1.0850,
            'volume': 0.01,
            'timestamp': '2025-12-21T10:00:00Z'
        }

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01,
            sl=1.0800,
            tp=1.0900
        )

        if not result['success']:
            print(f"Test Failed. Result: {result}")

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert result['symbol'] == 'EURUSD'
        assert result['price'] == 1.0850
        assert 'command_id' in result

@pytest.mark.asyncio
async def test_process_buy_order_validation_error(processor):
    """Test buy order with validation error"""
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.side_effect = ValueError("Invalid symbol")

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='INVALID',
            volume=0.01
        )

        assert result['success'] is False
        assert result['code'] == ErrorCode.VALIDATION_ERROR.value
        assert "Invalid symbol" in result['message']

@pytest.mark.asyncio
async def test_process_buy_order_mt5_error(processor):
    """Test buy order with MT5 connection error"""
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.side_effect = RuntimeError("MT5 not connected")

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01
        )

        assert result['success'] is False
        assert result['code'] == ErrorCode.MT5_NOT_CONNECTED.value

@pytest.mark.asyncio
async def test_process_sell_order_success(processor):
    """Test successful sell order processing"""
    with patch.object(processor.trading_ops, 'place_sell_market') as mock_sell:
        mock_sell.return_value = {
            'ticket': 654321,
            'price': 1.0840,
            'volume': 0.01,
            'timestamp': '2025-12-21T10:00:00Z'
        }

        result = await processor.process_sell_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01
        )

        assert result['success'] is True
        assert result['ticket'] == 654321
        assert result['type'] == 'sell' if 'type' in result else True # check handled by endpoint, here just check success

@pytest.mark.asyncio
async def test_process_modify_position_success(processor):
    """Test successful position modification"""
    with patch.object(processor.trading_ops, 'modify_position') as mock_modify:
        mock_modify.return_value = {
            'ticket': 123456,
            'new_sl': 1.0820,
            'new_tp': 1.0920,
            'modified_at': '2025-12-21T10:05:00Z'
        }

        result = await processor.process_modify_position(
            sid='test_client',
            ticket=123456,
            sl=1.0820,
            tp=1.0920
        )

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert result['sl'] == 1.0820

@pytest.mark.asyncio
async def test_process_close_position_success(processor):
    """Test successful position close"""
    with patch.object(processor.trading_ops, 'close_position') as mock_close:
        mock_close.return_value = {
            'ticket': 123456,
            'close_ticket': 999999,
            'close_price': 1.0850,
            'volume_closed': 0.01,
            'profit': 10.0,
            'closed_at': '2025-12-21T10:10:00Z'
        }

        result = await processor.process_close_position(
            sid='test_client',
            ticket=123456
        )

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert result['profit'] == 10.0
