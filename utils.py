import os
import functools
import time
import asyncio
from typing import Any, Callable, TypeVar, cast
from logger import logger

F = TypeVar("F", bound=Callable[..., Any])

def handle_errors(label: str = "Operation"):
    """
    A decorator that logs errors and prevents the application from crashing.
    Works for both sync and async functions.
    """
    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"[{label}] Error in {func.__name__}: {str(e)}")
                    logger.exception(e)
                    return None
            return cast(F, async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"[{label}] Error in {func.__name__}: {str(e)}")
                    logger.exception(e)
                    return None
            return cast(F, sync_wrapper)
    return decorator

def time_it(func: F) -> F:
    """Logs the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.debug(f"{func.__name__} took {end_time - start_time:.4f}s")
        return result
    return cast(F, wrapper)

def ensure_dir(directory: str):
    """Ensures that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
