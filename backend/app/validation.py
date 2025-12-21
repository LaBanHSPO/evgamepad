from typing import Dict, Any, Tuple

def validate_login_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate login command payload"""
    required = ['account', 'password', 'server']

    # Check required fields
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Type validation
    if not isinstance(data['account'], int):
        return False, "Account must be an integer"

    if not isinstance(data['password'], str) or not data['password']:
        return False, "Password must be a non-empty string"

    if not isinstance(data['server'], str) or not data['server']:
        return False, "Server must be a non-empty string"

    return True, ""

def validate_order_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate buy/sell order command"""
    required = ['symbol', 'volume']

    # Check required fields
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Symbol validation
    if not isinstance(data['symbol'], str) or not data['symbol']:
        return False, "Symbol must be a non-empty string"

    # Volume validation
    try:
        volume = float(data['volume'])
        if volume <= 0:
            return False, "Volume must be positive"
        if volume > 100:  # Sanity check
            return False, "Volume exceeds maximum (100 lots)"
    except (ValueError, TypeError):
        return False, "Volume must be a number"

    # Optional: SL/TP validation
    if 'sl' in data:
        try:
            float(data['sl'])
        except (ValueError, TypeError):
            return False, "SL must be a number"

    if 'tp' in data:
        try:
            float(data['tp'])
        except (ValueError, TypeError):
            return False, "TP must be a number"

    return True, ""

def validate_modify_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate modify position command"""
    required = ['ticket']

    # Check required fields
    if 'ticket' not in data:
        return False, "Missing required field: ticket"

    # Ticket validation
    try:
        int(data['ticket'])
    except (ValueError, TypeError):
        return False, "Ticket must be an integer"

    # At least one modification
    if 'sl' not in data and 'tp' not in data:
        return False, "Must provide at least one of: sl, tp"

    # SL/TP validation
    if 'sl' in data:
        try:
            float(data['sl'])
        except (ValueError, TypeError):
            return False, "SL must be a number"

    if 'tp' in data:
        try:
            float(data['tp'])
        except (ValueError, TypeError):
            return False, "TP must be a number"

    return True, ""

def validate_close_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate close position command"""
    required = ['ticket']

    if 'ticket' not in data:
        return False, "Missing required field: ticket"

    # Ticket validation
    try:
        int(data['ticket'])
    except (ValueError, TypeError):
        return False, "Ticket must be an integer"

    # Optional volume validation
    if 'volume' in data:
        try:
            volume = float(data['volume'])
            if volume <= 0:
                return False, "Volume must be positive"
        except (ValueError, TypeError):
            return False, "Volume must be a number"

    return True, ""
