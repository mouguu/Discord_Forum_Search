"""
统一配置管理器
整合所有配置选项到单一文件，支持环境特定配置
"""
import os
import logging
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger('discord_bot.config')

class Environment(Enum):
    """环境类型枚举"""
    DEFAULT = "default"
    LARGE_SERVER = "large_server"
    DEVELOPMENT = "development"
    PRODUCTION = "production"

# 环境配置预设
ENVIRONMENT_CONFIGS = {
    Environment.DEFAULT: {
        "description": "默认配置 - 适用于中小型服务器",
        "cache": {
            "use_redis": False,
            "ttl": 300,
            "thread_cache_size": 5000,
            "max_items": 10000
        },
        "search": {
            "max_messages_per_search": 1000,
            "messages_per_page": 5,
            "concurrent_limit": 5,
            "guild_concurrent_searches": 3,
            "user_search_cooldown": 60,
            "search_timeout": 60.0,
            "max_embed_field_length": 1024
        },
        "database": {
            "use_database_index": False,
            "db_path": "data/searchdb.sqlite",
            "connection_pool_size": 5
        },
        "bot": {
            "command_prefix": "/",
            "log_level": "INFO",
            "embed_color": 0x3498db,
            "reaction_timeout": 900.0
        },
        "performance": {
            "enable_performance_monitoring": True,
            "thread_pool_workers": 4,
            "io_thread_pool_workers": 8,
            "max_results_per_user": 5000,
            "rate_limit_enabled": True,
            "max_commands_per_minute": 20
        }
    },
    Environment.LARGE_SERVER: {
        "description": "大型服务器配置 - 适用于10000+用户和大量帖子的服务器环境",
        "cache": {
            "use_redis": True,
            "redis_url": "redis://localhost:6379/0",
            "ttl": 600,  # 10分钟
            "thread_cache_size": 1000,
            "max_items": 10000
        },
        "search": {
            "max_messages_per_search": 1000,
            "messages_per_page": 5,
            "concurrent_limit": 5,
            "guild_concurrent_searches": 3,
            "user_search_cooldown": 60,
            "search_timeout": 60.0,
            "max_embed_field_length": 1000,
            "use_incremental_loading": True,
            "message_batch_size": 100,
            "max_archived_threads": 500
        },
        "database": {
            "use_database_index": True,
            "db_path": "data/searchdb.sqlite",
            "connection_pool_size": 5
        },
        "bot": {
            "command_prefix": "/",
            "log_level": "INFO",
            "embed_color": 0x3498db,
            "reaction_timeout": 1800.0  # 30分钟
        },
        "performance": {
            "enable_performance_monitoring": True,
            "optimize_message_content": True,
            "max_content_length": 2000,
            "max_attachments_preview": 3,
            "max_reaction_count": 10,
            "thread_pool_workers": 4,
            "io_thread_pool_workers": 8,
            "stats_update_interval": 3600,
            "keep_stats_history": True,
            "stats_history_length": 24,
            "search_auto_cancel": True,
            "max_results_per_user": 5000,
            "rate_limit_enabled": True,
            "max_commands_per_minute": 20
        }
    },
    Environment.DEVELOPMENT: {
        "description": "开发环境配置 - 用于本地开发和测试",
        "cache": {
            "use_redis": False,
            "ttl": 300,
            "thread_cache_size": 100,
            "max_items": 1000
        },
        "search": {
            "max_messages_per_search": 100,
            "messages_per_page": 3,
            "concurrent_limit": 2,
            "guild_concurrent_searches": 1,
            "user_search_cooldown": 10,
            "search_timeout": 30.0,
            "max_embed_field_length": 1024
        },
        "database": {
            "use_database_index": False,
            "db_path": "data/dev_searchdb.sqlite",
            "connection_pool_size": 2
        },
        "bot": {
            "command_prefix": "!",
            "log_level": "DEBUG",
            "embed_color": 0xe74c3c,
            "reaction_timeout": 300.0  # 5分钟
        },
        "performance": {
            "enable_performance_monitoring": False,
            "thread_pool_workers": 2,
            "io_thread_pool_workers": 4,
            "max_results_per_user": 100,
            "rate_limit_enabled": False,
            "max_commands_per_minute": 100
        }
    },
    Environment.PRODUCTION: {
        "description": "生产环境配置 - 用于正式部署",
        "cache": {
            "use_redis": True,
            "redis_url": "redis://localhost:6379/0",
            "ttl": 900,  # 15分钟
            "thread_cache_size": 2000,
            "max_items": 20000
        },
        "search": {
            "max_messages_per_search": 2000,
            "messages_per_page": 5,
            "concurrent_limit": 10,
            "guild_concurrent_searches": 5,
            "user_search_cooldown": 30,
            "search_timeout": 120.0,
            "max_embed_field_length": 1024,
            "use_incremental_loading": True,
            "message_batch_size": 200,
            "max_archived_threads": 1000
        },
        "database": {
            "use_database_index": True,
            "db_path": "data/prod_searchdb.sqlite",
            "connection_pool_size": 10
        },
        "bot": {
            "command_prefix": "/",
            "log_level": "WARNING",
            "embed_color": 0x2ecc71,
            "reaction_timeout": 3600.0  # 1小时
        },
        "performance": {
            "enable_performance_monitoring": True,
            "optimize_message_content": True,
            "max_content_length": 3000,
            "max_attachments_preview": 5,
            "max_reaction_count": 15,
            "thread_pool_workers": 8,
            "io_thread_pool_workers": 16,
            "stats_update_interval": 1800,
            "keep_stats_history": True,
            "stats_history_length": 48,
            "search_auto_cancel": True,
            "max_results_per_user": 10000,
            "rate_limit_enabled": True,
            "max_commands_per_minute": 30
        }
    }
}

