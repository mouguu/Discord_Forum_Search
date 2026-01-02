"""
缓存管理器 - 统一缓存接口
"""
import logging
from typing import Optional, Dict, Any
from .advanced_cache import AdvancedCache, ThreadCache

logger = logging.getLogger('discord_bot.cache_manager')

class CacheManager:
    """统一的缓存管理器"""

    def __init__(self) -> None:
        self._thread_cache: Optional[ThreadCache] = None
        self._general_cache: Optional[AdvancedCache] = None

    def initialize(self, use_redis: bool = False, redis_url: Optional[str] = None,
                  cache_ttl: int = 300, thread_cache_size: int = 5000) -> None:
        """初始化缓存系统"""
        try:
            # 初始化线程缓存
            self._thread_cache = ThreadCache(
                use_redis=use_redis,
                redis_url=redis_url,
                ttl=cache_ttl,
                max_items=thread_cache_size
            )

            # 初始化通用缓存
            self._general_cache = AdvancedCache(
                use_redis=use_redis,
                redis_url=redis_url,
                ttl=cache_ttl,
                max_items=10000
            )

            logger.info(f"缓存管理器初始化完成 - Redis: {use_redis}")

        except Exception as e:
            logger.error(f"缓存管理器初始化失败: {e}")
            # 降级到内存缓存
            self._thread_cache = ThreadCache(use_redis=False)
            self._general_cache = AdvancedCache(use_redis=False)

    @property
    def thread_cache(self) -> ThreadCache:
        """获取线程缓存实例"""
        if self._thread_cache is None:
            self.initialize()
        return self._thread_cache

    @property
    def general_cache(self) -> AdvancedCache:
        """获取通用缓存实例"""
        if self._general_cache is None:
            self.initialize()
        return self._general_cache

    async def start_background_tasks(self) -> None:
        """启动后台清理任务"""
        if self._thread_cache:
            await self._thread_cache.start_background_cleanup(interval=300)
        if self._general_cache:
            await self._general_cache.start_background_cleanup(interval=300)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats: Dict[str, Any] = {}
        if self._thread_cache:
            stats['thread_cache'] = self._thread_cache.get_stats()
        if self._general_cache:
            stats['general_cache'] = self._general_cache.get_stats()
        return stats

# 全局缓存管理器实例
cache_manager = CacheManager()
