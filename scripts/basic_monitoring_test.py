#!/usr/bin/env python3
"""
基础监控系统测试脚本
不依赖外部模块的监控功能验证
"""
import sys
import os
import time
import json
import platform
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

class BasicMonitoringTester:
    """基础监控系统测试器"""
    
    def __init__(self):
        self.test_results = {}
        
    def test_config_monitoring(self):
        """测试配置监控功能"""
        print("🔧 测试配置监控功能...")
        
        # 测试配置加载
        config_tests = {
            'bot_config': {
                'command_prefix': settings.bot.command_prefix,
                'log_level': settings.bot.log_level,
                'embed_color': settings.bot.embed_color
            },
            'search_config': {
                'max_messages_per_search': settings.search.max_messages_per_search,
                'messages_per_page': settings.search.messages_per_page,
                'concurrent_limit': settings.search.concurrent_limit
            },
            'cache_config': {
                'use_redis': settings.cache.use_redis,
                'ttl': settings.cache.ttl,
                'thread_cache_size': settings.cache.thread_cache_size
            }
        }
        
        # 验证配置值
        errors = []
        
        # Bot配置验证
        if not isinstance(settings.bot.command_prefix, str):
            errors.append("命令前缀应为字符串")
        if settings.bot.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            errors.append(f"无效的日志级别: {settings.bot.log_level}")
        if not isinstance(settings.bot.embed_color, int):
            errors.append("嵌入颜色应为整数")
            
        # 搜索配置验证
        if settings.search.max_messages_per_search <= 0:
            errors.append("最大搜索消息数应大于0")
        if settings.search.messages_per_page <= 0:
            errors.append("每页消息数应大于0")
        if settings.search.concurrent_limit <= 0:
            errors.append("并发限制应大于0")
            
        # 缓存配置验证
        if not isinstance(settings.cache.use_redis, bool):
            errors.append("Redis使用标志应为布尔值")
        if settings.cache.ttl <= 0:
            errors.append("缓存TTL应大于0")
            
        self.test_results['config_monitoring'] = {
            'status': 'passed' if not errors else 'failed',
            'config_values': config_tests,
            'errors': errors
        }
        
        if not errors:
            print("  ✅ 配置监控测试通过")
            print(f"    - 命令前缀: {settings.bot.command_prefix}")
            print(f"    - 日志级别: {settings.bot.log_level}")
            print(f"    - 最大搜索消息数: {settings.search.max_messages_per_search}")
            print(f"    - 并发限制: {settings.search.concurrent_limit}")
        else:
            print("  ❌ 配置监控测试失败:")
            for error in errors:
                print(f"    - {error}")
                
        return len(errors) == 0
    
    def test_file_system_monitoring(self):
        """测试文件系统监控功能"""
        print("📁 测试文件系统监控功能...")
        
        # 检查关键目录和文件
        critical_paths = [
            'config/settings.py',
            'utils/',
            'cogs/',
            'main.py'
        ]
        
        missing_paths = []
        existing_paths = []
        
        for path in critical_paths:
            full_path = project_root / path
            if full_path.exists():
                existing_paths.append(path)
            else:
                missing_paths.append(path)
        
        # 检查日志目录
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 测试文件写入权限
        test_file = logs_dir / "monitoring_test.tmp"
        write_permission = True
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()  # 删除测试文件
        except Exception as e:
            write_permission = False
            
        self.test_results['file_system_monitoring'] = {
            'status': 'passed' if not missing_paths and write_permission else 'failed',
            'existing_paths': existing_paths,
            'missing_paths': missing_paths,
            'write_permission': write_permission
        }
        
        print(f"  ✅ 存在的关键路径: {len(existing_paths)}/{len(critical_paths)}")
        print(f"  ✅ 日志目录写入权限: {'是' if write_permission else '否'}")
        
        if missing_paths:
            print(f"  ⚠️ 缺失的路径: {missing_paths}")
            
        return len(missing_paths) == 0 and write_permission
    
    def test_system_info_collection(self):
        """测试系统信息收集"""
        print("💻 测试系统信息收集...")
        
        # 收集基础系统信息
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation()
        }
        
        # 收集进程信息
        process_info = {
            'pid': os.getpid(),
            'working_directory': os.getcwd(),
            'environment_variables': len(os.environ)
        }
        
        # 验证信息收集
        required_fields = ['platform', 'python_version', 'pid']
        missing_fields = [field for field in required_fields if not system_info.get(field) and not process_info.get(field)]
        
        self.test_results['system_info_collection'] = {
            'status': 'passed' if not missing_fields else 'failed',
            'system_info': system_info,
            'process_info': process_info,
            'missing_fields': missing_fields
        }
        
        print(f"  ✅ 操作系统: {system_info['platform']} {system_info['platform_release']}")
        print(f"  ✅ Python版本: {system_info['python_version']}")
        print(f"  ✅ 进程ID: {process_info['pid']}")
        print(f"  ✅ 工作目录: {process_info['working_directory']}")
        
        return len(missing_fields) == 0
    
    def test_performance_baseline(self):
        """测试性能基准收集"""
        print("⚡ 测试性能基准收集...")
        
        # 简单的性能测试
        performance_tests = {}
        
        # 测试1: 字符串操作性能
        start_time = time.time()
        test_string = "performance test " * 1000
        for _ in range(1000):
            test_string.upper().lower().strip()
        string_ops_time = time.time() - start_time
        
        # 测试2: 列表操作性能
        start_time = time.time()
        test_list = list(range(10000))
        for _ in range(100):
            sorted(test_list, reverse=True)
        list_ops_time = time.time() - start_time
        
        # 测试3: 字典操作性能
        start_time = time.time()
        test_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}
        for _ in range(1000):
            _ = test_dict.get(f"key_{500}")
        dict_ops_time = time.time() - start_time
        
        performance_tests = {
            'string_operations_ms': string_ops_time * 1000,
            'list_operations_ms': list_ops_time * 1000,
            'dict_operations_ms': dict_ops_time * 1000
        }
        
        # 验证性能基准
        performance_ok = all(time_ms < 1000 for time_ms in performance_tests.values())  # 所有操作应在1秒内完成
        
        self.test_results['performance_baseline'] = {
            'status': 'passed' if performance_ok else 'failed',
            'performance_tests': performance_tests,
            'baseline_met': performance_ok
        }
        
        print(f"  ✅ 字符串操作: {performance_tests['string_operations_ms']:.2f}ms")
        print(f"  ✅ 列表操作: {performance_tests['list_operations_ms']:.2f}ms")
        print(f"  ✅ 字典操作: {performance_tests['dict_operations_ms']:.2f}ms")
        
        return performance_ok
    
    def test_logging_functionality(self):
        """测试日志功能"""
        print("📝 测试日志功能...")
        
        import logging
        
        # 创建测试日志器
        test_logger = logging.getLogger('monitoring_test')
        test_logger.setLevel(logging.INFO)
        
        # 测试日志文件写入
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / "monitoring_test.log"
        
        try:
            # 创建文件处理器
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            test_logger.addHandler(file_handler)
            
            # 写入测试日志
            test_logger.info("监控测试日志 - 开始")
            test_logger.warning("监控测试日志 - 警告")
            test_logger.error("监控测试日志 - 错误")
            
            # 验证日志文件
            log_exists = log_file.exists()
            log_size = log_file.stat().st_size if log_exists else 0
            
            # 清理
            file_handler.close()
            test_logger.removeHandler(file_handler)
            if log_file.exists():
                log_file.unlink()
                
            self.test_results['logging_functionality'] = {
                'status': 'passed' if log_exists and log_size > 0 else 'failed',
                'log_file_created': log_exists,
                'log_file_size': log_size
            }
            
            print(f"  ✅ 日志文件创建: {'成功' if log_exists else '失败'}")
            print(f"  ✅ 日志文件大小: {log_size} 字节")
            
            return log_exists and log_size > 0
            
        except Exception as e:
            self.test_results['logging_functionality'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"  ❌ 日志测试失败: {e}")
            return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n📋 生成基础监控测试报告...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': len([r for r in self.test_results.values() if r['status'] == 'passed']),
                'failed': len([r for r in self.test_results.values() if r['status'] == 'failed']),
                'skipped': len([r for r in self.test_results.values() if r['status'] == 'skipped'])
            }
        }
        
        # 保存报告
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        report_path = logs_dir / "basic_monitoring_test_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 测试报告已保存: {report_path}")
        return report

def main():
    """主测试函数"""
    print("🔍 开始基础监控系统测试...")
    print("=" * 50)
    
    tester = BasicMonitoringTester()
    results = []
    
    try:
        # 运行所有测试
        results.append(tester.test_config_monitoring())
        results.append(tester.test_file_system_monitoring())
        results.append(tester.test_system_info_collection())
        results.append(tester.test_performance_baseline())
        results.append(tester.test_logging_functionality())
        
        # 生成报告
        report = tester.generate_report()
        
        print("=" * 50)
        print("📊 基础监控测试摘要:")
        print(f"  总测试数: {report['summary']['total_tests']}")
        print(f"  通过: {report['summary']['passed']}")
        print(f"  失败: {report['summary']['failed']}")
        print(f"  跳过: {report['summary']['skipped']}")
        
        if all(results):
            print("🎉 所有基础监控测试通过！")
            return True
        else:
            print("❌ 部分基础监控测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 基础监控测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
