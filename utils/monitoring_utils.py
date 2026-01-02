"""
统一监控工具模块
整合分散的监控功能到统一接口
"""
import time
import platform
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# 尝试导入psutil，如果失败则使用基础实现
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.start_time = time.time()

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统基础信息"""
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'hostname': platform.node()
        }

    def get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        if not PSUTIL_AVAILABLE:
            return self._get_basic_resource_usage()

        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # 内存信息
            memory = psutil.virtual_memory()

            # 磁盘信息
            disk = psutil.disk_usage('/')

            # 网络信息
            network = psutil.net_io_counters()

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_basic_resource_usage(self) -> Dict[str, Any]:
        """基础资源使用情况（不依赖psutil）"""
        try:
            # 基础系统信息
            result = {
                'cpu': {
                    'percent': 0.0,
                    'count': os.cpu_count() or 1,
                    'load_avg': None
                },
                'memory': {
                    'total_gb': 0.0,
                    'available_gb': 0.0,
                    'used_gb': 0.0,
                    'percent': 0.0
                },
                'disk': {
                    'total_gb': 0.0,
                    'used_gb': 0.0,
                    'free_gb': 0.0,
                    'percent': 0.0
                },
                'network': {
                    'bytes_sent': 0,
                    'bytes_recv': 0,
                    'packets_sent': 0,
                    'packets_recv': 0
                },
                'note': 'Basic implementation - install psutil for detailed metrics'
            }

            # 尝试获取负载平均值（仅Unix系统）
            try:
                if hasattr(os, 'getloadavg'):
                    result['cpu']['load_avg'] = os.getloadavg()
            except:
                pass

            return result
        except Exception as e:
            return {'error': str(e)}

    def get_process_info(self, process_name: Optional[str] = None) -> Dict[str, Any]:
        """获取进程信息"""
        if not PSUTIL_AVAILABLE:
            return self._get_basic_process_info()

        try:
            if process_name:
                # 查找特定进程
                for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                    if process_name.lower() in proc.info['name'].lower():
                        return {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': proc.info['memory_info'].rss / (1024**2),
                            'cpu_percent': proc.info['cpu_percent'],
                            'status': proc.status(),
                            'create_time': proc.create_time()
                        }
                return {'error': f'Process {process_name} not found'}
            else:
                # 当前进程信息
                current_proc = psutil.Process()
                with current_proc.oneshot():
                    return {
                        'pid': current_proc.pid,
                        'memory_mb': current_proc.memory_info().rss / (1024**2),
                        'cpu_percent': current_proc.cpu_percent(),
                        'thread_count': current_proc.num_threads(),
                        'open_files': len(current_proc.open_files()),
                        'connections': len(current_proc.connections()),
                        'create_time': current_proc.create_time()
                    }
        except Exception as e:
            return {'error': str(e)}

    def _get_basic_process_info(self) -> Dict[str, Any]:
        """基础进程信息（不依赖psutil）"""
        try:
            return {
                'pid': os.getpid(),
                'memory_mb': 0.0,
                'cpu_percent': 0.0,
                'thread_count': 1,
                'open_files': 0,
                'connections': 0,
                'create_time': time.time(),
                'note': 'Basic implementation - install psutil for detailed metrics'
            }
        except Exception as e:
            return {'error': str(e)}

    def check_health_thresholds(self, thresholds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """检查健康阈值"""
        if thresholds is None:
            thresholds = {
                'cpu_percent': 70.0,
                'memory_percent': 80.0,
                'disk_percent': 90.0
            }

        resource_usage = self.get_resource_usage()
        health_status = {
            'status': 'healthy',
            'alerts': [],
            'warnings': []
        }

        if 'error' in resource_usage:
            health_status['status'] = 'error'
            health_status['alerts'].append(f"无法获取资源信息: {resource_usage['error']}")
            return health_status

        # 检查CPU使用率
        if resource_usage['cpu']['percent'] > thresholds['cpu_percent']:
            health_status['alerts'].append(
                f"CPU使用率过高: {resource_usage['cpu']['percent']:.1f}% (阈值: {thresholds['cpu_percent']}%)"
            )
            health_status['status'] = 'warning'

        # 检查内存使用率
        if resource_usage['memory']['percent'] > thresholds['memory_percent']:
            health_status['alerts'].append(
                f"内存使用率过高: {resource_usage['memory']['percent']:.1f}% (阈值: {thresholds['memory_percent']}%)"
            )
            health_status['status'] = 'warning'

        # 检查磁盘使用率
        if resource_usage['disk']['percent'] > thresholds['disk_percent']:
            health_status['alerts'].append(
                f"磁盘使用率过高: {resource_usage['disk']['percent']:.1f}% (阈值: {thresholds['disk_percent']}%)"
            )
            health_status['status'] = 'critical'

        return health_status

class PerformanceCollector:
    """性能数据收集器"""

    def __init__(self):
        self.metrics = []
        self.start_time = time.time()

    def record_metric(self, name: str, value: float, timestamp: Optional[float] = None):
        """记录性能指标"""
        if timestamp is None:
            timestamp = time.time()

        self.metrics.append({
            'name': name,
            'value': value,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat()
        })

    def get_metrics_summary(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """获取指标摘要"""
        if metric_name:
            filtered_metrics = [m for m in self.metrics if m['name'] == metric_name]
        else:
            filtered_metrics = self.metrics

        if not filtered_metrics:
            return {'error': 'No metrics found'}

        values = [m['value'] for m in filtered_metrics]

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else None,
            'first_timestamp': filtered_metrics[0]['timestamp'],
            'last_timestamp': filtered_metrics[-1]['timestamp']
        }

    def clear_old_metrics(self, max_age_seconds: int = 3600):
        """清理旧指标"""
        cutoff_time = time.time() - max_age_seconds
        self.metrics = [m for m in self.metrics if m['timestamp'] > cutoff_time]

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alerts = []

    def add_alert(self, level: str, message: str, source: str = "system"):
        """添加告警"""
        alert = {
            'level': level,
            'message': message,
            'source': source,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat()
        }
        self.alerts.append(alert)

    def get_recent_alerts(self, max_age_seconds: int = 3600) -> list:
        """获取最近的告警"""
        cutoff_time = time.time() - max_age_seconds
        return [a for a in self.alerts if a['timestamp'] > cutoff_time]

    def clear_old_alerts(self, max_age_seconds: int = 86400):
        """清理旧告警"""
        cutoff_time = time.time() - max_age_seconds
        self.alerts = [a for a in self.alerts if a['timestamp'] > cutoff_time]

    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        recent_alerts = self.get_recent_alerts()

        summary = {
            'total_alerts': len(self.alerts),
            'recent_alerts': len(recent_alerts),
            'levels': {}
        }

        for alert in recent_alerts:
            level = alert['level']
            if level not in summary['levels']:
                summary['levels'][level] = 0
            summary['levels'][level] += 1

        return summary

# 全局实例
system_monitor = SystemMonitor()
performance_collector = PerformanceCollector()
alert_manager = AlertManager()

def get_comprehensive_status() -> Dict[str, Any]:
    """获取综合状态信息"""
    return {
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': time.time() - system_monitor.start_time,
        'system_info': system_monitor.get_system_info(),
        'resource_usage': system_monitor.get_resource_usage(),
        'process_info': system_monitor.get_process_info(),
        'health_check': system_monitor.check_health_thresholds(),
        'alert_summary': alert_manager.get_alert_summary(),
        'performance_summary': {
            'metrics_count': len(performance_collector.metrics),
            'collection_start': performance_collector.start_time
        }
    }

def cleanup_old_data(max_age_hours: int = 24):
    """清理旧数据"""
    max_age_seconds = max_age_hours * 3600
    performance_collector.clear_old_metrics(max_age_seconds)
    alert_manager.clear_old_alerts(max_age_seconds)
