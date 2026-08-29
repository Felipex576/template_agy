import functools
import time
from src.config.logger import get_logger

logger = get_logger("decorators")

def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Executing: {func.__qualname__}")
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"Completed: {func.__qualname__} in {elapsed:.2f}s")
        return result
    return wrapper

def raise_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__qualname__}: {str(e)}", exc_info=True)
            raise
    return wrapper
