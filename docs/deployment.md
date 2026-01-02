# Discord Forum Search Assistant - 部署指南

## 系统要求

### 最低要求

- **操作系统**: Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+
- **Python**: 3.11 或更高版本
- **内存**: 512MB RAM (小型服务器)
- **存储**: 1GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置

- **操作系统**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **内存**: 2GB+ RAM (大型服务器)
- **存储**: 5GB+ SSD
- **CPU**: 2+ 核心
- **网络**: 100Mbps+ 带宽

## 依赖服务

### Redis (可选但推荐)

#### Ubuntu/Debian 安装

```bash
# 更新包列表
sudo apt update

# 安装Redis
sudo apt install redis-server

# 启动Redis服务
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 验证安装
redis-cli ping
# 应该返回: PONG
```

#### Docker 安装

```bash
# 拉取Redis镜像
docker pull redis:7-alpine

# 运行Redis容器
docker run -d \
  --name discord-bot-redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes

# 验证运行状态
docker exec discord-bot-redis redis-cli ping
```

#### Redis 配置优化

```bash
# 编辑Redis配置文件
sudo nano /etc/redis/redis.conf

# 推荐配置项:
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### PostgreSQL (可选)

#### PostgreSQL 安装配置

```bash
# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE discord_bot;
CREATE USER bot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE discord_bot TO bot_user;
\q
```

## 应用部署

### 1. 获取源代码

```bash
# 克隆仓库
git clone https://github.com/your-username/discord-forum-search-assistant.git
cd discord-forum-search-assistant

# 或下载并解压源代码包
wget https://github.com/your-username/discord-forum-search-assistant/archive/main.zip
unzip main.zip
cd discord-forum-search-assistant-main
```

### 2. 环境准备

```bash
# 创建Python虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置设置

#### 环境变量配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

#### .env 文件示例

```env
# Discord Bot Token (必需)
DISCORD_TOKEN=your_discord_bot_token_here

# 日志级别
LOG_LEVEL=INFO

# 命令前缀
COMMAND_PREFIX=/

# Redis配置 (可选)
USE_REDIS_CACHE=true
REDIS_URL=redis://localhost:6379/0

# 缓存设置
CACHE_TTL=600
THREAD_CACHE_SIZE=1000

# 搜索限制
MAX_MESSAGES_PER_SEARCH=1000
CONCURRENT_SEARCH_LIMIT=5

# 数据库配置 (可选)
USE_DATABASE_INDEX=false
DB_PATH=data/searchdb.sqlite
```

#### 环境配置选择

```bash
# 对于小型服务器，使用默认配置
export BOT_ENVIRONMENT=default

# 对于大型服务器，使用优化配置
export BOT_ENVIRONMENT=large_server

# 对于生产环境
export BOT_ENVIRONMENT=production
```

### 4. Discord Bot 设置

#### 创建Discord应用

1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 "New Application"
3. 输入应用名称并创建
4. 在 "Bot" 页面创建机器人
5. 复制 Bot Token 到 `.env` 文件

#### 设置机器人权限

必需权限:

- `Send Messages` (发送消息)
- `Use Slash Commands` (使用斜杠命令)
- `Embed Links` (嵌入链接)
- `Read Message History` (读取消息历史)
- `View Channels` (查看频道)

推荐权限:

- `Manage Messages` (管理消息)
- `Add Reactions` (添加反应)

#### 邀请机器人到服务器

1. 在Developer Portal的 "OAuth2" > "URL Generator" 页面
2. 选择 "bot" 和 "applications.commands" 作用域
3. 选择上述权限
4. 复制生成的URL并在浏览器中打开
5. 选择服务器并授权

### 5. 启动应用

#### 开发环境启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动机器人
python main.py
```

#### 生产环境启动

##### 使用systemd (推荐)

```bash
# 创建systemd服务文件
sudo nano /etc/systemd/system/discord-bot.service
```

```ini
[Unit]
Description=Discord Forum Search Assistant
After=network.target redis.service

[Service]
Type=simple
User=discord-bot
Group=discord-bot
WorkingDirectory=/opt/discord-bot
Environment=PATH=/opt/discord-bot/venv/bin
ExecStart=/opt/discord-bot/venv/bin/python main.py
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/discord-bot/data /opt/discord-bot/logs

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable discord-bot
sudo systemctl start discord-bot

# 查看状态
sudo systemctl status discord-bot

# 查看日志
sudo journalctl -u discord-bot -f
```

##### 使用Docker

```bash
# 构建镜像
docker build -t discord-forum-search-assistant .

# 运行容器
docker run -d \
  --name discord-bot \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  discord-forum-search-assistant

# 查看日志
docker logs -f discord-bot
```

##### 使用Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  discord-bot:
    build: .
    container_name: discord-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    depends_on:
      - redis
    networks:
      - bot-network

  redis:
    image: redis:7-alpine
    container_name: discord-bot-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - bot-network

volumes:
  redis-data:

networks:
  bot-network:
    driver: bridge
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f discord-bot
```

## 验证部署

### 1. 健康检查

```bash
# 检查机器人是否在线
# 在Discord服务器中使用 /bot_stats 命令

# 检查Redis连接 (如果启用)
redis-cli ping

# 检查日志
tail -f logs/discord_bot.log
```

### 2. 功能测试

```bash
# 测试搜索功能
# 在Discord中使用 /forum_search 命令

# 测试统计功能
# 使用 /server_stats 命令

# 测试语法帮助
# 使用 /search_syntax 命令
```

### 3. 性能监控

```bash
# 查看系统资源使用
htop
# 或
docker stats discord-bot

# 查看Redis内存使用
redis-cli info memory

# 查看机器人统计
# 使用 /bot_stats 命令查看详细性能数据
```

## 故障排除

### 常见问题

#### 1. 机器人无法启动

```bash
# 检查Python版本
python --version

# 检查依赖安装
pip list

# 检查环境变量
echo $DISCORD_TOKEN

# 查看详细错误日志
python main.py
```

#### 2. Redis连接失败

```bash
# 检查Redis服务状态
sudo systemctl status redis-server

# 测试Redis连接
redis-cli ping

# 检查Redis配置
sudo nano /etc/redis/redis.conf
```

#### 3. 权限错误

- 确保机器人有必要的Discord权限
- 检查文件系统权限
- 验证用户权限设置

#### 4. 内存不足

```bash
# 检查内存使用
free -h

# 调整缓存大小
# 编辑配置文件中的 THREAD_CACHE_SIZE
```

### 日志分析

```bash
# 查看错误日志
grep ERROR logs/discord_bot.log

# 查看警告日志
grep WARNING logs/discord_bot.log

# 实时监控日志
tail -f logs/discord_bot.log | grep -E "(ERROR|WARNING)"
```

## 更新和维护

### 应用更新

```bash
# 停止服务
sudo systemctl stop discord-bot

# 备份数据
cp -r data data_backup_$(date +%Y%m%d)

# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl start discord-bot
```

### 数据备份

```bash
# 创建备份脚本
#!/bin/bash
BACKUP_DIR="/backup/discord-bot/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据目录
cp -r /opt/discord-bot/data $BACKUP_DIR/

# 备份Redis数据 (如果使用)
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

### 监控设置

```bash
# 设置日志轮转
sudo nano /etc/logrotate.d/discord-bot

# 内容:
/opt/discord-bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```
