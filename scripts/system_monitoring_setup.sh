#!/bin/bash
# 系统资源监控配置脚本
# 设置轻量级监控工具和告警阈值

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            PACKAGE_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        elif command -v dnf &> /dev/null; then
            PACKAGE_MANAGER="dnf"
        else
            log_error "不支持的Linux发行版"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    log_info "检测到操作系统: $OS, 包管理器: $PACKAGE_MANAGER"
}

# 安装基础监控工具
install_monitoring_tools() {
    log_info "安装基础监控工具..."
    
    case $PACKAGE_MANAGER in
        "apt")
            sudo apt update
            sudo apt install -y htop iotop nethogs sysstat curl jq
            ;;
        "yum"|"dnf")
            sudo $PACKAGE_MANAGER install -y htop iotop nethogs sysstat curl jq
            ;;
        "brew")
            brew install htop iotop-c sysstat curl jq
            ;;
    esac
    
    log_success "基础监控工具安装完成"
}

# 创建监控脚本目录
setup_monitoring_directory() {
    log_info "设置监控脚本目录..."
    
    MONITOR_DIR="/opt/discord-bot-monitoring"
    sudo mkdir -p $MONITOR_DIR
    sudo mkdir -p $MONITOR_DIR/logs
    sudo mkdir -p $MONITOR_DIR/scripts
    
    # 设置权限
    sudo chown -R $USER:$USER $MONITOR_DIR
    
    log_success "监控目录创建完成: $MONITOR_DIR"
}

# 创建系统资源监控脚本
create_resource_monitor() {
    log_info "创建系统资源监控脚本..."
    
    cat > /opt/discord-bot-monitoring/scripts/resource_monitor.sh << 'EOF'
#!/bin/bash
# 系统资源监控脚本

# 配置
LOG_FILE="/opt/discord-bot-monitoring/logs/resource_monitor.log"
ALERT_LOG="/opt/discord-bot-monitoring/logs/alerts.log"
WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"

# 告警阈值
CPU_THRESHOLD=70
MEMORY_THRESHOLD=80
DISK_THRESHOLD=90
LOAD_THRESHOLD=2.0

# 日志函数
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

send_alert() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "$timestamp - ALERT: $message" >> $ALERT_LOG
    
    # 发送Discord Webhook通知（如果配置了）
    if [[ -n "$WEBHOOK_URL" ]]; then
        curl -H "Content-Type: application/json" \
             -X POST \
             -d "{
                 \"embeds\": [{
                     \"title\": \"🚨 系统告警\",
                     \"description\": \"$message\",
                     \"color\": 15158332,
                     \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\"
                 }]
             }" \
             "$WEBHOOK_URL" 2>/dev/null
    fi
}

# 检查CPU使用率
check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    cpu_usage=${cpu_usage%.*}  # 去除小数部分
    
    if [[ $cpu_usage -gt $CPU_THRESHOLD ]]; then
        send_alert "CPU使用率过高: ${cpu_usage}% (阈值: ${CPU_THRESHOLD}%)"
    fi
    
    log_message "CPU使用率: ${cpu_usage}%"
}

# 检查内存使用率
check_memory() {
    local memory_info=$(free | grep Mem)
    local total=$(echo $memory_info | awk '{print $2}')
    local used=$(echo $memory_info | awk '{print $3}')
    local memory_usage=$((used * 100 / total))
    
    if [[ $memory_usage -gt $MEMORY_THRESHOLD ]]; then
        send_alert "内存使用率过高: ${memory_usage}% (阈值: ${MEMORY_THRESHOLD}%)"
    fi
    
    log_message "内存使用率: ${memory_usage}%"
}

# 检查磁盘使用率
check_disk() {
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        send_alert "磁盘使用率过高: ${disk_usage}% (阈值: ${DISK_THRESHOLD}%)"
    fi
    
    log_message "磁盘使用率: ${disk_usage}%"
}

# 检查系统负载
check_load() {
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    # 使用bc进行浮点数比较
    if command -v bc &> /dev/null; then
        if (( $(echo "$load_avg > $LOAD_THRESHOLD" | bc -l) )); then
            send_alert "系统负载过高: ${load_avg} (阈值: ${LOAD_THRESHOLD})"
        fi
    fi
    
    log_message "系统负载: ${load_avg}"
}

