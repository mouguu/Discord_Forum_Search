import asyncio
import logging
from discord import Thread
from typing import Dict, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger('discord_bot.thread_stats')

# 导入统一缓存管理器
from .cache_manager import cache_manager

async def get_thread_stats(thread: Thread) -> Dict[str, int]:
    """
    获取线程的统计数据，包括 reaction_count 和 reply_count。
    使用统一缓存管理器减少API调用，并优化数据获取方式。

    Args:
        thread: Discord线程对象

    Returns:
        包含reaction_count和reply_count的字典
    """
    try:
        # 检查统一缓存
        cached_stats = await cache_manager.thread_cache.get_thread_stats(str(thread.id))
        if cached_stats:
            return cached_stats

        stats = {'reaction_count': 0, 'reply_count': 0}

        # 使用 fetch_message 直接获取第一条消息
        try:
            first_message = await thread.fetch_message(thread.id)
            if first_message:
                stats['reaction_count'] = sum(r.count for r in first_message.reactions) if first_message.reactions else 0
        except Exception as e:
            logger.warning(f"无法获取线程 {thread.id} 的第一条消息: {e}")
            try:
                # 如果获取失败，尝试使用history
                async for msg in thread.history(limit=1, oldest_first=True):
                    stats['reaction_count'] = sum(r.count for r in msg.reactions) if msg.reactions else 0
                    break
            except Exception as e2:
                logger.error(f"无法获取线程 {thread.id} 的历史消息: {e2}")

        # 优化回复数计算逻辑
        try:
            # 首选使用message_count属性（如果可用）
            if hasattr(thread, "message_count") and thread.message_count is not None:
                stats['reply_count'] = max(0, thread.message_count - 1)
            else:
                # 使用history计数作为可靠的备选方案
                count = 0
                async for _ in thread.history(limit=None):
                    count += 1
                stats['reply_count'] = max(0, count - 1)  # 减去初始消息
        except Exception as e:
            logger.error(f"计算线程 {thread.id} 的回复数时出错: {e}", exc_info=True)
            stats['reply_count'] = 0

        # 保存到统一缓存
        await cache_manager.thread_cache.set_thread_stats(str(thread.id), stats)
        return stats

    except Exception as e:
        logger.error(f"计算线程 {thread.name} ({thread.id}) 的统计数据时出错: {e}", exc_info=True)
        return {'reaction_count': 0, 'reply_count': 0}
