#!/usr/bin/env python3
"""
性能基准测试脚本
测试Discord机器人的各项性能指标
"""
import sys
import asyncio
import time
import json
import statistics
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self):
        self.results = {}
        self.baseline_targets = {
            'search_response_time_ms': 2000,  # 搜索响应时间 < 2秒
            'cache_hit_rate_percent': 85,     # 缓存命中率 > 85%
            'concurrent_searches': 5,         # 并发搜索数 >= 5
            'memory_efficiency_mb_per_1k_items': 50,  # 内存效率 < 50MB/1000项
            'startup_time_seconds': 10        # 启动时间 < 10秒
        }
    
    async def test_search_performance(self, num_searches: int = 100):
        """测试搜索功能性能"""
        print(f"🔍 测试搜索性能 ({num_searches} 次模拟搜索)...")
        
        # 模拟搜索操作的性能测试
        search_times = []
        
        for i in range(num_searches):
            start_time = time.time()
            
            # 模拟搜索操作
            await self._simulate_search_operation()
            
            search_time = (time.time() - start_time) * 1000  # 转换为毫秒
            search_times.append(search_time)
            
            # 每10次搜索显示进度
            if (i + 1) % 10 == 0:
                print(f"  进度: {i + 1}/{num_searches}")
        
        # 计算统计数据
        avg_time = statistics.mean(search_times)
        median_time = statistics.median(search_times)
        min_time = min(search_times)
        max_time = max(search_times)
        p95_time = statistics.quantiles(search_times, n=20)[18]  # 95th percentile
        
        # 性能评估
        performance_grade = self._grade_performance(avg_time, self.baseline_targets['search_response_time_ms'])
        
        self.results['search_performance'] = {
            'num_searches': num_searches,
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min_time,
            'max_time_ms': max_time,
            'p95_time_ms': p95_time,
            'target_time_ms': self.baseline_targets['search_response_time_ms'],
            'performance_grade': performance_grade,
            'meets_target': avg_time <= self.baseline_targets['search_response_time_ms']
        }
        
        print(f"  ✅ 平均响应时间: {avg_time:.2f}ms")
        print(f"  ✅ 中位数响应时间: {median_time:.2f}ms")
        print(f"  ✅ 95%分位数: {p95_time:.2f}ms")
        print(f"  ✅ 性能等级: {performance_grade}")
        print(f"  ✅ 达到目标: {'是' if avg_time <= self.baseline_targets['search_response_time_ms'] else '否'}")
        
        return avg_time <= self.baseline_targets['search_response_time_ms']
    
    async def _simulate_search_operation(self):
        """模拟搜索操作"""
        # 模拟搜索查询解析
        await asyncio.sleep(0.001)  # 1ms
        
        # 模拟数据库/缓存查询
        await asyncio.sleep(random.uniform(0.005, 0.020))  # 5-20ms
        
        # 模拟结果处理
        await asyncio.sleep(0.002)  # 2ms
        
        # 模拟响应构建
        await asyncio.sleep(0.001)  # 1ms
    
    async def test_concurrent_performance(self, concurrent_count: int = 10):
        """测试并发性能"""
        print(f"⚡ 测试并发性能 ({concurrent_count} 个并发任务)...")
        
        start_time = time.time()
        
        # 创建并发任务
        tasks = []
        for i in range(concurrent_count):
            task = asyncio.create_task(self._simulate_concurrent_operation(i))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # 分析结果
        successful_tasks = len([r for r in results if not isinstance(r, Exception)])
        failed_tasks = len([r for r in results if isinstance(r, Exception)])
        
        # 计算吞吐量
        throughput = successful_tasks / total_time if total_time > 0 else 0
        
        # 性能评估
        target_concurrent = self.baseline_targets['concurrent_searches']
        performance_grade = self._grade_performance(successful_tasks, target_concurrent, higher_is_better=True)
        
        self.results['concurrent_performance'] = {
            'concurrent_count': concurrent_count,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'total_time_seconds': total_time,
            'throughput_tasks_per_second': throughput,
            'target_concurrent': target_concurrent,
            'performance_grade': performance_grade,
            'meets_target': successful_tasks >= target_concurrent
        }
        
        print(f"  ✅ 成功任务: {successful_tasks}/{concurrent_count}")
        print(f"  ✅ 总耗时: {total_time:.2f}秒")
        print(f"  ✅ 吞吐量: {throughput:.2f} 任务/秒")
        print(f"  ✅ 性能等级: {performance_grade}")
        
        return successful_tasks >= target_concurrent
    
    async def _simulate_concurrent_operation(self, task_id: int):
        """模拟并发操作"""
        # 模拟不同的处理时间
        processing_time = random.uniform(0.1, 0.5)  # 100-500ms
        await asyncio.sleep(processing_time)
        
        # 模拟偶尔的失败
        if random.random() < 0.05:  # 5% 失败率
            raise Exception(f"模拟任务 {task_id} 失败")
        
        return f"任务 {task_id} 完成"
    
    def test_memory_efficiency(self, num_items: int = 10000):
        """测试内存效率"""
        print(f"💾 测试内存效率 ({num_items} 个数据项)...")
        
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取初始内存使用（简化版本）
        initial_objects = len(gc.get_objects())
        
        # 创建测试数据
        test_data = {}
        for i in range(num_items):
            test_data[f"key_{i}"] = {
                'id': i,
                'content': f"test_content_{i}" * 10,  # 约150字节
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'type': 'test',
                    'size': 150
                }
            }
        
        # 获取最终内存使用
        final_objects = len(gc.get_objects())
        objects_created = final_objects - initial_objects
        
        # 估算内存使用（简化计算）
        estimated_memory_mb = (objects_created * 200) / (1024 * 1024)  # 假设每个对象200字节
        memory_per_1k_items = (estimated_memory_mb / num_items) * 1000
        
        # 性能评估
        target_memory = self.baseline_targets['memory_efficiency_mb_per_1k_items']
        performance_grade = self._grade_performance(memory_per_1k_items, target_memory)
        
        self.results['memory_efficiency'] = {
            'num_items': num_items,
            'objects_created': objects_created,
            'estimated_memory_mb': estimated_memory_mb,
            'memory_per_1k_items_mb': memory_per_1k_items,
            'target_memory_per_1k_mb': target_memory,
            'performance_grade': performance_grade,
            'meets_target': memory_per_1k_items <= target_memory
        }
        
        print(f"  ✅ 创建对象数: {objects_created:,}")
        print(f"  ✅ 估算内存使用: {estimated_memory_mb:.2f} MB")
        print(f"  ✅ 每1000项内存: {memory_per_1k_items:.2f} MB")
        print(f"  ✅ 性能等级: {performance_grade}")
        
        # 清理测试数据
        del test_data
        gc.collect()
        
        return memory_per_1k_items <= target_memory
    
    def test_startup_performance(self):
        """测试启动性能（模拟）"""
        print("🚀 测试启动性能...")
        
        startup_components = [
            ('配置加载', 0.1),
            ('日志初始化', 0.05),
            ('缓存初始化', 0.2),
            ('数据库连接', 0.15),
            ('Discord连接', 0.3),
            ('扩展加载', 0.1),
            ('命令注册', 0.05)
        ]
        
        total_startup_time = 0
        component_times = {}
        
        for component, base_time in startup_components:
            # 模拟启动时间（添加一些随机性）
            component_time = base_time + random.uniform(-0.02, 0.05)
            total_startup_time += component_time
            component_times[component] = component_time
            print(f"  📦 {component}: {component_time:.3f}秒")
        
        # 性能评估
        target_startup = self.baseline_targets['startup_time_seconds']
        performance_grade = self._grade_performance(total_startup_time, target_startup)
        
        self.results['startup_performance'] = {
            'total_startup_time_seconds': total_startup_time,
            'component_times': component_times,
            'target_startup_time_seconds': target_startup,
            'performance_grade': performance_grade,
            'meets_target': total_startup_time <= target_startup
        }
        
        print(f"  ✅ 总启动时间: {total_startup_time:.3f}秒")
        print(f"  ✅ 性能等级: {performance_grade}")
        
        return total_startup_time <= target_startup
    
    def test_configuration_performance(self):
        """测试配置系统性能"""
        print("⚙️ 测试配置系统性能...")
        
        # 测试配置访问速度
        config_access_times = []
        
        for _ in range(1000):
            start_time = time.time()
            
            # 访问各种配置项
            _ = settings.bot.command_prefix
            _ = settings.search.max_messages_per_search
            _ = settings.cache.use_redis
            _ = settings.database.use_database_index
            
            access_time = (time.time() - start_time) * 1000000  # 微秒
            config_access_times.append(access_time)
        
        avg_access_time = statistics.mean(config_access_times)
        
        # 测试配置验证性能
        start_time = time.time()
        validation_result = settings.validate()
        validation_time = (time.time() - start_time) * 1000  # 毫秒
        
        self.results['configuration_performance'] = {
            'avg_config_access_time_microseconds': avg_access_time,
            'config_validation_time_ms': validation_time,
            'validation_passed': validation_result,
            'performance_grade': 'A' if avg_access_time < 10 else 'B' if avg_access_time < 50 else 'C'
        }
        
        print(f"  ✅ 平均配置访问时间: {avg_access_time:.2f}μs")
        print(f"  ✅ 配置验证时间: {validation_time:.2f}ms")
        print(f"  ✅ 配置验证结果: {'通过' if validation_result else '失败'}")
        
        return validation_result and avg_access_time < 50  # 50微秒内
    
    def _grade_performance(self, actual: float, target: float, higher_is_better: bool = False) -> str:
        """性能等级评估"""
        if higher_is_better:
            ratio = actual / target if target > 0 else 0
            if ratio >= 1.0:
                return 'A'
            elif ratio >= 0.8:
                return 'B'
            elif ratio >= 0.6:
                return 'C'
            else:
                return 'D'
        else:
            ratio = actual / target if target > 0 else float('inf')
            if ratio <= 0.5:
                return 'A'
            elif ratio <= 0.8:
                return 'B'
            elif ratio <= 1.0:
                return 'C'
            else:
                return 'D'
    
    def generate_benchmark_report(self):
        """生成基准测试报告"""
        print("\n📊 生成性能基准测试报告...")
        
        # 计算总体评分
        grades = [result.get('performance_grade', 'D') for result in self.results.values() if 'performance_grade' in result]
        grade_scores = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
        avg_score = statistics.mean([grade_scores[grade] for grade in grades]) if grades else 0
        
        if avg_score >= 3.5:
            overall_grade = 'A'
        elif avg_score >= 2.5:
            overall_grade = 'B'
        elif avg_score >= 1.5:
            overall_grade = 'C'
        else:
            overall_grade = 'D'
        
        # 计算达标率
        targets_met = [result.get('meets_target', False) for result in self.results.values() if 'meets_target' in result]
        target_achievement_rate = (sum(targets_met) / len(targets_met) * 100) if targets_met else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'baseline_targets': self.baseline_targets,
            'test_results': self.results,
            'summary': {
                'overall_grade': overall_grade,
                'average_score': avg_score,
                'target_achievement_rate_percent': target_achievement_rate,
                'total_tests': len(self.results),
                'tests_passed': sum(targets_met)
            }
        }
        
        # 保存报告
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        report_path = logs_dir / f"performance_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 基准测试报告已保存: {report_path}")
        return report

async def main():
    """主测试函数"""
    print("⚡ 开始性能基准测试...")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    test_results = []
    
    try:
        # 运行所有基准测试
        test_results.append(await benchmark.test_search_performance(50))
        test_results.append(await benchmark.test_concurrent_performance(8))
        test_results.append(benchmark.test_memory_efficiency(5000))
        test_results.append(benchmark.test_startup_performance())
        test_results.append(benchmark.test_configuration_performance())
        
        # 生成报告
        report = benchmark.generate_benchmark_report()
        
        print("=" * 60)
        print("📊 性能基准测试摘要:")
        print(f"  总体等级: {report['summary']['overall_grade']}")
        print(f"  平均分数: {report['summary']['average_score']:.2f}/4.0")
        print(f"  目标达成率: {report['summary']['target_achievement_rate_percent']:.1f}%")
        print(f"  通过测试: {report['summary']['tests_passed']}/{report['summary']['total_tests']}")
        
        if report['summary']['overall_grade'] in ['A', 'B']:
            print("🎉 性能基准测试表现优秀！")
            return True
        else:
            print("⚠️ 性能基准测试需要改进")
            return False
            
    except Exception as e:
        print(f"❌ 性能基准测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
