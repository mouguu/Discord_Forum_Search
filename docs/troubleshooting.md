# Discord Forum Search Assistant - 故障排除指南

## 常见问题诊断

### 1. 机器人无法启动

#### 症状

- 服务启动失败
- 机器人在Discord中显示离线
- 启动时出现错误信息

#### 诊断步骤

```bash
# 1. 检查服务状态
sudo systemctl status discord-bot

# 2. 查看启动日志
sudo journalctl -u discord-bot --since "5 minutes ago"

# 3. 手动启动查看详细错误
cd /opt/discord-bot
source venv/bin/activate
python main.py
```

#### 常见原因及解决方案

##### Discord Token无效

```bash
# 检查环境变量
echo $DISCORD_TOKEN

# 验证Token格式 (应该是长字符串)
# 重新生成Token:
# 1. 访问 Discord Developer Portal
# 2. 选择应用 > Bot > Reset Token
# 3. 更新 .env 文件
```

##### Python依赖问题

```bash
# 检查Python版本
python --version  # 应该是 3.11+

# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 检查关键依赖
pip show discord.py
```

##### 权限问题

```bash
# 检查文件权限
ls -la /opt/discord-bot/

# 修复权限
sudo chown -R discord-bot:discord-bot /opt/discord-bot/
sudo chmod +x /opt/discord-bot/main.py
```

### 2. 搜索功能异常

#### 搜索异常症状

- 搜索命令无响应
- 搜索结果为空
- 搜索超时

#### 搜索问题诊断

```bash
# 1. 检查搜索相关日志
grep "Search command" /opt/discord-bot/logs/discord_bot.log | tail -10

# 2. 检查并发限制
grep "semaphore" /opt/discord-bot/logs/discord_bot.log | tail -5

# 3. 检查Discord API限制
grep "rate limit" /opt/discord-bot/logs/discord_bot.log | tail -5
```

#### 解决方案

##### 并发限制过低

```python
# 编辑 config/large_server.py
CONCURRENT_SEARCH_LIMIT = 8  # 增加并发数
GUILD_CONCURRENT_SEARCHES = 5  # 增加服务器并发数

# 重启服务
sudo systemctl restart discord-bot
```

##### 缓存问题

```bash
# 清理缓存
redis-cli FLUSHDB  # 如果使用Redis

# 或重启服务清理内存缓存
sudo systemctl restart discord-bot
```

##### Discord API权限不足

```bash
# 检查机器人权限:
# - Read Message History
# - View Channels
# - Send Messages
# - Embed Links
```

### 3. 缓存系统问题

#### 缓存异常症状

- 缓存命中率低
- Redis连接失败
- 内存使用过高

#### Redis连接问题

##### Redis连接诊断

```bash
# 检查Redis服务状态
sudo systemctl status redis-server

# 测试Redis连接
redis-cli ping

# 检查Redis日志
sudo journalctl -u redis-server --since "10 minutes ago"
```

##### Redis连接解决方案

```bash
# 重启Redis服务
sudo systemctl restart redis-server

# 检查Redis配置
sudo nano /etc/redis/redis.conf

# 确保以下配置正确:
# bind 127.0.0.1
# port 6379
# timeout 0
```

#### 内存缓存问题

##### 内存缓存诊断

```bash
# 检查缓存统计
# 在Discord中使用: /bot_stats

# 检查内存使用
ps aux | grep "python main.py"
```

##### 内存缓存解决方案

```python
# 调整缓存配置 config/settings.py
cache.thread_cache_size = 1000  # 减少缓存大小
cache.ttl = 300  # 减少TTL时间
cache.max_items = 5000  # 减少最大项数
```

### 4. 性能问题

#### 性能异常症状

- 响应时间慢
- 高CPU使用率
- 内存泄漏

#### 诊断工具

```bash
# 1. 系统资源监控
htop
# 或
top -p $(pgrep -f "python main.py")

# 2. 内存使用分析
ps -o pid,vsz,rss,comm -p $(pgrep -f "python main.py")

# 3. 网络连接检查
netstat -tlnp | grep python

# 4. 磁盘I/O检查
iotop -p $(pgrep -f "python main.py")
```

#### 性能优化

##### CPU使用率高

```python
# 减少并发搜索数量
CONCURRENT_SEARCH_LIMIT = 3

# 增加搜索超时时间
SEARCH_TIMEOUT = 30.0

# 减少消息处理数量
MAX_MESSAGES_PER_SEARCH = 500
```

##### 内存使用过高

```python
# 减少缓存大小
THREAD_CACHE_SIZE = 500
MAX_ITEMS = 2000

# 减少TTL时间
CACHE_TTL = 180  # 3分钟
```

##### 网络延迟高

```bash
# 检查网络连接
ping discord.com
traceroute discord.com

# 检查DNS解析
nslookup discord.com
```

### 5. 权限和认证问题

#### 权限异常症状

- 403 Forbidden错误
- 无法访问某些频道
- 命令执行失败

#### 权限问题诊断

```bash
# 1. 检查权限相关错误
grep "Forbidden\|403" /opt/discord-bot/logs/discord_bot.log

# 2. 检查机器人角色权限
# 在Discord服务器设置中检查机器人角色

# 3. 检查频道特定权限
# 检查机器人在目标频道的权限
```

#### 权限问题解决方案

##### 机器人权限不足

- 必需权限:
  - View Channels (查看频道)
  - Send Messages (发送消息)
  - Embed Links (嵌入链接)
  - Read Message History (读取消息历史)
  - Use Slash Commands (使用斜杠命令)
