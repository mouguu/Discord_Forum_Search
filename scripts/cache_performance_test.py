#!/usr/bin/env python3
"""
缓存性能测试脚本
测试缓存系统的性能和故障转移机制
"""
import sys
import asyncio
import time
import random
import statistics
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.cache_manager import cache_manager
from config.settings import settings

class CachePerformanceTester:
    """缓存性能测试器"""
    
    def __init__(self):
        self.test_results = {}
        
    async def test_cache_hit_rate(self, num_operations=1000):
        """测试缓存命中率"""
        print(f"🎯 测试缓存命中率 ({num_operations} 次操作)...")
        
        # 初始化缓存
        cache_manager.initialize(
            use_redis=settings.cache.use_redis,
            redis_url=settings.cache.redis_url,
            cache_ttl=settings.cache.ttl,
            thread_cache_size=settings.cache.thread_cache_size
        )
        
        # 准备测试数据
        test_keys = [f"test_key_{i}" for i in range(100)]
        test_data = {key: f"test_data_{i}" for i, key in enumerate(test_keys)}
        
        # 写入测试数据
        start_time = time.time()
        for key, value in test_data.items():
            await cache_manager.general_cache.set(key, value)
        write_time = time.time() - start_time
        
        # 执行读取操作（80%命中，20%未命中）
        hits = 0
        misses = 0
        read_times = []
        
        for _ in range(num_operations):
            # 80%概率选择存在的key，20%概率选择不存在的key
            if random.random() < 0.8:
                key = random.choice(test_keys)
                expected_hit = True
            else:
                key = f"nonexistent_key_{random.randint(1000, 9999)}"
                expected_hit = False
            
            start_read = time.time()
            result = await cache_manager.general_cache.get(key)
            read_time = time.time() - start_read
            read_times.append(read_time)
            
            if result is not None:
                hits += 1
            else:
                misses += 1
        
        # 计算统计数据
        hit_rate = (hits / num_operations) * 100
        avg_read_time = statistics.mean(read_times)
        median_read_time = statistics.median(read_times)
        
        # 获取缓存统计
        cache_stats = cache_manager.get_stats()
        
        self.test_results['cache_hit_rate'] = {
            'num_operations': num_operations,
            'hits': hits,
            'misses': misses,
            'hit_rate_percent': hit_rate,
            'write_time_seconds': write_time,
            'avg_read_time_ms': avg_read_time * 1000,
            'median_read_time_ms': median_read_time * 1000,
            'cache_stats': cache_stats
        }
        
        print(f"  ✅ 命中率: {hit_rate:.1f}% ({hits}/{num_operations})")
        print(f"  ✅ 平均读取时间: {avg_read_time * 1000:.2f}ms")
        print(f"  ✅ 中位数读取时间: {median_read_time * 1000:.2f}ms")
        print(f"  ✅ 写入时间: {write_time:.2f}秒")
        
        # 验证命中率目标（应该接近80%）
        expected_hit_rate = 80.0
        tolerance = 5.0  # 5%容差
        
        if abs(hit_rate - expected_hit_rate) <= tolerance:
            print(f"  ✅ 命中率符合预期 (目标: {expected_hit_rate}% ± {tolerance}%)")
            return True
        else:
            print(f"  ⚠️ 命中率偏离预期 (目标: {expected_hit_rate}% ± {tolerance}%, 实际: {hit_rate:.1f}%)")
            return False
    
    async def test_cache_performance_comparison(self):
        """测试启用/禁用缓存的性能对比"""
        print("⚡ 测试缓存性能对比...")
        
        # 准备测试数据
        test_data = {f"perf_key_{i}": f"performance_test_data_{i}" * 10 for i in range(50)}
        num_reads = 200
        
        # 测试1: 启用缓存
        print("  📊 测试启用缓存的性能...")
        cache_manager.initialize(use_redis=settings.cache.use_redis)
        
        # 预热缓存
        for key, value in test_data.items():
            await cache_manager.general_cache.set(key, value)
        
        # 测试读取性能
        start_time = time.time()
        for _ in range(num_reads):
            key = random.choice(list(test_data.keys()))
            await cache_manager.general_cache.get(key)
        cached_time = time.time() - start_time
        
        # 测试2: 模拟无缓存（每次都未命中）
        print("  📊 测试无缓存的性能...")
        start_time = time.time()
        for _ in range(num_reads):
            # 模拟数据库查询延迟
            await asyncio.sleep(0.001)  # 1ms延迟模拟数据库查询
        uncached_time = time.time() - start_time
        
        # 计算性能提升
        performance_improvement = ((uncached_time - cached_time) / uncached_time) * 100
        
        self.test_results['cache_performance_comparison'] = {
            'num_reads': num_reads,
            'cached_time_seconds': cached_time,
            'uncached_time_seconds': uncached_time,
            'performance_improvement_percent': performance_improvement,
            'speedup_factor': uncached_time / cached_time if cached_time > 0 else 0
        }
        
        print(f"  ✅ 启用缓存时间: {cached_time:.3f}秒")
        print(f"  ✅ 无缓存时间: {uncached_time:.3f}秒")
        print(f"  ✅ 性能提升: {performance_improvement:.1f}%")
        print(f"  ✅ 加速倍数: {uncached_time / cached_time:.1f}x")
        
        # 验证性能提升目标（应该有显著提升）
        min_improvement = 30.0  # 至少30%提升
        
        if performance_improvement >= min_improvement:
            print(f"  ✅ 性能提升符合预期 (目标: ≥{min_improvement}%)")
            return True
        else:
            print(f"  ⚠️ 性能提升低于预期 (目标: ≥{min_improvement}%, 实际: {performance_improvement:.1f}%)")
            return False
    
    async def test_redis_failover(self):
        """测试Redis故障转移机制"""
        print("🔄 测试Redis故障转移机制...")
        
        if not settings.cache.use_redis:
            print("  ⚠️ Redis未启用，跳过故障转移测试")
            self.test_results['redis_failover'] = {
                'status': 'skipped',
                'reason': 'Redis not enabled'
            }
            return True
        
        try:
            # 初始化缓存（启用Redis）
            cache_manager.initialize(
                use_redis=True,
                redis_url=settings.cache.redis_url
            )
            
            # 测试正常Redis操作
            test_key = "failover_test"
            test_value = "failover_test_value"
            
            await cache_manager.general_cache.set(test_key, test_value)
            result = await cache_manager.general_cache.get(test_key)
            
            redis_working = result == test_value
            print(f"  📊 Redis正常工作: {'是' if redis_working else '否'}")
            
            # 模拟Redis故障（通过使用错误的URL）
            print("  🔧 模拟Redis连接故障...")
            cache_manager.initialize(
                use_redis=True,
                redis_url="redis://invalid_host:6379/0"  # 无效的Redis URL
            )
            
            # 测试故障转移到内存缓存
            fallback_key = "fallback_test"
            fallback_value = "fallback_test_value"
            
            start_time = time.time()
            await cache_manager.general_cache.set(fallback_key, fallback_value)
            result = await cache_manager.general_cache.get(fallback_key)
            fallback_time = time.time() - start_time
            
            fallback_working = result == fallback_value
            print(f"  📊 内存缓存故障转移: {'成功' if fallback_working else '失败'}")
            print(f"  📊 故障转移时间: {fallback_time * 1000:.2f}ms")
            
            self.test_results['redis_failover'] = {
                'redis_initially_working': redis_working,
                'fallback_working': fallback_working,
                'fallback_time_ms': fallback_time * 1000,
                'status': 'passed' if fallback_working else 'failed'
            }
            
            return fallback_working
            
        except Exception as e:
            print(f"  ❌ 故障转移测试出错: {e}")
            self.test_results['redis_failover'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    async def test_cache_memory_usage(self):
        """测试缓存内存使用"""
        print("💾 测试缓存内存使用...")
        
        # 初始化缓存
        cache_manager.initialize()
        
        # 获取初始内存使用
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 写入大量数据
        large_data = "x" * 1024  # 1KB数据
        num_items = 1000
        
        start_time = time.time()
        for i in range(num_items):
            await cache_manager.general_cache.set(f"memory_test_{i}", large_data)
        write_time = time.time() - start_time
        
        # 获取写入后内存使用
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 获取缓存统计
        cache_stats = cache_manager.get_stats()
        
        self.test_results['cache_memory_usage'] = {
            'num_items': num_items,
            'item_size_bytes': len(large_data),
            'total_data_size_kb': (num_items * len(large_data)) / 1024,
            'initial_memory_mb': initial_memory / (1024 * 1024),
            'final_memory_mb': final_memory / (1024 * 1024),
            'memory_increase_mb': memory_increase / (1024 * 1024),
            'write_time_seconds': write_time,
            'cache_stats': cache_stats
        }
        
        print(f"  ✅ 写入项目数: {num_items}")
        print(f"  ✅ 单项大小: {len(large_data)} 字节")
        print(f"  ✅ 总数据大小: {(num_items * len(large_data)) / 1024:.1f} KB")
        print(f"  ✅ 内存增长: {memory_increase / (1024 * 1024):.1f} MB")
        print(f"  ✅ 写入时间: {write_time:.2f}秒")
        
        return True

async def main():
    """主测试函数"""
    print("⚡ 开始缓存性能测试...")
    print("=" * 50)
    
    tester = CachePerformanceTester()
    results = []
    
    try:
        # 运行所有测试
        results.append(await tester.test_cache_hit_rate())
        results.append(await tester.test_cache_performance_comparison())
        results.append(await tester.test_redis_failover())
        results.append(await tester.test_cache_memory_usage())
        
        # 保存测试结果
        import json
        report_path = project_root / "logs" / "cache_performance_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'test_results': tester.test_results,
                'summary': {
                    'total_tests': len(results),
                    'passed': sum(results),
                    'failed': len(results) - sum(results)
                }
            }, f, indent=2, ensure_ascii=False)
        
        print("=" * 50)
        print("📊 缓存性能测试摘要:")
        print(f"  总测试数: {len(results)}")
        print(f"  通过: {sum(results)}")
        print(f"  失败: {len(results) - sum(results)}")
        print(f"📄 详细报告: {report_path}")
        
        if all(results):
            print("🎉 所有缓存性能测试通过！")
            return True
        else:
            print("❌ 部分缓存性能测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 缓存性能测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
