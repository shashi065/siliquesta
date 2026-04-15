"""Caching layer for simulation results and computations.

Supports Redis caching with in-memory fallback.
Implements cache key generation, TTL management, and hit/miss tracking.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-backed cache with in-memory fallback."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        use_redis: bool = True,
    ):
        """Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default cache TTL in seconds (1 hour)
            use_redis: Use Redis if available, otherwise use in-memory
        """
        self.default_ttl = default_ttl
        self.use_redis = use_redis
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_cache: dict[str, tuple[Any, datetime]] = {}  # {key: (value, expiry)}
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        
        if use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Connected to Redis for caching")
            except Exception as e:
                logger.warning(f"⚠️  Redis unavailable for caching: {e}. Using in-memory cache.")
                self.use_redis = False

    @staticmethod
    def generate_key(
        operation: str,
        params: dict[str, Any],
        user_id: Optional[int] = None,
    ) -> str:
        """Generate cache key from operation and parameters.
        
        Args:
            operation: Operation type ('simulate', 'optimize', etc.)
            params: Operation parameters
            user_id: Optional user ID for user-specific caching
            
        Returns:
            Cache key
        """
        # Create stable parameter hash
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        if user_id:
            return f"cache:u{user_id}:{operation}:{param_hash}"
        else:
            return f"cache:{operation}:{param_hash}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.stats["hits"] += 1
                    logger.debug(f"🎯 Cache hit: {key}")
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                else:
                    self.stats["misses"] += 1
                    return None
            else:
                return self._get_memory(key)
        except Exception as e:
            logger.warning(f"⚠️  Cache get failed: {e}")
            self.stats["misses"] += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            Success flag
        """
        ttl = ttl or self.default_ttl
        
        try:
            value_json = json.dumps(value) if not isinstance(value, str) else value
            
            if self.redis_client:
                self.redis_client.setex(key, ttl, value_json)
                logger.debug(f"💾 Cached: {key} (TTL: {ttl}s)")
                return True
            else:
                return self._set_memory(key, value, ttl)
        except Exception as e:
            logger.warning(f"⚠️  Cache set failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Success flag
        """
        try:
            if self.redis_client:
                self.redis_client.delete(key)
                return True
            else:
                if key in self.in_memory_cache:
                    del self.in_memory_cache[key]
                    self.stats["evictions"] += 1
                    return True
                return False
        except Exception as e:
            logger.warning(f"⚠️  Cache delete failed: {e}")
            return False

    def clear_prefix(self, prefix: str) -> int:
        """Clear all keys matching prefix (e.g., 'cache:simulate:*').
        
        Args:
            prefix: Key prefix
            
        Returns:
            Number of keys deleted
        """
        count = 0
        
        try:
            if self.redis_client:
                # Redis SCAN for pattern matching (non-blocking)
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=f"{prefix}*", count=100)
                    for key in keys:
                        self.redis_client.delete(key)
                        count += 1
                    if cursor == 0:
                        break
            else:
                # In-memory: delete matching keys
                keys_to_delete = [k for k in self.in_memory_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.in_memory_cache[key]
                    count += 1
                    self.stats["evictions"] += 1
        except Exception as e:
            logger.warning(f"⚠️  Cache clear_prefix failed: {e}")
        
        logger.info(f"🗑️  Cleared {count} cache keys with prefix: {prefix}")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Hit rate, stats, and memory info
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        stats = {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate_%": round(hit_rate, 2),
            "total_requests": total,
            "backend": "redis" if (self.redis_client and self.use_redis) else "in-memory",
        }
        
        # Add memory info if using in-memory cache
        if not self.redis_client or not self.use_redis:
            stats["in_memory_entries"] = len(self.in_memory_cache)
            stats["max_entries"] = 10000  # Safety limit
        
        return stats

    def cache_simulation_result(
        self,
        params: dict[str, Any],
        result: dict[str, Any],
        user_id: Optional[int] = None,
        ttl: int = 7200,  # 2 hours for simulations
    ) -> str:
        """Cache a simulation result.
        
        Args:
            params: Simulation parameters
            result: Simulation result
            user_id: Optional user ID
            ttl: Cache TTL in seconds
            
        Returns:
            Cache key
        """
        key = self.generate_key("simulate", params, user_id)
        self.set(key, result, ttl=ttl)
        logger.info(f"📊 Simulation cached: {key}")
        return key

    def get_simulation_cache(
        self,
        params: dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        """Get cached simulation result.
        
        Args:
            params: Simulation parameters
            user_id: Optional user ID
            
        Returns:
            Cached result or None
        """
        key = self.generate_key("simulate", params, user_id)
        return self.get(key)

    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of entries cleared
        """
        prefix = f"cache:u{user_id}:"
        return self.clear_prefix(prefix)

    def invalidate_operation_cache(self, operation: str) -> int:
        """Invalidate all cache entries for an operation type.
        
        Args:
            operation: Operation type ('simulate', 'optimize', etc.)
            
        Returns:
            Number of entries cleared
        """
        prefix = f"cache:{operation}:"
        return self.clear_prefix(prefix)

    # ============ Private Methods ============

    def _get_memory(self, key: str) -> Optional[Any]:
        """Get from in-memory cache."""
        if key in self.in_memory_cache:
            value, expiry = self.in_memory_cache[key]
            if datetime.utcnow() < expiry:
                self.stats["hits"] += 1
                logger.debug(f"🎯 In-memory cache hit: {key}")
                return value
            else:
                # Expired, remove it
                del self.in_memory_cache[key]
                self.stats["evictions"] += 1
        
        self.stats["misses"] += 1
        return None

    def _set_memory(self, key: str, value: Any, ttl: int) -> bool:
        """Set in-memory cache."""
        # Simple memory limit: keep only 10,000 entries
        if len(self.in_memory_cache) >= 10000:
            # Remove oldest entry
            oldest_key = min(
                self.in_memory_cache.keys(),
                key=lambda k: self.in_memory_cache[k][1]
            )
            del self.in_memory_cache[oldest_key]
            self.stats["evictions"] += 1
        
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self.in_memory_cache[key] = (value, expiry)
        logger.debug(f"💾 In-memory cached: {key} (TTL: {ttl}s)")
        return True

    def warm_cache(
        self,
        common_params_list: list[dict[str, Any]],
        operation: str = "simulate",
        user_id: Optional[int] = None,
    ) -> None:
        """Pre-warm cache with common parameter sets.
        
        Useful for frequently-used designs.
        
        Args:
            common_params_list: List of common parameter dicts
            operation: Operation type
            user_id: Optional user ID
        """
        logger.info(f"🔥 Warming cache with {len(common_params_list)} common designs...")
        for params in common_params_list:
            key = self.generate_key(operation, params, user_id)
            # Mark as "warming" placeholder - will be filled with real results
            self.set(key, {"status": "warming"}, ttl=self.default_ttl)

    def estimate_memory_usage(self) -> dict[str, Any]:
        """Estimate cache memory usage.
        
        Returns:
            Memory usage estimate
        """
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info("memory")
                return {
                    "used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                    "peak_mb": round(info.get("used_memory_peak", 0) / 1024 / 1024, 2),
                    "allocated_mb": round(info.get("maxmemory", 0) / 1024 / 1024, 2),
                }
            except Exception as e:
                logger.warning(f"⚠️  Failed to get Redis memory info: {e}")
        
        # Estimate from in-memory cache
        import sys
        total_bytes = sum(
            sys.getsizeof(key) + sys.getsizeof(value)
            for key, (value, _) in self.in_memory_cache.items()
        )
        
        return {
            "used_mb": round(total_bytes / 1024 / 1024, 2),
            "peak_mb": 0,
            "allocated_mb": 0,
        }


# Global cache instance
_cache: Optional[CacheManager] = None


def get_cache(redis_url: str = "redis://localhost:6379") -> CacheManager:
    """Get or create global cache instance."""
    global _cache
    
    if _cache is None:
        _cache = CacheManager(redis_url=redis_url)
    
    return _cache
