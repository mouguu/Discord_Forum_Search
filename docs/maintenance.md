# Discord Forum Search Assistant - 运维手册

## 日常运维任务

### 系统监控

#### 1. 服务状态检查

```bash
# 检查机器人服务状态
sudo systemctl status discord-bot

# 检查Redis服务状态 (如果使用)
sudo systemctl status redis-server

# 检查Docker容器状态 (如果使用Docker)
docker ps | grep discord-bot
```

#### 2. 资源使用监控

```bash
# 检查系统资源使用
htop
# 或使用top
top -p $(pgrep -f "python main.py")

# 检查内存使用详情
ps aux | grep "python main.py"

# 检查磁盘使用
df -h
du -sh /opt/discord-bot/logs/
```

#### 3. 网络连接检查

```bash
# 检查Discord API连接
curl -I https://discord.com/api/v10/gateway

# 检查Redis连接 (如果使用)
redis-cli ping

# 检查端口监听
netstat -tlnp | grep python
```

### 日志管理

#### 1. 日志查看

```bash
# 查看实时日志
tail -f /opt/discord-bot/logs/discord_bot.log

# 查看错误日志
grep ERROR /opt/discord-bot/logs/discord_bot.log | tail -20

# 查看警告日志
grep WARNING /opt/discord-bot/logs/discord_bot.log | tail -20

# 查看特定时间段的日志
grep "2024-01-01" /opt/discord-bot/logs/discord_bot.log
```

#### 2. 日志分析

```bash
# 统计错误数量
grep -c ERROR /opt/discord-bot/logs/discord_bot.log

# 查看最常见的错误
grep ERROR /opt/discord-bot/logs/discord_bot.log | cut -d'-' -f4- | sort | uniq -c | sort -nr

# 分析搜索性能
grep "Search command" /opt/discord-bot/logs/discord_bot.log | tail -10
```

#### 3. 日志清理

```bash
# 手动清理旧日志 (保留最近30天)
find /opt/discord-bot/logs/ -name "*.log" -mtime +30 -delete

# 压缩旧日志
find /opt/discord-bot/logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### 性能优化

#### 1. 缓存管理

```bash
# 查看Redis内存使用 (如果使用Redis)
redis-cli info memory

# 清理Redis缓存
redis-cli FLUSHDB

# 查看缓存命中率
# 使用Discord命令: /bot_stats
```

#### 2. 内存优化

```bash
# 检查内存泄漏
ps -o pid,vsz,rss,comm -p $(pgrep -f "python main.py")

# 重启服务释放内存 (如果需要)
sudo systemctl restart discord-bot
```

#### 3. 数据库维护 (如果使用数据库)

```bash
# SQLite数据库优化
sqlite3 /opt/discord-bot/data/searchdb.sqlite "VACUUM;"

# 检查数据库大小
ls -lh /opt/discord-bot/data/searchdb.sqlite
```

## 定期维护任务

### 每日任务

#### 1. 健康检查脚本

```bash
#!/bin/bash
# /opt/discord-bot/scripts/daily_health_check.sh

LOG_FILE="/opt/discord-bot/logs/health_check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting daily health check" >> $LOG_FILE

# 检查服务状态
if systemctl is-active --quiet discord-bot; then
    echo "[$DATE] ✓ Discord bot service is running" >> $LOG_FILE
else
    echo "[$DATE] ✗ Discord bot service is not running" >> $LOG_FILE
    # 尝试重启服务
    systemctl restart discord-bot
    echo "[$DATE] Attempted to restart discord-bot service" >> $LOG_FILE
fi

# 检查Redis状态
if systemctl is-active --quiet redis-server; then
    echo "[$DATE] ✓ Redis service is running" >> $LOG_FILE
else
    echo "[$DATE] ✗ Redis service is not running" >> $LOG_FILE
fi

# 检查磁盘空间
DISK_USAGE=$(df /opt/discord-bot | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$DATE] ⚠ Disk usage is high: ${DISK_USAGE}%" >> $LOG_FILE
else
    echo "[$DATE] ✓ Disk usage is normal: ${DISK_USAGE}%" >> $LOG_FILE
fi

# 检查内存使用
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "[$DATE] ⚠ Memory usage is high: ${MEMORY_USAGE}%" >> $LOG_FILE
else
    echo "[$DATE] ✓ Memory usage is normal: ${MEMORY_USAGE}%" >> $LOG_FILE
fi

echo "[$DATE] Daily health check completed" >> $LOG_FILE
```

#### 2. 设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加以下行 (每天早上8点执行健康检查)
0 8 * * * /opt/discord-bot/scripts/daily_health_check.sh

# 每小时检查一次服务状态
0 * * * * systemctl is-active --quiet discord-bot || systemctl restart discord-bot
```

