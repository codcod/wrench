# Resilient API calls

```python
from wrench.core.retry import retry_async, CircuitBreaker, timeout_async

@retry_async(max_retries=3, backoff_factor=2.0)
@timeout_async(30.0)
async def resilient_api_call():
    # Your API call here
    pass

# Circuit breaker for preventing cascading failures
cb = CircuitBreaker(failure_threshold=5)

@cb
async def protected_operation():
    # Operation that might fail
    pass
```
