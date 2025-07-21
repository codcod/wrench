"""
Retry logic and resilience patterns for Wrench.

This module provides decorators and utilities for handling transient failures
in API calls and other operations.
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Awaitable, Callable, Type, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f'Failed after {attempts} attempts. Last error: {last_exception}'
        )


def retry_async(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    max_backoff: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
):
    """
    Decorator that adds retry logic to async functions.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        max_backoff: Maximum backoff time in seconds
        exceptions: Tuple of exception types to retry on
        jitter: Add randomization to backoff timing

    Example:
        @retry_async(max_retries=3, backoff_factor=2.0)
        async def unreliable_api_call():
            # Implementation here
            pass
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Exception = Exception('No attempts made')

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f'All retry attempts exhausted for {func.__name__}'
                        )
                        raise RetryExhaustedError(attempt + 1, e)

                    # Calculate backoff time
                    backoff_time = min(backoff_factor * (2**attempt), max_backoff)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        backoff_time *= 0.5 + random.random() * 0.5

                    logger.warning(
                        f'Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. '
                        f'Retrying in {backoff_time:.2f}s'
                    )

                    await asyncio.sleep(backoff_time)

            # This should never be reached, but just in case
            raise RetryExhaustedError(max_retries + 1, last_exception)

        return wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, calls are allowed
    - OPEN: Calls are blocked, returns failure immediately
    - HALF_OPEN: Test calls are allowed to check if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def __call__(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        """Use as decorator."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
                logger.info(
                    f'Circuit breaker for {func.__name__} entering HALF_OPEN state'
                )
            else:
                raise Exception(f'Circuit breaker OPEN for {func.__name__}')

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return (
            asyncio.get_event_loop().time() - self.last_failure_time
        ) >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            logger.info('Circuit breaker reset to CLOSED state')

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(
                f'Circuit breaker opened after {self.failure_count} failures'
            )


def timeout_async(seconds: float):
    """
    Decorator to add timeout to async functions.

    Args:
        seconds: Timeout in seconds

    Example:
        @timeout_async(30.0)
        async def slow_operation():
            # Implementation here
            pass
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f'Function {func.__name__} timed out after {seconds}s')
                raise

        return wrapper

    return decorator


# Common retry configurations
api_retry = retry_async(
    max_retries=3,
    backoff_factor=1.5,
    exceptions=(
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
    ),
)

network_retry = retry_async(
    max_retries=5,
    backoff_factor=2.0,
    max_backoff=30.0,
    exceptions=(
        ConnectionError,
        TimeoutError,
        OSError,  # Network errors
    ),
)