### 每周任务

#### 1. 性能报告生成

```bash
#!/bin/bash
# /opt/discord-bot/scripts/weekly_report.sh

REPORT_FILE="/opt/discord-bot/reports/weekly_$(date +%Y%m%d).txt"
mkdir -p /opt/discord-bot/reports

echo "Discord Bot Weekly Performance Report" > $REPORT_FILE
echo "Generated: $(date)" >> $REPORT_FILE
echo "========================================" >> $REPORT_FILE

# 服务运行时间
echo "Service Uptime:" >> $REPORT_FILE
systemctl show discord-bot --property=ActiveEnterTimestamp >> $REPORT_FILE

# 错误统计
echo -e "\nError Statistics (Last 7 days):" >> $REPORT_FILE
grep ERROR /opt/discord-bot/logs/discord_bot.log | \
    awk -v date="$(date -d '7 days ago' '+%Y-%m-%d')" '$0 >= date' | \
    wc -l >> $REPORT_FILE

# 内存使用趋势
echo -e "\nCurrent Memory Usage:" >> $REPORT_FILE
ps -o pid,vsz,rss,comm -p $(pgrep -f "python main.py") >> $REPORT_FILE

# Redis统计 (如果使用)
if systemctl is-active --quiet redis-server; then
    echo -e "\nRedis Statistics:" >> $REPORT_FILE
    redis-cli info stats | grep -E "(total_commands_processed|keyspace_hits|keyspace_misses)" >> $REPORT_FILE
fi
```

### 每月任务

#### 1. 数据备份

```bash
#!/bin/bash
# /opt/discord-bot/scripts/monthly_backup.sh

BACKUP_DIR="/backup/discord-bot/monthly/$(date +%Y%m)"
mkdir -p $BACKUP_DIR

# 停止服务 (可选，用于一致性备份)
# systemctl stop discord-bot

# 备份应用数据
tar -czf $BACKUP_DIR/data_$(date +%Y%m%d).tar.gz /opt/discord-bot/data/

# 备份配置文件
tar -czf $BACKUP_DIR/config_$(date +%Y%m%d).tar.gz /opt/discord-bot/config/

# 备份Redis数据 (如果使用)
if systemctl is-active --quiet redis-server; then
    redis-cli BGSAVE
    cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$(date +%Y%m%d).rdb
fi

# 重启服务 (如果之前停止了)
# systemctl start discord-bot

# 清理旧备份 (保留6个月)
find /backup/discord-bot/monthly/ -type d -mtime +180 -exec rm -rf {} \;
```

#### 2. 系统更新检查

```bash
# 检查系统更新
sudo apt update && sudo apt list --upgradable

# 检查Python包更新
pip list --outdated

# 检查Docker镜像更新 (如果使用Docker)
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"
```

## 故障处理

### 常见故障及解决方案

#### 1. 机器人离线

```bash
# 检查服务状态
sudo systemctl status discord-bot

# 查看最近的错误日志
sudo journalctl -u discord-bot --since "10 minutes ago"

# 重启服务
sudo systemctl restart discord-bot

# 如果问题持续，检查网络连接
ping discord.com
curl -I https://discord.com/api/v10/gateway
```

#### 2. 内存使用过高

```bash
# 检查内存使用详情
ps aux --sort=-%mem | head -10

# 检查是否有内存泄漏
pmap -d $(pgrep -f "python main.py")

# 临时解决：重启服务
sudo systemctl restart discord-bot

# 长期解决：调整缓存配置
# 设置环境变量或修改 config/settings.py
export THREAD_CACHE_SIZE=2000
export CACHE_MAX_ITEMS=5000
```

#### 3. Redis连接问题

```bash
# 检查Redis服务
sudo systemctl status redis-server

# 测试Redis连接
redis-cli ping

# 检查Redis配置
sudo nano /etc/redis/redis.conf

# 重启Redis服务
sudo systemctl restart redis-server

# 如果Redis不可用，机器人会自动降级到内存缓存
```

#### 4. 搜索性能下降

```bash
# 检查并发搜索数量
grep "Search command" /opt/discord-bot/logs/discord_bot.log | tail -20

# 调整并发限制
nano /opt/discord-bot/config/large_server.py
# 修改 CONCURRENT_SEARCH_LIMIT 值

# 清理缓存
redis-cli FLUSHDB  # 如果使用Redis

# 重启服务应用新配置
sudo systemctl restart discord-bot
```