@dataclass
class CacheConfig:
    """缓存配置"""
    use_redis: bool = False
    redis_url: str = "redis://localhost:6379/0"
    ttl: int = 300
    thread_cache_size: int = 5000
    max_items: int = 10000

@dataclass
class SearchConfig:
    """搜索配置"""
    max_messages_per_search: int = 1000
    messages_per_page: int = 5
    concurrent_limit: int = 5
    guild_concurrent_searches: int = 3
    user_search_cooldown: int = 60
    search_timeout: float = 60.0
    max_embed_field_length: int = 1024
    min_reactions: int = 1
    reaction_cache_ttl: int = 3600
    # 搜索排序选项
    search_order_options: List[str] = field(default_factory=lambda: [
        "最高反应降序",
        "最高反应升序",
        "总回复数降序",
        "总回复数升序",
        "发帖时间由新到旧",
        "发帖时间由旧到新",
        "最后活跃由新到旧",
        "最后活跃由旧到新"
    ])
    # 增量加载策略
    use_incremental_loading: bool = True
    message_batch_size: int = 100
    max_archived_threads: int = 500

@dataclass
class DatabaseConfig:
    """数据库配置"""
    use_database_index: bool = False
    db_path: str = "data/searchdb.sqlite"
    connection_pool_size: int = 5

@dataclass
class PerformanceConfig:
    """性能优化配置"""
    # 内存优化
    optimize_message_content: bool = True
    max_content_length: int = 2000
    max_attachments_preview: int = 3
    max_reaction_count: int = 10
    # 线程池设置
    thread_pool_workers: int = 4
    io_thread_pool_workers: int = 8
    # 统计和监控
    enable_performance_monitoring: bool = True
    stats_update_interval: int = 3600
    keep_stats_history: bool = True
    stats_history_length: int = 24
    # 负载均衡
    search_auto_cancel: bool = True
    # 安全设置
    max_results_per_user: int = 5000
    rate_limit_enabled: bool = True
    max_commands_per_minute: int = 20

@dataclass
class BotConfig:
    """机器人配置"""
    command_prefix: str = "/"
    log_level: str = "INFO"
    log_dir: str = "logs"
    embed_color: int = 0x3498db
    reaction_timeout: float = 900.0

