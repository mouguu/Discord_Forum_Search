"""
统一错误处理装饰器和异常管理
"""
import logging
import functools
import traceback
from typing import Callable, Any, Optional, Dict, List, Tuple
import discord
from discord.ext import commands
from utils.embed_helper import DiscordEmbedBuilder

logger = logging.getLogger('discord_bot.error_handler')

class BotError(Exception):
    """机器人基础异常类"""
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.user_message = user_message or message

class ConfigurationError(BotError):
    """配置错误"""
    pass

class CacheError(BotError):
    """缓存错误"""
    pass

class SearchError(BotError):
    """搜索错误"""
    pass

class PermissionError(BotError):
    """权限错误"""
    pass

def handle_command_errors(embed_builder: Optional[DiscordEmbedBuilder] = None) -> Callable[[Callable], Callable]:
    """
    命令错误处理装饰器

    Args:
        embed_builder: 可选的embed构建器，如果未提供将创建默认的
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await _handle_command_error(e, args, embed_builder)
        return wrapper
    return decorator

async def _handle_command_error(error: Exception, args: Tuple[Any, ...], embed_builder: Optional[DiscordEmbedBuilder]) -> None:
    """处理命令错误的内部函数"""
    # 尝试获取interaction对象
    interaction = None
    for arg in args:
        if isinstance(arg, discord.Interaction):
            interaction = arg
            break

    if not interaction:
        logger.error(f"无法找到interaction对象进行错误响应: {error}")
        return

    # 创建embed构建器
    if not embed_builder:
        embed_builder = DiscordEmbedBuilder()

    # 根据错误类型创建不同的响应
    if isinstance(error, BotError):
        embed = embed_builder.create_error_embed(
            "操作失败",
            error.user_message
        )
        logger.warning(f"Bot error in command: {error}")
    elif isinstance(error, discord.Forbidden):
        embed = embed_builder.create_error_embed(
            "权限不足",
            "机器人缺少执行此操作的权限，请联系管理员检查权限设置"
        )
        logger.warning(f"Permission error: {error}")
    elif isinstance(error, discord.NotFound):
        embed = embed_builder.create_error_embed(
            "资源未找到",
            "请求的资源不存在或已被删除"
        )
        logger.warning(f"Resource not found: {error}")
    elif isinstance(error, discord.HTTPException):
        if error.status == 429:  # Rate limited
            embed = embed_builder.create_warning_embed(
                "请求过于频繁",
                "请稍后再试，避免过于频繁的操作"
            )
        else:
            embed = embed_builder.create_error_embed(
                "网络错误",
                f"与Discord服务器通信时出现问题，请稍后重试"
            )
        logger.error(f"Discord HTTP error: {error}")
    else:
        # 未知错误
        embed = embed_builder.create_error_embed(
            "系统错误",
            "发生了未预期的错误，请稍后重试。如果问题持续存在，请联系管理员"
        )
        logger.error(f"Unexpected error in command: {error}", exc_info=True)

    # 发送错误响应
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as send_error:
        logger.error(f"Failed to send error response: {send_error}")

def handle_background_task_errors(task_name: str) -> Callable[[Callable], Callable]:
    """
    后台任务错误处理装饰器

    Args:
        task_name: 任务名称，用于日志记录
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in background task '{task_name}': {e}", exc_info=True)
                # 后台任务错误不需要用户响应，只记录日志
        return wrapper
    return decorator

class ErrorReporter:
    """错误报告器，用于收集和报告系统错误"""

    def __init__(self) -> None:
        self.error_counts: Dict[str, int] = {}
        self.last_errors: List[Dict[str, Any]] = []
        self.max_last_errors: int = 50

    def report_error(self, error: Exception, context: str = "unknown") -> None:
        """报告错误"""
        error_type = type(error).__name__
        error_key = f"{context}:{error_type}"

        # 更新错误计数
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # 记录最近的错误
        error_info = {
            'type': error_type,
            'message': str(error),
            'context': context,
            'traceback': traceback.format_exc(),
            'count': self.error_counts[error_key]
        }

        self.last_errors.insert(0, error_info)
        if len(self.last_errors) > self.max_last_errors:
            self.last_errors.pop()

        logger.error(f"Error reported - {context}: {error}", exc_info=True)

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return {
            'total_error_types': len(self.error_counts),
            'error_counts': dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)),
            'recent_errors': self.last_errors[:10]  # 最近10个错误
        }

# 全局错误报告器实例
error_reporter = ErrorReporter()