- 推荐权限:
  - Manage Messages (管理消息)
  - Add Reactions (添加反应)

##### 频道权限覆盖

- 检查频道设置 > 权限 > 机器人角色
- 确保没有被拒绝关键权限

### 6. 数据库问题

#### 数据库异常症状

- 数据库连接失败
- 数据查询错误
- 数据库文件损坏

#### SQLite问题

##### SQLite问题诊断

```bash
# 检查数据库文件
ls -la /opt/discord-bot/data/searchdb.sqlite

# 检查数据库完整性
sqlite3 /opt/discord-bot/data/searchdb.sqlite "PRAGMA integrity_check;"

# 检查数据库大小
du -h /opt/discord-bot/data/searchdb.sqlite
```

##### SQLite问题解决方案

```bash
# 修复数据库
sqlite3 /opt/discord-bot/data/searchdb.sqlite "VACUUM;"

# 如果数据库损坏，从备份恢复
cp /backup/discord-bot/latest/data/searchdb.sqlite /opt/discord-bot/data/

# 或删除数据库让系统重新创建
rm /opt/discord-bot/data/searchdb.sqlite
sudo systemctl restart discord-bot
```

### 7. Docker相关问题

#### Docker异常症状

- 容器启动失败
- 容器频繁重启
- 卷挂载问题

#### Docker问题诊断

```bash
# 1. 检查容器状态
docker ps -a | grep discord-bot

# 2. 查看容器日志
docker logs discord-bot

# 3. 检查容器资源使用
docker stats discord-bot

# 4. 检查卷挂载
docker inspect discord-bot | grep -A 10 "Mounts"
```

#### Docker问题解决方案

##### 容器启动失败

```bash
# 检查Docker镜像
docker images | grep discord-forum-search-assistant

# 重新构建镜像
docker build -t discord-forum-search-assistant .

# 检查环境变量
docker exec discord-bot env | grep DISCORD_TOKEN
```

##### 容器重启循环

```bash
# 检查退出代码
docker ps -a | grep discord-bot

# 查看详细日志
docker logs --details discord-bot

# 检查资源限制
docker inspect discord-bot | grep -A 5 "Memory"
```

## 日志分析

### 关键日志模式

#### 1. 错误模式

```bash
# 搜索相关错误
grep -E "(Search.*error|search.*failed)" /opt/discord-bot/logs/discord_bot.log

# 缓存相关错误
grep -E "(Cache.*error|Redis.*error)" /opt/discord-bot/logs/discord_bot.log

# Discord API错误
grep -E "(discord.*error|HTTP.*error)" /opt/discord-bot/logs/discord_bot.log
```

#### 2. 性能模式

```bash
# 慢查询
grep -E "(slow|timeout|exceeded)" /opt/discord-bot/logs/discord_bot.log

# 内存警告
grep -E "(memory|Memory)" /opt/discord-bot/logs/discord_bot.log

# 并发限制
grep -E "(semaphore|concurrent|limit)" /opt/discord-bot/logs/discord_bot.log
```

### 日志级别调整

#### 临时调试

```python
# 在 config/settings.py 中临时调整
bot.log_level = "DEBUG"

# 重启服务
sudo systemctl restart discord-bot
```

#### 特定模块调试

```python
# 在代码中临时添加
import logging
logging.getLogger('discord_bot.search').setLevel(logging.DEBUG)
```

## 紧急恢复程序

### 1. 服务完全无响应

```bash
# Step 1: 强制停止
sudo systemctl kill discord-bot
sudo pkill -f "python main.py"

# Step 2: 清理临时文件
rm -f /tmp/discord-bot-*
rm -f /opt/discord-bot/*.pid

# Step 3: 检查系统资源
free -h
df -h

# Step 4: 重启服务
sudo systemctl start discord-bot

# Step 5: 验证启动
sudo systemctl status discord-bot
```

### 2. 数据恢复

```bash
# Step 1: 停止服务
sudo systemctl stop discord-bot

# Step 2: 备份当前状态
mv /opt/discord-bot/data /opt/discord-bot/data_backup_$(date +%Y%m%d_%H%M%S)

# Step 3: 从备份恢复
tar -xzf /backup/discord-bot/latest/data.tar.gz -C /opt/discord-bot/

# Step 4: 修复权限
sudo chown -R discord-bot:discord-bot /opt/discord-bot/data

# Step 5: 重启服务
sudo systemctl start discord-bot
```

### 3. 配置回滚

```bash
# Step 1: 备份当前配置
cp -r /opt/discord-bot/config /opt/discord-bot/config_backup_$(date +%Y%m%d_%H%M%S)

# Step 2: 恢复默认配置
git checkout HEAD -- config/

# Step 3: 重新应用环境变量
source .env

# Step 4: 重启服务
sudo systemctl restart discord-bot
```

## 预防措施

### 1. 监控设置

```bash
# 设置基本监控
*/5 * * * * /opt/discord-bot/scripts/health_check.sh

# 设置告警
*/10 * * * * /opt/discord-bot/scripts/alert_check.sh
```

### 2. 自动备份

```bash
# 每日备份
0 2 * * * /opt/discord-bot/scripts/daily_backup.sh

# 每周完整备份
0 3 * * 0 /opt/discord-bot/scripts/weekly_backup.sh
```

### 3. 日志轮转

```bash
# 配置logrotate
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
