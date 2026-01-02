# 系统服务配置详细步骤

## 概述

本指南提供了将Discord机器人配置为系统服务的详细步骤，支持systemd、Docker和Docker Compose三种方式。

## 方式一：systemd服务配置（推荐用于Linux）

### 1. 创建服务文件

创建systemd服务文件：

```bash
sudo nano /etc/systemd/system/discord-bot.service
```

### 2. 服务文件内容

```ini
[Unit]
Description=Discord Forum Search Assistant Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=discord-bot
Group=discord-bot
WorkingDirectory=/opt/discord-bot
Environment=PATH=/opt/discord-bot/venv/bin
ExecStart=/opt/discord-bot/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/discord-bot/data /opt/discord-bot/logs

# 资源限制
LimitNOFILE=65536
MemoryMax=2G

[Install]
WantedBy=multi-user.target
```

### 3. 创建专用用户

```bash
# 创建系统用户
sudo useradd --system --shell /bin/false --home /opt/discord-bot discord-bot

# 创建目录
sudo mkdir -p /opt/discord-bot/{data,logs}

# 复制项目文件
sudo cp -r /path/to/your/project/* /opt/discord-bot/

# 设置权限
sudo chown -R discord-bot:discord-bot /opt/discord-bot
sudo chmod -R 755 /opt/discord-bot
sudo chmod -R 750 /opt/discord-bot/data
sudo chmod -R 750 /opt/discord-bot/logs
```

### 4. 创建Python虚拟环境

```bash
# 切换到项目目录
cd /opt/discord-bot

# 创建虚拟环境
sudo -u discord-bot python3 -m venv venv

# 激活虚拟环境并安装依赖
sudo -u discord-bot /opt/discord-bot/venv/bin/pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
# 创建环境文件
sudo nano /opt/discord-bot/.env
```

```env
# Discord配置
DISCORD_TOKEN=your_discord_bot_token_here

# 缓存配置
USE_REDIS_CACHE=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=600

# 日志配置
LOG_LEVEL=INFO

# 数据路径
DB_PATH=/opt/discord-bot/data/searchdb.sqlite
```

```bash
# 设置环境文件权限
sudo chown discord-bot:discord-bot /opt/discord-bot/.env
sudo chmod 600 /opt/discord-bot/.env
```

### 6. 启动和管理服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable discord-bot

# 启动服务
sudo systemctl start discord-bot

# 检查服务状态
sudo systemctl status discord-bot

# 查看日志
sudo journalctl -u discord-bot -f

# 重启服务
sudo systemctl restart discord-bot

# 停止服务
sudo systemctl stop discord-bot
```

### 7. 日志轮转配置

创建日志轮转配置：

```bash
sudo nano /etc/logrotate.d/discord-bot
```

```text
/opt/discord-bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 discord-bot discord-bot
    postrotate
        systemctl reload discord-bot
    endscript
}
```

## 方式二：Docker配置

### 1. 创建Dockerfile

```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 设置权限
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# 启动命令
CMD ["python", "main.py"]
```

### 2. 构建和运行Docker镜像

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

# 查看容器状态
docker ps

# 查看日志
docker logs -f discord-bot

# 进入容器
docker exec -it discord-bot bash

# 停止容器
docker stop discord-bot

# 重启容器
docker restart discord-bot
```

### 3. Docker资源限制

```bash
# 运行时设置资源限制
docker run -d \
  --name discord-bot \
  --restart unless-stopped \
  --memory=2g \
  --cpus=1.5 \
  --memory-swap=2g \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  discord-forum-search-assistant
```

## 方式三：Docker Compose配置（推荐）

### 1. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  discord-bot:
    build: .
    container_name: discord-bot
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - USE_REDIS_CACHE=true
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
    networks:
      - bot-network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.5'
        reservations:
          memory: 512M
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    container_name: discord-bot-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - bot-network
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  # 可选：监控服务
  prometheus:
    image: prom/prometheus:latest
    container_name: discord-bot-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - bot-network
    profiles:
      - monitoring

volumes:
  redis-data:
  prometheus-data:

networks:
  bot-network:
    driver: bridge
```

### 2. 环境变量文件

创建 `.env` 文件：

```env
# Discord配置
DISCORD_TOKEN=your_discord_bot_token_here

# 应用配置
LOG_LEVEL=INFO
CACHE_TTL=600
MAX_MESSAGES_PER_SEARCH=1000

