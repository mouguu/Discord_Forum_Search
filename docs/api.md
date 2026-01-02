# Discord Forum Search Assistant API 文档

## 概述

本文档详细说明了Discord Forum Search Assistant的主要组件、类和方法的使用方法。

## 核心组件

### 1. 缓存管理器 (CacheManager)

统一的缓存管理接口，支持内存和Redis双层缓存。

#### 初始化

```python
from utils.cache_manager import cache_manager

# 初始化缓存管理器
cache_manager.initialize(
    use_redis=True,
    redis_url="redis://localhost:6379/0",
    cache_ttl=600,
    thread_cache_size=5000
)
```

#### 主要方法

##### `initialize(use_redis, redis_url, cache_ttl, thread_cache_size)`

初始化缓存系统。

**参数:**

- `use_redis` (bool): 是否启用Redis缓存
- `redis_url` (str): Redis连接URL
- `cache_ttl` (int): 缓存生存时间（秒）
- `thread_cache_size` (int): 线程缓存最大项数

**示例:**

```python
cache_manager.initialize(
    use_redis=True,
    redis_url="redis://localhost:6379/0",
    cache_ttl=300,
    thread_cache_size=1000
)
```

##### `get_stats()`

获取缓存统计信息。

**返回值:**

```python
{
    'thread_cache': {
        'memory_size': 1500,
        'hit_rate_pct': 85.2,
        'redis_available': True
    },
    'general_cache': {
        'memory_size': 800,
        'hit_rate_pct': 78.9,
        'redis_available': True
    }
}
```

### 2. 线程缓存 (ThreadCache)

专用于Discord线程数据的缓存管理器。

#### ThreadCache 主要方法

##### `get_thread_stats(thread_id)`

获取线程统计信息。

**参数:**

- `thread_id` (str): Discord线程ID

**返回值:**

```python
{
    'reaction_count': 15,
    'reply_count': 42
}
```

**示例:**

```python
stats = await cache_manager.thread_cache.get_thread_stats("123456789")
if stats:
    print(f"反应数: {stats['reaction_count']}")
    print(f"回复数: {stats['reply_count']}")
```

##### `set_thread_stats(thread_id, stats)`

缓存线程统计信息。

**参数:**

- `thread_id` (str): Discord线程ID
- `stats` (dict): 统计数据

**示例:**

```python
await cache_manager.thread_cache.set_thread_stats(
    "123456789",
    {'reaction_count': 15, 'reply_count': 42}
)
```

### 3. 错误处理装饰器

统一的错误处理机制。

#### `@handle_command_errors()`

为Discord命令添加错误处理。

**示例:**

```python
from utils.error_handler import handle_command_errors

@app_commands.command(name="example")
@handle_command_errors()
async def example_command(self, interaction: discord.Interaction):
    """示例命令"""
    # 命令逻辑
    pass
```

#### `@handle_background_task_errors(task_name)`

为后台任务添加错误处理。

**示例:**

```python
from utils.error_handler import handle_background_task_errors

@handle_background_task_errors("cleanup_task")
async def cleanup_old_data():
    """清理旧数据的后台任务"""
    # 任务逻辑
    pass
```

### 4. 配置管理 (Settings)

统一的配置管理系统。

#### 配置结构

```python
from config.settings import settings

# 机器人配置
settings.bot.command_prefix      # 命令前缀
settings.bot.log_level          # 日志级别
settings.bot.embed_color        # 嵌入颜色
settings.bot.reaction_timeout   # 反应超时时间

# 缓存配置
settings.cache.use_redis        # 是否使用Redis
settings.cache.redis_url        # Redis连接URL
settings.cache.ttl              # 缓存生存时间
settings.cache.thread_cache_size # 线程缓存大小

# 搜索配置
settings.search.max_messages_per_search  # 最大搜索消息数
settings.search.messages_per_page        # 每页消息数
settings.search.concurrent_limit         # 并发限制
settings.search.search_timeout           # 搜索超时时间

# 数据库配置
settings.database.use_database_index     # 是否使用数据库索引
settings.database.db_path               # 数据库路径
settings.database.connection_pool_size  # 连接池大小
```

#### 环境变量支持

所有配置都可以通过环境变量覆盖：

