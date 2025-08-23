import logging


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[95m', # Magenta
    }
    RESET = '\033[0m'          # Reset color
    BOLD = '\033[1m'           # Bold text
    
    def format(self, record):
        # Get the color for this log level
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format the message
        log_message = super().format(record)
        
        # Apply colors to different parts
        parts = log_message.split(' - ', 3)
        if len(parts) >= 4:
            timestamp, name, level, message = parts
            # Color the level and make it bold
            colored_level = f"{color}{self.BOLD}{level}{self.RESET}"
            # Color the logger name
            colored_name = f"\033[34m{name}{self.RESET}"  # Blue
            # Color the timestamp
            colored_timestamp = f"\033[90m{timestamp}{self.RESET}"  # Gray
            
            return f"{colored_timestamp} - {colored_name} - {colored_level} - {message}"
        
        return f"{color}{log_message}{self.RESET}"


def setup_logging():
    """Set up logging configuration with colors."""
    # Set up logging with colors
    logger_handler = logging.StreamHandler()
    logger_handler.setFormatter(ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(logger_handler)

    # Configure specific loggers
    # Set httpx to WARNING level to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Reduce noise from these loggers:
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # FastAPI logging configuration
    # Main FastAPI logger - set to INFO to see request/response logs
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Uvicorn loggers (if using uvicorn as ASGI server)
    # Configure uvicorn loggers to use the same format as your app
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_error_logger = logging.getLogger("uvicorn.error")

    # Remove uvicorn's default handlers and use your configured format
    for logger in [uvicorn_logger, uvicorn_access_logger, uvicorn_error_logger]:
        logger.handlers.clear()
        logger.setLevel(logging.WARNING)
        logger.propagate = True  # This makes them use the root logger's handlers

    # Optional: Enable more detailed logging for development
    # Uncomment these for even more verbose FastAPI logs:
    # logging.getLogger("fastapi").setLevel(logging.DEBUG)
    # logging.getLogger("starlette").setLevel(logging.INFO)  # Starlette framework logs