# 数据库配置（可选）
USE_DATABASE_INDEX=false
DB_PATH=/app/data/searchdb.sqlite
```

### 3. Docker Compose操作命令

```bash
# 启动所有服务
docker-compose up -d

# 启动包含监控的服务
docker-compose --profile monitoring up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f discord-bot

# 重启特定服务
docker-compose restart discord-bot

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 更新服务
docker-compose pull
docker-compose up -d --build

# 扩展服务（多实例）
docker-compose up -d --scale discord-bot=2
```

### 4. 生产环境优化

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  discord-bot:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - USE_REDIS_CACHE=true
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=WARNING
      - USE_DATABASE_INDEX=true
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - bot-network
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3

  redis:
    image: redis:7-alpine
    restart: always
    command: >
      redis-server
      --appendonly yes
      --maxmemory 1gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    volumes:
      - redis-data:/data
    networks:
      - bot-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  redis-data:
    driver: local

networks:
  bot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

使用生产配置：

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 监控和维护

### 1. 健康检查脚本

创建 `scripts/health-check.sh`：

```bash
#!/bin/bash

# 健康检查脚本
SERVICE_NAME="discord-bot"
LOG_FILE="/var/log/discord-bot-health.log"

check_service() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): $SERVICE_NAME is running" >> $LOG_FILE
        return 0
    else
        echo "$(date): $SERVICE_NAME is not running" >> $LOG_FILE
        return 1
    fi
}

check_redis() {
    if redis-cli ping > /dev/null 2>&1; then
        echo "$(date): Redis is responding" >> $LOG_FILE
        return 0
    else
        echo "$(date): Redis is not responding" >> $LOG_FILE
        return 1
    fi
}

restart_service() {
    echo "$(date): Restarting $SERVICE_NAME" >> $LOG_FILE
    systemctl restart $SERVICE_NAME
    sleep 10
}

# 主检查逻辑
if ! check_service; then
    restart_service
    if ! check_service; then
        echo "$(date): Failed to restart $SERVICE_NAME" >> $LOG_FILE
        # 发送告警通知
        curl -X POST "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" \
             -H "Content-Type: application/json" \
             -d '{"content": "🚨 Discord Bot服务重启失败！"}'
    fi
fi

check_redis
```

设置定时任务：

```bash
# 编辑crontab
crontab -e

# 添加健康检查（每5分钟检查一次）
*/5 * * * * /opt/discord-bot/scripts/health-check.sh
```

### 2. 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/discord-bot"
DATE=$(date +%Y%m%d_%H%M%S)
DATA_DIR="/opt/discord-bot/data"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
tar -czf "$BACKUP_DIR/data_backup_$DATE.tar.gz" -C "$DATA_DIR" .

# 备份Redis数据（如果使用）
if systemctl is-active --quiet redis-server; then
    redis-cli BGSAVE
    sleep 5
    cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"
fi

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete

echo "$(date): Backup completed" >> /var/log/discord-bot-backup.log
```

设置自动备份：

```bash
# 每天凌晨2点备份
0 2 * * * /opt/discord-bot/scripts/backup.sh
```

## 故障排除

### 常见问题

1. **服务启动失败**

   ```bash
   # 检查服务状态
   sudo systemctl status discord-bot

   # 查看详细日志
   sudo journalctl -u discord-bot -n 50

   # 检查配置文件
   sudo systemctl cat discord-bot
   ```

2. **权限问题**

   ```bash
   # 检查文件权限
   ls -la /opt/discord-bot/

   # 修复权限
   sudo chown -R discord-bot:discord-bot /opt/discord-bot/
   sudo chmod -R 755 /opt/discord-bot/
   ```

3. **Docker容器问题**

   ```bash
   # 检查容器状态
   docker ps -a

   # 查看容器日志
   docker logs discord-bot

   # 进入容器调试
   docker exec -it discord-bot bash
   ```

### 性能优化

1. **系统级优化**

   ```bash
   # 增加文件描述符限制
   echo "discord-bot soft nofile 65536" >> /etc/security/limits.conf
   echo "discord-bot hard nofile 65536" >> /etc/security/limits.conf
   ```

2. **Docker优化**

   ```bash
   # 使用多阶段构建减小镜像大小
   # 启用BuildKit
   export DOCKER_BUILDKIT=1
   docker build --target production -t discord-bot .
   ```

这些配置提供了完整的生产环境部署方案，包括安全性、可靠性和可维护性的考虑。