# 检查Discord机器人进程
check_bot_process() {
    local bot_pid=$(pgrep -f "python.*main.py" | head -1)
    
    if [[ -z "$bot_pid" ]]; then
        send_alert "Discord机器人进程未运行"
        log_message "Discord机器人进程: 未运行"
    else
        # 获取进程资源使用情况
        local process_info=$(ps -p $bot_pid -o pid,pcpu,pmem,rss --no-headers)
        if [[ -n "$process_info" ]]; then
            local cpu_percent=$(echo $process_info | awk '{print $2}')
            local mem_percent=$(echo $process_info | awk '{print $3}')
            local mem_rss=$(echo $process_info | awk '{print $4}')
            
            log_message "Discord机器人进程 (PID: $bot_pid): CPU=${cpu_percent}%, 内存=${mem_percent}%, RSS=${mem_rss}KB"
        fi
    fi
}

# 主监控函数
main() {
    log_message "开始系统资源监控检查"
    
    check_cpu
    check_memory
    check_disk
    check_load
    check_bot_process
    
    log_message "系统资源监控检查完成"
}

# 运行监控
main
EOF

    chmod +x /opt/discord-bot-monitoring/scripts/resource_monitor.sh
    log_success "系统资源监控脚本创建完成"
}

# 创建性能报告脚本
create_performance_report() {
    log_info "创建性能报告脚本..."
    
    cat > /opt/discord-bot-monitoring/scripts/performance_report.sh << 'EOF'
#!/bin/bash
# 性能报告生成脚本

REPORT_FILE="/opt/discord-bot-monitoring/logs/performance_report_$(date +%Y%m%d_%H%M%S).json"
WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"

# 收集系统信息
collect_system_info() {
    local uptime_info=$(uptime)
    local cpu_info=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
    local memory_info=$(free -h | grep Mem)
    local disk_info=$(df -h / | tail -1)
    
    cat > $REPORT_FILE << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
    "system_info": {
        "uptime": "$uptime_info",
        "cpu_model": "$cpu_info",
        "memory": "$memory_info",
        "disk": "$disk_info"
    },
    "performance_metrics": {
EOF
}

# 收集Discord机器人性能数据
collect_bot_performance() {
    local bot_pid=$(pgrep -f "python.*main.py" | head -1)
    
    if [[ -n "$bot_pid" ]]; then
        local process_info=$(ps -p $bot_pid -o pid,pcpu,pmem,rss,etime --no-headers)
        local cpu_percent=$(echo $process_info | awk '{print $2}')
        local mem_percent=$(echo $process_info | awk '{print $3}')
        local mem_rss=$(echo $process_info | awk '{print $4}')
        local runtime=$(echo $process_info | awk '{print $5}')
        
        cat >> $REPORT_FILE << EOF
        "bot_process": {
            "pid": $bot_pid,
            "cpu_percent": $cpu_percent,
            "memory_percent": $mem_percent,
            "memory_rss_kb": $mem_rss,
            "runtime": "$runtime"
        },
EOF
    else
        cat >> $REPORT_FILE << EOF
        "bot_process": {
            "status": "not_running"
        },
EOF
    fi
}

# 收集网络统计
collect_network_stats() {
    local network_stats=$(cat /proc/net/dev | grep -E "(eth|wlan|enp)" | head -1)
    
    if [[ -n "$network_stats" ]]; then
        local interface=$(echo $network_stats | awk '{print $1}' | sed 's/://')
        local rx_bytes=$(echo $network_stats | awk '{print $2}')
        local tx_bytes=$(echo $network_stats | awk '{print $10}')
        
        cat >> $REPORT_FILE << EOF
        "network": {
            "interface": "$interface",
            "rx_bytes": $rx_bytes,
            "tx_bytes": $tx_bytes
        }
EOF
    else
        cat >> $REPORT_FILE << EOF
        "network": {
            "status": "no_interface_found"
        }
EOF
    fi
}

# 完成JSON文件
finalize_report() {
    cat >> $REPORT_FILE << EOF
    }
}
EOF
}

# 发送性能报告
send_performance_report() {
    if [[ -n "$WEBHOOK_URL" ]] && [[ -f "$REPORT_FILE" ]]; then
        local summary=$(jq -r '.performance_metrics.bot_process | "CPU: \(.cpu_percent)%, 内存: \(.memory_percent)%, 运行时间: \(.runtime)"' $REPORT_FILE 2>/dev/null || echo "性能数据收集完成")
        
        curl -H "Content-Type: application/json" \
             -X POST \
             -d "{
                 \"embeds\": [{
                     \"title\": \"📊 性能报告\",
                     \"description\": \"$summary\",
                     \"color\": 3447003,
                     \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\"
                 }]
             }" \
             "$WEBHOOK_URL" 2>/dev/null
    fi
}

