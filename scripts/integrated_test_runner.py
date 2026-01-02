#!/usr/bin/env python3
"""
整合测试运行器
统一所有测试功能的入口点
"""
import sys
import asyncio
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.monitoring_utils import get_comprehensive_status, system_monitor

class IntegratedTestRunner:
    """整合测试运行器"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # 测试套件定义
        self.test_suites = {
            'quick': [
                ('config_migration_validator.py', '配置验证', 30),
                ('basic_monitoring_test.py', '基础监控', 60)
            ],
            'full': [
                ('config_migration_validator.py', '配置验证', 30),
                ('basic_monitoring_test.py', '基础监控', 60),
                ('performance_benchmark.py', '性能基准', 120),
                ('cache_performance_test.py', '缓存性能', 90)
            ],
            'performance': [
                ('performance_benchmark.py', '性能基准', 120),
                ('cache_performance_test.py', '缓存性能', 90)
            ],
            'monitoring': [
                ('basic_monitoring_test.py', '基础监控', 60)
            ]
        }
    
    def run_test_script(self, script_name: str, description: str, timeout: int = 60) -> Dict[str, Any]:
        """运行单个测试脚本"""
        print(f"\n🧪 运行测试: {description}")
        print("-" * 50)
        
        script_path = project_root / "scripts" / script_name
        
        if not script_path.exists():
            return {
                'status': 'failed',
                'error': f'测试脚本不存在: {script_path}',
                'execution_time': 0,
                'output': ''
            }
        
        start_time = time.time()
        
        try:
            # 运行测试脚本
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ 测试通过")
                return {
                    'status': 'passed',
                    'execution_time': execution_time,
                    'output': result.stdout,
                    'stderr': result.stderr
                }
            else:
                print("❌ 测试失败")
                return {
                    'status': 'failed',
                    'execution_time': execution_time,
                    'output': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print("⏰ 测试超时")
            return {
                'status': 'timeout',
                'execution_time': execution_time,
                'error': f'测试执行超时 ({timeout}秒)'
            }
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 测试执行出错: {e}")
            return {
                'status': 'error',
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def run_test_suite(self, suite_name: str = 'quick') -> bool:
        """运行测试套件"""
        if suite_name not in self.test_suites:
            print(f"❌ 未知的测试套件: {suite_name}")
            print(f"可用套件: {', '.join(self.test_suites.keys())}")
            return False
        
        print(f"🚀 开始运行测试套件: {suite_name}")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        # 获取系统状态
        pre_test_status = get_comprehensive_status()
        
        # 运行测试
        test_suite = self.test_suites[suite_name]
        for script_name, description, timeout in test_suite:
            test_result = self.run_test_script(script_name, description, timeout)
            self.results[script_name] = {
                'description': description,
                'result': test_result,
                'timestamp': datetime.now().isoformat()
            }
        
        self.end_time = datetime.now()
        
        # 获取测试后系统状态
        post_test_status = get_comprehensive_status()
        
        # 生成报告
        success = self.generate_test_report(suite_name, pre_test_status, post_test_status)
        
        return success
    
    def generate_test_report(self, suite_name: str, pre_status: Dict, post_status: Dict) -> bool:
        """生成测试报告"""
        print("\n📊 生成测试报告...")
        print("=" * 60)
        
        # 计算统计信息
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r['result']['status'] == 'passed'])
        failed_tests = len([r for r in self.results.values() if r['result']['status'] == 'failed'])
        error_tests = len([r for r in self.results.values() if r['result']['status'] == 'error'])
        timeout_tests = len([r for r in self.results.values() if r['result']['status'] == 'timeout'])
        
        total_execution_time = sum(r['result']['execution_time'] for r in self.results.values())
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 确定整体状态
        if passed_tests == total_tests:
            overall_status = '🎉 全部通过'
        elif passed_tests >= total_tests * 0.8:
            overall_status = '⚠️ 大部分通过'
        else:
            overall_status = '❌ 需要修复'
        
        # 系统资源对比
        resource_comparison = self.compare_system_resources(pre_status, post_status)
        
        # 生成完整报告
        report = {
            'test_suite_info': {
                'suite_name': suite_name,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'total_duration_seconds': (self.end_time - self.start_time).total_seconds(),
                'total_execution_time_seconds': total_execution_time
            },
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'timeout_tests': timeout_tests,
                'success_rate_percent': success_rate,
                'overall_status': overall_status
            },
            'system_impact': resource_comparison,
            'detailed_results': self.results,
            'pre_test_system_status': pre_status,
            'post_test_system_status': post_status
        }
        
        # 保存报告
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        report_path = logs_dir / f"integrated_test_report_{suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 显示摘要
        print(f"📋 测试套件摘要 ({suite_name}):")
        print(f"  总测试数: {total_tests}")
        print(f"  通过: {passed_tests}")
        print(f"  失败: {failed_tests}")
        print(f"  错误: {error_tests}")
        print(f"  超时: {timeout_tests}")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  总耗时: {total_execution_time:.2f}秒")
        print(f"  整体状态: {overall_status}")
        
        # 显示系统影响
        if resource_comparison['significant_changes']:
            print(f"\n⚠️ 系统资源变化:")
            for change in resource_comparison['changes']:
                print(f"  - {change}")
        
        print(f"\n📄 详细报告: {report_path}")
        
        # 显示详细结果
        print(f"\n📝 详细测试结果:")
        for script_name, test_info in self.results.items():
            status = test_info['result']['status']
            execution_time = test_info['result']['execution_time']
            
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'error': '💥',
                'timeout': '⏰'
            }.get(status, '❓')
            
            print(f"  {status_icon} {test_info['description']}: {status} ({execution_time:.2f}s)")
            
            if status != 'passed' and 'error' in test_info['result']:
                print(f"    错误: {test_info['result']['error']}")
        
        return passed_tests == total_tests
    
    def compare_system_resources(self, pre_status: Dict, post_status: Dict) -> Dict[str, Any]:
        """比较测试前后的系统资源"""
        comparison = {
            'significant_changes': False,
            'changes': []
        }
        
        try:
            pre_resources = pre_status.get('resource_usage', {})
            post_resources = post_status.get('resource_usage', {})
            
            # 比较内存使用
            if 'memory' in pre_resources and 'memory' in post_resources:
                memory_diff = post_resources['memory']['percent'] - pre_resources['memory']['percent']
                if abs(memory_diff) > 5:  # 超过5%变化
                    comparison['changes'].append(f"内存使用变化: {memory_diff:+.1f}%")
                    comparison['significant_changes'] = True
            
            # 比较CPU使用
            if 'cpu' in pre_resources and 'cpu' in post_resources:
                cpu_diff = post_resources['cpu']['percent'] - pre_resources['cpu']['percent']
                if abs(cpu_diff) > 10:  # 超过10%变化
                    comparison['changes'].append(f"CPU使用变化: {cpu_diff:+.1f}%")
                    comparison['significant_changes'] = True
            
        except Exception as e:
            comparison['error'] = str(e)
        
        return comparison
    
    def list_available_tests(self):
        """列出可用的测试"""
        print("📋 可用的测试套件:")
        for suite_name, tests in self.test_suites.items():
            print(f"\n🔧 {suite_name}:")
            for script_name, description, timeout in tests:
                print(f"  - {description} ({script_name}, 超时: {timeout}s)")
    
    def run_health_check(self) -> bool:
        """运行健康检查"""
        print("🏥 运行系统健康检查...")
        
        try:
            status = get_comprehensive_status()
            health = status.get('health_check', {})
            
            print(f"  系统状态: {health.get('status', 'unknown')}")
            
            if health.get('alerts'):
                print("  ⚠️ 告警:")
                for alert in health['alerts']:
                    print(f"    - {alert}")
            
            if health.get('warnings'):
                print("  💡 警告:")
                for warning in health['warnings']:
                    print(f"    - {warning}")
            
            return health.get('status') in ['healthy', 'warning']
            
        except Exception as e:
            print(f"  ❌ 健康检查失败: {e}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='整合测试运行器')
    parser.add_argument('--suite', '-s', default='quick', 
                       help='测试套件 (quick, full, performance, monitoring)')
    parser.add_argument('--list', '-l', action='store_true', 
                       help='列出可用的测试套件')
    parser.add_argument('--health', action='store_true', 
                       help='运行健康检查')
    
    args = parser.parse_args()
    
    runner = IntegratedTestRunner()
    
    if args.list:
        runner.list_available_tests()
        return
    
    if args.health:
        success = runner.run_health_check()
        sys.exit(0 if success else 1)
    
    # 运行测试套件
    success = runner.run_test_suite(args.suite)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
