# 配置系统文档

## 概述

Discord Forum Search Assistant 使用统一的配置系统，提供类型安全、环境管理和简洁的API设计。所有配置都集中在单个文件中，便于管理和维护。

## 文件结构

```text
config/
├── settings.py          # 主配置文件 - 统一配置管理
└── README.md           # 本文档
```

## 配置系统特性

### ✅ 结构化配置

使用 Python dataclasses 提供类型安全和IDE支持：

```python
from config.settings import settings

# 清晰的配置结构
settings.bot.command_prefix      # 机器人配置
settings.cache.use_redis         # 缓存配置
settings.search.max_messages_per_search     # 搜索配置
settings.database.use_database_index      # 数据库配置
settings.performance.enable_performance_monitoring  # 性能配置
```

### ✅ 环境管理

支持多种预设环境，可根据部署需求自动调整配置：

- `default` - 默认配置，适用于中小型服务器
- `large_server` - 大型服务器优化配置
- `development` - 开发环境配置
- `production` - 生产环境配置

### ✅ 类型安全

所有配置项都有明确的类型定义，提供IDE自动补全和错误检查。

## 使用方法

### 基本使用

```python
from config.settings import settings

# 访问配置
max_messages = settings.search.max_messages_per_search
use_redis = settings.cache.use_redis
log_level = settings.bot.log_level
```

### 环境切换

#### 方法1: 环境变量

```bash
export BOT_ENVIRONMENT=large_server
python main.py
```

#### 方法2: .env 文件

```bash
echo "BOT_ENVIRONMENT=large_server" >> .env
```

#### 方法3: 配置管理脚本

```bash
# 查看可用环境
python scripts/config_manager.py list

# 设置环境
python scripts/config_manager.py set large_server

# 查看当前配置
python scripts/config_manager.py current

# 比较环境差异
python scripts/config_manager.py compare default large_server
```

### 程序化环境加载

```python
from config.settings import Settings, Environment

# 加载特定环境
settings = Settings.load_for_environment(Environment.LARGE_SERVER)

# 或使用字符串
settings = Settings.load_for_environment(Environment('production'))
```

## 配置分类

### 🤖 Bot配置 (`settings.bot`)

- `command_prefix`: 命令前缀
- `log_level`: 日志级别
- `log_dir`: 日志目录
- `embed_color`: 嵌入消息颜色
- `reaction_timeout`: 反应超时时间

### 💾 缓存配置 (`settings.cache`)

- `use_redis`: 是否使用Redis
- `redis_url`: Redis连接URL
- `ttl`: 缓存生存时间
- `thread_cache_size`: 线程缓存大小
- `max_items`: 最大缓存项数

### 🔍 搜索配置 (`settings.search`)

- `max_messages_per_search`: 每次搜索最大消息数
- `messages_per_page`: 每页显示消息数
- `concurrent_limit`: 并发搜索限制
- `guild_concurrent_searches`: 每服务器并发搜索数
- `user_search_cooldown`: 用户搜索冷却时间
- `search_timeout`: 搜索超时时间
- `max_embed_field_length`: 嵌入字段最大长度
- `use_incremental_loading`: 是否使用增量加载
- `message_batch_size`: 消息批量大小
- `max_archived_threads`: 最大归档线程数

### 🗄️ 数据库配置 (`settings.database`)

- `use_database_index`: 是否使用数据库索引
- `db_path`: 数据库文件路径
- `connection_pool_size`: 连接池大小

### ⚡ 性能配置 (`settings.performance`)

- `enable_performance_monitoring`: 启用性能监控
- `optimize_message_content`: 优化消息内容
- `max_content_length`: 最大内容长度
- `thread_pool_workers`: 线程池工作者数
- `max_results_per_user`: 每用户最大结果数
- `rate_limit_enabled`: 启用速率限制

## 环境配置详情

### Default (默认)

适用于中小型服务器的平衡配置。

### Large Server (大型服务器)

针对10000+用户的大型服务器优化：

- 启用Redis缓存
- 增加并发限制
- 启用数据库索引
- 启用性能监控
- 优化内存使用

### Development (开发)

开发和测试环境：

- 调试日志级别
- 禁用Redis
- 较小的限制值
- 禁用性能监控

### Production (生产)

生产环境优化：

- 警告日志级别
- 启用所有优化
- 更大的缓存和限制
- 完整监控

## 配置验证

运行配置验证脚本确保系统正常工作：

```bash
python scripts/config_validator.py
```

## 故障排除

### 常见问题

1. **配置验证失败**

   ```bash
   python scripts/config_manager.py validate
   ```

2. **环境未生效**
   - 检查 `.env` 文件中的 `BOT_ENVIRONMENT` 设置
   - 确保重启了机器人

3. **导入错误**
   - 确保使用正确的导入方式: `from config.settings import settings`
   - 检查是否有拼写错误

### 调试命令

```bash
# 查看当前配置
python scripts/config_manager.py current

# 验证配置
python scripts/config_manager.py validate

# 查看环境详情
python scripts/config_manager.py show large_server
```

## 最佳实践

1. **使用环境变量**: 在不同部署环境中使用 `BOT_ENVIRONMENT` 环境变量
2. **配置验证**: 部署前运行配置验证
3. **监控配置**: 在生产环境启用性能监控
4. **文档更新**: 修改配置时更新相关文档

## 扩展配置

如需添加新的配置项：

1. 在 `settings.py` 中的相应 dataclass 添加字段
2. 在 `ENVIRONMENT_CONFIGS` 中为各环境添加默认值
3. 更新文档

## 配置系统架构

### 单文件设计

配置系统完全整合在 `config/settings.py` 中：

- **环境配置**: 内置在 `ENVIRONMENT_CONFIGS` 字典中
- **数据类**: 使用 Python dataclasses 提供类型安全
- **环境管理**: 内置环境切换和验证功能
- **简洁API**: 直接导入使用，无需额外配置

### 配置加载流程

1. 检查 `BOT_ENVIRONMENT` 环境变量
2. 从 `ENVIRONMENT_CONFIGS` 加载对应环境配置
3. 应用环境变量覆盖
4. 验证配置完整性
5. 返回配置实例

### 设计原则

- **单一职责**: 一个文件管理所有配置
- **类型安全**: 完整的类型注解和验证
- **环境感知**: 自动适配不同部署环境
- **易于扩展**: 简单添加新配置项和环境
