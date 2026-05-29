"""
Cache Manager - Centralized caching for the trading bot.
Reduces API calls and improves performance for non-LLM operations.

From PLAN_OF_ACTION.md:
- The only variable should be the LLM model
- All other bottlenecks should be handled properly
"""
import asyncio
import time
from typing import Dict, Any, Optional, Callable, TypeVar, List
from dataclasses import dataclass
from functools import wraps
from loguru import logger

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    value: Any
    timestamp: float
    ttl: float  # seconds
    hits: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return (time.time() - self.timestamp) > self.ttl
    
    def get(self) -> Any:
        """Get value and increment hit counter."""
        self.hits += 1
        return self.value


class CacheManager:
    """
    Centralized cache manager for the trading bot.
    
    Features:
    - TTL-based expiration
    - Namespace support for different data types
    - Hit/miss statistics
    - Automatic cleanup
    - Thread-safe operations
    """
    
    # Default TTLs for different data types (seconds)
    TTL_QUOTE = 5           # Stock quotes - very short
    TTL_LTP = 3             # Last traded price - very short
    TTL_HISTORICAL = 300    # Historical data - 5 minutes
    TTL_MARKET_CONTEXT = 300  # Market context - 5 minutes
    TTL_NEWS = 600          # News data - 10 minutes
    TTL_SCREENER = 600      # Screener results - 10 minutes
    TTL_TRADE_PLAN = 300    # Trade plans - 5 minutes
    TTL_MARGIN = 60         # Margin data - 1 minute
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of entries across all namespaces
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"📦 Cache Manager initialized (max_size={max_size})")
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create namespaced cache key."""
        return f"{namespace}:{key}"
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            namespace: Cache namespace (e.g., 'quote', 'historical')
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._make_key(namespace, key)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[cache_key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.get()
    
    async def set(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default for namespace if not provided)
        """
        cache_key = self._make_key(namespace, key)
        
        # Use default TTL for namespace if not provided
        if ttl is None:
            ttl = self._get_default_ttl(namespace)
        
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size:
                await self._evict_oldest()
            
            self._cache[cache_key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
    
    def _get_default_ttl(self, namespace: str) -> float:
        """Get default TTL for namespace."""
        ttl_map = {
            'quote': self.TTL_QUOTE,
            'ltp': self.TTL_LTP,
            'historical': self.TTL_HISTORICAL,
            'market_context': self.TTL_MARKET_CONTEXT,
            'news': self.TTL_NEWS,
            'screener': self.TTL_SCREENER,
            'trade_plan': self.TTL_TRADE_PLAN,
            'margin': self.TTL_MARGIN,
        }
        return ttl_map.get(namespace, 60)  # Default 1 minute
    
    async def _evict_oldest(self):
        """Evict oldest entries when at capacity."""
        if not self._cache:
            return
        
        # Sort by timestamp and remove oldest 10%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].timestamp
        )
        
        evict_count = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:evict_count]:
            del self._cache[key]
            self._evictions += 1
        
        logger.debug(f"🗑️ Evicted {evict_count} cache entries")
    
    async def invalidate(self, namespace: str, key: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            namespace: Cache namespace
            key: Specific key to invalidate (if None, invalidates entire namespace)
        """
        async with self._lock:
            if key:
                cache_key = self._make_key(namespace, key)
                if cache_key in self._cache:
                    del self._cache[cache_key]
            else:
                # Invalidate entire namespace
                prefix = f"{namespace}:"
                keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
                for k in keys_to_delete:
                    del self._cache[k]
                logger.debug(f"🗑️ Invalidated {len(keys_to_delete)} entries in {namespace}")

    async def cleanup_expired(self):
        """Remove all expired entries."""
        async with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired()
            ]
            for k in expired_keys:
                del self._cache[k]

            if expired_keys:
                logger.debug(f"🧹 Cleaned up {len(expired_keys)} expired entries")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "entries": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(hit_rate, 2),
            "evictions": self._evictions,
            "namespaces": self._get_namespace_stats()
        }

    def _get_namespace_stats(self) -> Dict[str, int]:
        """Get entry count per namespace."""
        stats = {}
        for key in self._cache:
            namespace = key.split(":")[0]
            stats[namespace] = stats.get(namespace, 0) + 1
        return stats

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🗑️ Cleared {count} cache entries")


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(namespace: str, key_func: Optional[Callable] = None, ttl: Optional[float] = None):
    """
    Decorator for caching async function results.

    Args:
        namespace: Cache namespace
        key_func: Function to generate cache key from args (default: str of first arg)
        ttl: Time-to-live in seconds

    Example:
        @cached('ltp', key_func=lambda symbol: symbol)
        async def get_ltp(symbol: str) -> float:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            elif args:
                cache_key = str(args[0])
            else:
                cache_key = "default"

            # Try to get from cache
            cached_value = await cache.get(namespace, cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)

            if result is not None:
                await cache.set(namespace, cache_key, result, ttl)

            return result

        return wrapper
    return decorator


class RateLimiter:
    """
    Rate limiter for API calls.
    Prevents exceeding API rate limits.
    """

    def __init__(self, calls_per_second: float = 10, calls_per_minute: float = 100):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Maximum calls per second
            calls_per_minute: Maximum calls per minute
        """
        self.calls_per_second = calls_per_second
        self.calls_per_minute = calls_per_minute

        self._second_calls: List[float] = []
        self._minute_calls: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """
        Acquire permission to make an API call.
        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = time.time()

            # Clean old entries
            self._second_calls = [t for t in self._second_calls if now - t < 1]
            self._minute_calls = [t for t in self._minute_calls if now - t < 60]

            # Check limits
            while len(self._second_calls) >= self.calls_per_second:
                await asyncio.sleep(0.1)
                now = time.time()
                self._second_calls = [t for t in self._second_calls if now - t < 1]

            while len(self._minute_calls) >= self.calls_per_minute:
                await asyncio.sleep(1)
                now = time.time()
                self._minute_calls = [t for t in self._minute_calls if now - t < 60]

            # Record call
            self._second_calls.append(now)
            self._minute_calls.append(now)

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        now = time.time()
        return {
            "calls_last_second": len([t for t in self._second_calls if now - t < 1]),
            "calls_last_minute": len([t for t in self._minute_calls if now - t < 60]),
            "limit_per_second": self.calls_per_second,
            "limit_per_minute": self.calls_per_minute
        }


def rate_limited(limiter: RateLimiter):
    """
    Decorator for rate-limiting async function calls.

    Args:
        limiter: RateLimiter instance

    Example:
        api_limiter = RateLimiter(calls_per_second=5)

        @rate_limited(api_limiter)
        async def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiters for different APIs
fyers_rate_limiter = RateLimiter(calls_per_second=10, calls_per_minute=200)
news_rate_limiter = RateLimiter(calls_per_second=2, calls_per_minute=60)
ai_rate_limiter = RateLimiter(calls_per_second=1, calls_per_minute=30)

