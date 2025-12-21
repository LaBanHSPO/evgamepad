import logging
import sys

def setup_logging(debug: bool = False, json_format: bool = False):
    level = logging.DEBUG if debug else logging.INFO

    if json_format:
        # JSON structured logging for production
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler(sys.stdout)
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
            handler.setFormatter(formatter)

            logging.basicConfig(
                level=level,
                handlers=[handler]
            )
        except ImportError:
            # Fallback to standard logging
            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
    else:
        # Standard logging for development
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return logging.getLogger("app")