@dataclass
class Settings:
    """应用设置"""
    bot: BotConfig = field(default_factory=BotConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    environment: Environment = Environment.DEFAULT

    @classmethod
    def load_from_env(cls) -> 'Settings':
        """从环境变量加载配置"""
        settings = cls()

        # Bot配置
        settings.bot.command_prefix = os.getenv('COMMAND_PREFIX', settings.bot.command_prefix)
        settings.bot.log_level = os.getenv('LOG_LEVEL', settings.bot.log_level)

        # 缓存配置
        settings.cache.use_redis = os.getenv('USE_REDIS_CACHE', 'false').lower() == 'true'
        settings.cache.redis_url = os.getenv('REDIS_URL', settings.cache.redis_url)
        settings.cache.ttl = int(os.getenv('CACHE_TTL', str(settings.cache.ttl)))

        # 搜索配置
        settings.search.max_messages_per_search = int(os.getenv('MAX_MESSAGES_PER_SEARCH', str(settings.search.max_messages_per_search)))
        settings.search.concurrent_limit = int(os.getenv('CONCURRENT_SEARCH_LIMIT', str(settings.search.concurrent_limit)))
        settings.search.messages_per_page = int(os.getenv('MESSAGES_PER_PAGE', str(settings.search.messages_per_page)))
        settings.search.guild_concurrent_searches = int(os.getenv('GUILD_CONCURRENT_SEARCHES', str(settings.search.guild_concurrent_searches)))
        settings.search.user_search_cooldown = int(os.getenv('USER_SEARCH_COOLDOWN', str(settings.search.user_search_cooldown)))
        settings.search.search_timeout = float(os.getenv('SEARCH_TIMEOUT', str(settings.search.search_timeout)))
        settings.search.max_embed_field_length = int(os.getenv('MAX_EMBED_FIELD_LENGTH', str(settings.search.max_embed_field_length)))
        settings.search.min_reactions = int(os.getenv('MIN_REACTIONS', str(settings.search.min_reactions)))
        settings.search.reaction_cache_ttl = int(os.getenv('REACTION_CACHE_TTL', str(settings.search.reaction_cache_ttl)))

        # 数据库配置
        settings.database.use_database_index = os.getenv('USE_DATABASE_INDEX', 'false').lower() == 'true'
        settings.database.db_path = os.getenv('DB_PATH', settings.database.db_path)
        settings.database.connection_pool_size = int(os.getenv('DB_CONNECTION_POOL_SIZE', str(settings.database.connection_pool_size)))

        # 性能配置
        settings.performance.enable_performance_monitoring = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        settings.performance.thread_pool_workers = int(os.getenv('THREAD_POOL_WORKERS', str(settings.performance.thread_pool_workers)))
        settings.performance.max_results_per_user = int(os.getenv('MAX_RESULTS_PER_USER', str(settings.performance.max_results_per_user)))

        return settings

    @classmethod
    def load_for_environment(cls, env: Environment) -> 'Settings':
        """根据环境加载配置"""
        # 先从环境变量加载基础配置
        settings = cls.load_from_env()
        settings.environment = env

        # 获取环境特定配置
        env_config = ENVIRONMENT_CONFIGS.get(env, ENVIRONMENT_CONFIGS[Environment.DEFAULT])

        # 应用环境配置
        if 'cache' in env_config:
            cache_config = env_config['cache']
            for key, value in cache_config.items():
                if hasattr(settings.cache, key):
                    setattr(settings.cache, key, value)

        if 'search' in env_config:
            search_config = env_config['search']
            for key, value in search_config.items():
                if hasattr(settings.search, key):
                    setattr(settings.search, key, value)

        if 'database' in env_config:
            db_config = env_config['database']
            for key, value in db_config.items():
                if hasattr(settings.database, key):
                    setattr(settings.database, key, value)

        if 'bot' in env_config:
            bot_config = env_config['bot']
            for key, value in bot_config.items():
                if hasattr(settings.bot, key):
                    setattr(settings.bot, key, value)

        if 'performance' in env_config:
            perf_config = env_config['performance']
            for key, value in perf_config.items():
                if hasattr(settings.performance, key):
                    setattr(settings.performance, key, value)

        return settings

    @classmethod
    def load_from_file(cls, config_file: str = 'large_server') -> 'Settings':
        """从配置文件加载设置（向后兼容）"""
        if config_file == 'large_server':
            return cls.load_for_environment(Environment.LARGE_SERVER)
        else:
            return cls.load_from_env()

    def validate(self) -> bool:
        """验证配置"""
        errors = []

        if self.cache.ttl <= 0:
            errors.append("缓存TTL必须大于0")

        if self.search.max_messages_per_search <= 0:
            errors.append("最大搜索消息数必须大于0")

        if self.search.concurrent_limit <= 0:
            errors.append("并发限制必须大于0")

        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            return False

        return True

    @staticmethod
    def get_environment_config(env: Environment) -> Dict[str, Any]:
        """获取环境特定的配置字典"""
        return ENVIRONMENT_CONFIGS.get(env, ENVIRONMENT_CONFIGS[Environment.DEFAULT])

    @staticmethod
    def list_available_environments() -> Dict[str, str]:
        """列出可用的环境及其描述"""
        return {
            env.value: config["description"]
            for env, config in ENVIRONMENT_CONFIGS.items()
        }

    def get_environment_description(self) -> str:
        """获取当前环境的描述"""
        env_config = self.get_environment_config(self.environment)
        return env_config.get("description", "未知环境")

# 全局设置实例
def _initialize_settings() -> Settings:
    """初始化全局设置"""
    # 检查环境变量指定的环境
    env_name = os.getenv('BOT_ENVIRONMENT', 'default').lower()

    try:
        if env_name == 'large_server':
            env = Environment.LARGE_SERVER
        elif env_name == 'development':
            env = Environment.DEVELOPMENT
        elif env_name == 'production':
            env = Environment.PRODUCTION
        else:
            env = Environment.DEFAULT
    except:
        env = Environment.DEFAULT

    # 向后兼容：检查旧配置文件
    if env == Environment.DEFAULT:
        if os.path.exists('config/large_server.py'):
            env = Environment.LARGE_SERVER

    # 加载配置
    if env == Environment.DEFAULT:
        settings = Settings.load_from_env()
    else:
        settings = Settings.load_for_environment(env)

    # 验证配置
    if not settings.validate():
        logger.warning("配置验证失败，使用默认配置")
        settings = Settings()

    logger.info(f"配置已加载，环境: {settings.environment.value}")
    return settings

settings = _initialize_settings()
