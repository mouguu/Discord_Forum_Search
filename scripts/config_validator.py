#!/usr/bin/env python3
"""
配置系统验证脚本
验证配置系统的功能正常性
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

def test_config_loading():
    """测试配置加载"""
    print("🔧 测试配置加载...")

    # 测试基本配置
    assert settings.bot.command_prefix == "/", f"命令前缀错误: {settings.bot.command_prefix}"
    assert settings.bot.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"], f"日志级别错误: {settings.bot.log_level}"
    assert isinstance(settings.bot.embed_color, int), f"嵌入颜色类型错误: {type(settings.bot.embed_color)}"

    # 测试搜索配置
    assert settings.search.max_messages_per_search > 0, f"最大搜索消息数错误: {settings.search.max_messages_per_search}"
    assert settings.search.messages_per_page > 0, f"每页消息数错误: {settings.search.messages_per_page}"
    assert settings.search.concurrent_limit > 0, f"并发限制错误: {settings.search.concurrent_limit}"

    # 测试缓存配置
    assert isinstance(settings.cache.use_redis, bool), f"Redis使用标志类型错误: {type(settings.cache.use_redis)}"
    assert settings.cache.ttl > 0, f"缓存TTL错误: {settings.cache.ttl}"

    print("✅ 配置加载测试通过")

def test_direct_config_access():
    """测试直接配置访问"""
    print("🔄 测试直接配置访问...")

    # 测试配置是否可以直接访问
    assert settings.search.max_messages_per_search > 0, "max_messages_per_search 配置无效"
    assert settings.search.messages_per_page > 0, "messages_per_page 配置无效"
    assert settings.search.concurrent_limit > 0, "concurrent_limit 配置无效"
    assert settings.bot.embed_color > 0, "embed_color 配置无效"
    assert settings.bot.reaction_timeout > 0, "reaction_timeout 配置无效"
    assert settings.search.max_embed_field_length > 0, "max_embed_field_length 配置无效"

    print("✅ 直接配置访问测试通过")

def test_environment_variables():
    """测试环境变量覆盖"""
    print("🌍 测试环境变量覆盖...")

    # 设置测试环境变量
    test_env = {
        'MAX_MESSAGES_PER_SEARCH': '2000',
        'CACHE_TTL': '900',
        'USE_REDIS_CACHE': 'true'
    }

    # 临时设置环境变量
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # 重新加载配置
        from config.settings import Settings
        test_settings = Settings.load_from_env()

        # 验证环境变量是否生效
        assert test_settings.search.max_messages_per_search == 2000, "环境变量 MAX_MESSAGES_PER_SEARCH 未生效"
        assert test_settings.cache.ttl == 900, "环境变量 CACHE_TTL 未生效"
        assert test_settings.cache.use_redis == True, "环境变量 USE_REDIS_CACHE 未生效"

        print("✅ 环境变量覆盖测试通过")

    finally:
        # 恢复原始环境变量
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

def test_config_validation():
    """测试配置验证"""
    print("✔️ 测试配置验证...")

    # 测试有效配置
    assert settings.validate(), "有效配置验证失败"

    # 测试无效配置
    from config.settings import Settings, SearchConfig, CacheConfig

    invalid_settings = Settings()
    invalid_settings.search = SearchConfig(
        max_messages_per_search=-1,  # 无效值
        concurrent_limit=0  # 无效值
    )
    invalid_settings.cache = CacheConfig(ttl=-1)  # 无效值

    assert not invalid_settings.validate(), "无效配置验证应该失败"

    print("✅ 配置验证测试通过")

def test_environment_loading():
    """测试环境配置加载"""
    print("📁 测试环境配置加载...")

    # 测试所有可用环境
    from config.settings import Settings, Environment

    environments = [
        Environment.DEFAULT,
        Environment.LARGE_SERVER,
        Environment.DEVELOPMENT,
        Environment.PRODUCTION
    ]

    for env in environments:
        try:
            env_settings = Settings.load_for_environment(env)
            assert env_settings.validate(), f"环境 {env.value} 配置验证失败"
            print(f"  ✅ 环境 {env.value} 配置加载成功")
        except Exception as e:
            print(f"  ❌ 环境 {env.value} 配置加载失败: {e}")
            return False

    print("✅ 环境配置加载测试通过")
    return True

def main():
    """主测试函数"""
    print("🚀 开始配置系统验证...")
    print("=" * 50)

    try:
        test_config_loading()
        test_direct_config_access()
        test_environment_variables()
        test_config_validation()
        test_environment_loading()

        print("=" * 50)
        print("🎉 所有配置系统验证测试通过！")
        print("\n📋 配置摘要:")
        print(f"  • 命令前缀: {settings.bot.command_prefix}")
        print(f"  • 日志级别: {settings.bot.log_level}")
        print(f"  • 最大搜索消息数: {settings.search.max_messages_per_search}")
        print(f"  • 每页消息数: {settings.search.messages_per_page}")
        print(f"  • 并发限制: {settings.search.concurrent_limit}")
        print(f"  • 使用Redis: {settings.cache.use_redis}")
        print(f"  • 缓存TTL: {settings.cache.ttl}秒")
        print(f"  • 使用数据库索引: {settings.database.use_database_index}")

        return True

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
