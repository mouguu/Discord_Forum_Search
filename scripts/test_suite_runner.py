#!/usr/bin/env python3
"""
测试套件运行器
统一执行所有监控和性能测试
"""
import sys
import asyncio
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestSuiteRunner:
    """测试套件运行器"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_test_script(self, script_name: str, description: str) -> Dict[str, Any]:
        """运行测试脚本"""
        print(f"\n🧪 运行测试: {description}")
        print("=" * 60)
        
        script_path = project_root / "scripts" / script_name
        
        if not script_path.exists():
            return {
                'status': 'failed',
                'error': f'测试脚本不存在: {script_path}',
                'execution_time': 0
            }
        
        start_time = time.time()
        
        try:
            # 运行测试脚本
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ 测试通过")
                return {
                    'status': 'passed',
                    'execution_time': execution_time,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                print("❌ 测试失败")
                print(f"错误输出: {result.stderr}")
                return {
                    'status': 'failed',
                    'execution_time': execution_time,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print("⏰ 测试超时")
            return {
                'status': 'timeout',
                'execution_time': execution_time,
                'error': '测试执行超时'
            }
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 测试执行出错: {e}")
            return {
                'status': 'error',
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始完整测试套件")
        print("=" * 80)
        
        self.start_time = datetime.now()
        
        # 定义测试套件
        test_suite = [
            ('config_migration_validator.py', '配置迁移验证'),
            ('basic_monitoring_test.py', '基础监控功能测试'),
            ('performance_benchmark.py', '性能基准测试'),
        ]
        
        # 运行每个测试
        for script_name, description in test_suite:
            test_result = self.run_test_script(script_name, description)
            self.results[script_name] = {
                'description': description,
                'result': test_result,
                'timestamp': datetime.now().isoformat()
            }
        
        self.end_time = datetime.now()
        
        # 生成综合报告
        self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        print("\n📊 生成综合测试报告...")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r['result']['status'] == 'passed'])
        failed_tests = len([r for r in self.results.values() if r['result']['status'] == 'failed'])
        error_tests = len([r for r in self.results.values() if r['result']['status'] == 'error'])
        timeout_tests = len([r for r in self.results.values() if r['result']['status'] == 'timeout'])
        
        total_execution_time = sum(r['result']['execution_time'] for r in self.results.values())
        
        # 计算成功率
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 确定整体状态
        if passed_tests == total_tests:
            overall_status = '🎉 全部通过'
            status_color = 'green'
        elif passed_tests >= total_tests * 0.8:
            overall_status = '⚠️ 大部分通过'
            status_color = 'yellow'
        else:
            overall_status = '❌ 需要修复'
            status_color = 'red'
        
        # 生成报告
        report = {
            'test_suite_info': {
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
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }
        
        # 保存报告
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        report_path = logs_dir / f"test_suite_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 显示摘要
        print(f"📋 测试摘要:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过: {passed_tests}")
        print(f"  失败: {failed_tests}")
        print(f"  错误: {error_tests}")
        print(f"  超时: {timeout_tests}")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  总耗时: {total_execution_time:.2f}秒")
        print(f"  整体状态: {overall_status}")
        
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
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 检查失败的测试
        failed_tests = [name for name, info in self.results.items() 
                       if info['result']['status'] in ['failed', 'error']]
        
        if failed_tests:
            recommendations.append("修复失败的测试用例")
            for test in failed_tests:
                recommendations.append(f"  - 检查 {test} 的错误信息并修复")
        
        # 检查性能问题
        slow_tests = [name for name, info in self.results.items() 
                     if info['result']['execution_time'] > 60]  # 超过1分钟
        
        if slow_tests:
            recommendations.append("优化慢速测试的性能")
            for test in slow_tests:
                exec_time = self.results[test]['result']['execution_time']
                recommendations.append(f"  - {test} 执行时间过长 ({exec_time:.1f}s)")
        
        # 检查超时测试
        timeout_tests = [name for name, info in self.results.items() 
                        if info['result']['status'] == 'timeout']
        
        if timeout_tests:
            recommendations.append("解决测试超时问题")
            for test in timeout_tests:
                recommendations.append(f"  - {test} 执行超时，可能需要增加超时时间或优化代码")
        
        # 如果所有测试都通过，提供优化建议
        if not failed_tests and not timeout_tests:
            recommendations.extend([
                "所有测试通过！考虑以下优化:",
                "  - 添加更多边界情况测试",
                "  - 增加负载测试",
                "  - 设置持续集成",
                "  - 定期运行性能基准测试"
            ])
        
        return recommendations
    
    def run_specific_test(self, test_name: str):
        """运行特定测试"""
        test_mapping = {
            'config': ('config_migration_validator.py', '配置迁移验证'),
            'monitoring': ('basic_monitoring_test.py', '基础监控功能测试'),
            'performance': ('performance_benchmark.py', '性能基准测试'),
            'cache': ('cache_performance_test.py', '缓存性能测试')
        }
        
        if test_name not in test_mapping:
            print(f"❌ 未知的测试名称: {test_name}")
            print(f"可用的测试: {', '.join(test_mapping.keys())}")
            return False
        
        script_name, description = test_mapping[test_name]
        result = self.run_test_script(script_name, description)
        
        return result['status'] == 'passed'

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discord机器人测试套件运行器')
    parser.add_argument('--test', '-t', help='运行特定测试 (config, monitoring, performance, cache)')
    parser.add_argument('--all', '-a', action='store_true', help='运行所有测试')
    
    args = parser.parse_args()
    
    runner = TestSuiteRunner()
    
    if args.test:
        success = runner.run_specific_test(args.test)
        sys.exit(0 if success else 1)
    elif args.all or len(sys.argv) == 1:
        runner.run_all_tests()
        
        # 检查是否所有测试都通过
        all_passed = all(info['result']['status'] == 'passed' 
                        for info in runner.results.values())
        sys.exit(0 if all_passed else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