```bash
# 缓存配置
USE_REDIS_CACHE=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=600

# 搜索配置
MAX_MESSAGES_PER_SEARCH=1000
CONCURRENT_SEARCH_LIMIT=5

# 数据库配置
USE_DATABASE_INDEX=true
DB_PATH=data/searchdb.sqlite
CONNECTION_POOL_SIZE=5
```

### 5. 数据库管理器 (DatabaseManager)

SQLite数据库连接池和查询优化（仅在启用数据库索引时可用）。

#### 获取数据库管理器

```python
from utils.database_manager import get_database_manager

db_manager = get_database_manager()
if db_manager:
    # 数据库功能可用
    await db_manager.initialize()
```

#### DatabaseManager 主要方法

##### `upsert_thread_stats(thread_id, guild_id, channel_id, reaction_count, reply_count)`

插入或更新线程统计信息。

**示例:**

```python
await db_manager.upsert_thread_stats(
    thread_id=123456789,
    guild_id=987654321,
    channel_id=111222333,
    reaction_count=15,
    reply_count=42
)
```

##### `get_thread_stats_from_db(thread_id)`

从数据库获取线程统计信息。

**示例:**

```python
stats = await db_manager.get_thread_stats(123456789) # Renamed to avoid conflict with CacheManager method
if stats:
    print(f"反应数: {stats['reaction_count']}")
    print(f"更新时间: {stats['updated_at']}")
```

##### `record_search_history(user_id, guild_id, query, results_count, search_time)`

记录搜索历史。

**示例:**

```python
await db_manager.record_search_history(
    user_id=123456789,
    guild_id=987654321,
    query="Python 教程",
    results_count=25,
    search_time=1.5
)
```

## 最佳实践

### 1. 缓存使用

```python
# 优先使用缓存
cached_data = await cache_manager.thread_cache.get_thread_stats(thread_id)
if cached_data:
    return cached_data

# 缓存未命中时获取新数据
fresh_data = await fetch_fresh_data(thread_id)
await cache_manager.thread_cache.set_thread_stats(thread_id, fresh_data)
return fresh_data
```

### 2. 错误处理

```python
# 为所有命令添加错误处理装饰器
@app_commands.command(name="search")
@handle_command_errors()
async def search_command(self, interaction: discord.Interaction):
    """搜索命令"""
    # 命令逻辑
    pass

# 为后台任务添加错误处理
@handle_background_task_errors("data_cleanup")
async def cleanup_task():
    """数据清理任务"""
    # 清理逻辑
    pass
```

### 3. 配置管理

```python
# 使用统一配置
from config.settings import settings

# 根据配置调整行为
if settings.cache.use_redis:
    # 使用Redis缓存
    pass
else:
    # 使用内存缓存
    pass

# 使用配置中的限制
max_concurrent = settings.search.concurrent_limit
semaphore = asyncio.Semaphore(max_concurrent)
```

### 4. 数据库使用

```python
# 检查数据库是否启用
db_manager = get_database_manager()
if db_manager and settings.database.use_database_index:
    # 使用数据库功能
    await db_manager.record_search_history(...)
else:
    # 使用内存存储
    pass
```

## 性能优化建议

### 1. 缓存策略

- 对于频繁访问的数据，使用较长的TTL
- 对于大型服务器，启用Redis缓存
- 定期清理过期缓存项

### 2. 数据库优化

- 仅在需要持久化存储时启用数据库索引
- 使用连接池避免频繁连接创建
- 定期清理旧数据

### 3. 并发控制

- 使用信号量限制并发操作
- 根据服务器规模调整并发限制
- 实现优雅的降级机制

## 故障排除

### 常见问题

1. **缓存连接失败**
   - 检查Redis服务是否运行
   - 验证连接URL和端口
   - 查看网络连接状态

2. **数据库错误**
   - 确认数据库文件权限
   - 检查磁盘空间
   - 验证SQL语法

3. **性能问题**
   - 监控缓存命中率
   - 检查并发限制设置
   - 分析慢查询日志

### 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger('discord_bot').setLevel(logging.DEBUG)

# 检查缓存状态
stats = cache_manager.get_stats()
print(f"缓存统计: {stats}")

# 验证配置
if not settings.validate():
    print("配置验证失败")
```
