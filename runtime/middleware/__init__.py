from .base import Middleware
from .scope_guard import ScopeGuardMiddleware
from .rate_limiter import RateLimiterMiddleware
from .ua_injector import UAInjectorMiddleware
from .destructive_guard import DestructiveGuardMiddleware
from .audit_logger import AuditLoggerMiddleware

def create_default_middleware(scope_file: str = "", rate_limit: int = 10) -> list[Middleware]:
    """Create the standard middleware stack."""
    mw = [
        DestructiveGuardMiddleware(),
        UAInjectorMiddleware(),
        RateLimiterMiddleware(rps=rate_limit),
        AuditLoggerMiddleware(),
    ]
    if scope_file:
        mw.insert(0, ScopeGuardMiddleware(scope_file))
    return mw