# 主函数
main() {
    collect_system_info
    collect_bot_performance
    collect_network_stats
    finalize_report
    send_performance_report
    
    echo "性能报告已生成: $REPORT_FILE"
}

main
EOF

    chmod +x /opt/discord-bot-monitoring/scripts/performance_report.sh
    log_success "性能报告脚本创建完成"
}

# 设置定时任务
setup_cron_jobs() {
    log_info "设置定时监控任务..."
    
    # 创建cron任务
    (crontab -l 2>/dev/null; echo "# Discord Bot 监控任务") | crontab -
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/discord-bot-monitoring/scripts/resource_monitor.sh") | crontab -
    (crontab -l 2>/dev/null; echo "0 */6 * * * /opt/discord-bot-monitoring/scripts/performance_report.sh") | crontab -
    
    log_success "定时任务设置完成:"
    log_info "  - 资源监控: 每5分钟执行一次"
    log_info "  - 性能报告: 每6小时执行一次"
}

# 创建日志轮转配置
setup_log_rotation() {
    log_info "设置日志轮转..."
    
    sudo tee /etc/logrotate.d/discord-bot-monitoring > /dev/null << EOF
/opt/discord-bot-monitoring/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 $USER $USER
}
EOF
    
    log_success "日志轮转配置完成"
}

# 创建监控仪表板
create_monitoring_dashboard() {
    log_info "创建监控仪表板..."
    
    cat > /opt/discord-bot-monitoring/scripts/dashboard.sh << 'EOF'
#!/bin/bash
# 简单的监控仪表板

clear
echo "======================================"
echo "    Discord Bot 监控仪表板"
echo "======================================"
echo

# 系统信息
echo "📊 系统信息:"
echo "  运行时间: $(uptime -p)"
echo "  负载: $(uptime | awk -F'load average:' '{print $2}')"
echo

# 资源使用
echo "💾 资源使用:"
echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "  内存: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "  磁盘: $(df / | tail -1 | awk '{print $5}')"
echo

# Discord机器人状态
echo "🤖 Discord机器人状态:"
BOT_PID=$(pgrep -f "python.*main.py" | head -1)
if [[ -n "$BOT_PID" ]]; then
    echo "  状态: 运行中 (PID: $BOT_PID)"
    PROCESS_INFO=$(ps -p $BOT_PID -o pcpu,pmem,rss,etime --no-headers)
    echo "  CPU: $(echo $PROCESS_INFO | awk '{print $1}')%"
    echo "  内存: $(echo $PROCESS_INFO | awk '{print $2}')%"
    echo "  RSS: $(echo $PROCESS_INFO | awk '{print $3}')KB"
    echo "  运行时间: $(echo $PROCESS_INFO | awk '{print $4}')"
else
    echo "  状态: 未运行"
fi
echo

# 最近的告警
echo "🚨 最近告警 (最近5条):"
if [[ -f "/opt/discord-bot-monitoring/logs/alerts.log" ]]; then
    tail -5 /opt/discord-bot-monitoring/logs/alerts.log | while read line; do
        echo "  $line"
    done
else
    echo "  无告警记录"
fi
echo

echo "======================================"
echo "刷新时间: $(date)"
echo "按 Ctrl+C 退出"
EOF

    chmod +x /opt/discord-bot-monitoring/scripts/dashboard.sh
    log_success "监控仪表板创建完成"
}

# 主函数
main() {
    echo "🔧 Discord Bot 系统监控设置"
    echo "================================"
    
    detect_os
    install_monitoring_tools
    setup_monitoring_directory
    create_resource_monitor
    create_performance_report
    setup_cron_jobs
    setup_log_rotation
    create_monitoring_dashboard
    
    echo
    log_success "系统监控设置完成！"
    echo
    echo "📋 使用说明:"
    echo "  1. 查看监控仪表板: /opt/discord-bot-monitoring/scripts/dashboard.sh"
    echo "  2. 手动运行资源检查: /opt/discord-bot-monitoring/scripts/resource_monitor.sh"
    echo "  3. 生成性能报告: /opt/discord-bot-monitoring/scripts/performance_report.sh"
    echo "  4. 查看监控日志: tail -f /opt/discord-bot-monitoring/logs/resource_monitor.log"
    echo "  5. 查看告警日志: tail -f /opt/discord-bot-monitoring/logs/alerts.log"
    echo
    echo "💡 提示:"
    echo "  - 设置环境变量 DISCORD_WEBHOOK_URL 以启用Discord通知"
    echo "  - 监控任务已自动添加到crontab"
    echo "  - 日志会自动轮转，保留30天"
}

# 运行主函数
main "$@"
