#!/usr/bin/env python3
"""
配置管理脚本
用于管理和切换不同的环境配置
"""
import sys
import os
from pathlib import Path
import argparse
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings, Environment

def show_current_config():
    """显示当前配置"""
    print("🔧 当前配置状态")
    print("=" * 50)

    try:
        from config.settings import settings

        print(f"环境: {settings.environment.value}")
        print(f"命令前缀: {settings.bot.command_prefix}")
        print(f"日志级别: {settings.bot.log_level}")
        print(f"使用Redis: {settings.cache.use_redis}")
        print(f"缓存TTL: {settings.cache.ttl}秒")
        print(f"最大搜索消息数: {settings.search.max_messages_per_search}")
        print(f"每页消息数: {settings.search.messages_per_page}")
        print(f"并发限制: {settings.search.concurrent_limit}")
        print(f"使用数据库索引: {settings.database.use_database_index}")
        print(f"性能监控: {settings.performance.enable_performance_monitoring}")

    except Exception as e:
        print(f"❌ 无法加载当前配置: {e}")

def list_environments():
    """列出所有可用环境"""
    print("🌍 可用环境")
    print("=" * 50)

    environments = Settings.list_available_environments()
    for env_name, description in environments.items():
        print(f"• {env_name}: {description}")

def show_environment_details(env_name: str):
    """显示特定环境的详细配置"""
    try:
        env = Environment(env_name)
        config = Settings.get_environment_config(env)

        print(f"🔍 环境详情: {env_name}")
        print("=" * 50)
        print(f"描述: {config['description']}")
        print()

        print("📋 配置详情:")
        for category, settings in config.items():
            if category == "description":
                continue
            print(f"\n{category.upper()}:")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {settings}")

    except ValueError:
        print(f"❌ 未知环境: {env_name}")
        print("使用 'list' 命令查看可用环境")

def set_environment(env_name: str):
    """设置环境变量"""
    try:
        env = Environment(env_name)

        # 创建或更新 .env 文件
        env_file = project_root / ".env"

        # 读取现有内容
        existing_lines = []
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()

        # 更新或添加 BOT_ENVIRONMENT
        updated = False
        for i, line in enumerate(existing_lines):
            if line.startswith('BOT_ENVIRONMENT='):
                existing_lines[i] = f'BOT_ENVIRONMENT={env_name}\n'
                updated = True
                break

        if not updated:
            existing_lines.append(f'BOT_ENVIRONMENT={env_name}\n')

        # 写回文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(existing_lines)

        print(f"✅ 环境已设置为: {env_name}")
        print(f"📝 已更新 .env 文件")
        print("🔄 重启机器人以应用新配置")

    except ValueError:
        print(f"❌ 未知环境: {env_name}")
        print("使用 'list' 命令查看可用环境")

def validate_config():
    """验证当前配置"""
    print("✔️ 验证配置")
    print("=" * 50)

    try:
        from config.settings import settings

        if settings.validate():
            print("✅ 配置验证通过")
            return True
        else:
            print("❌ 配置验证失败")
            return False

    except Exception as e:
        print(f"❌ 配置验证出错: {e}")
        return False

def compare_environments(env1: str, env2: str):
    """比较两个环境的配置差异"""
    try:
        env1_obj = Environment(env1)
        env2_obj = Environment(env2)

        config1 = Settings.get_environment_config(env1_obj)
        config2 = Settings.get_environment_config(env2_obj)

        print(f"🔄 比较环境: {env1} vs {env2}")
        print("=" * 50)

        # 比较每个配置类别
        all_categories = set(config1.keys()) | set(config2.keys())

        for category in sorted(all_categories):
            if category == "description":
                continue

            print(f"\n{category.upper()}:")

            settings1 = config1.get(category, {})
            settings2 = config2.get(category, {})

            all_keys = set(settings1.keys()) | set(settings2.keys())

            for key in sorted(all_keys):
                val1 = settings1.get(key, "未设置")
                val2 = settings2.get(key, "未设置")

                if val1 != val2:
                    print(f"  {key}:")
                    print(f"    {env1}: {val1}")
                    print(f"    {env2}: {val2}")
                else:
                    print(f"  {key}: {val1} (相同)")

    except ValueError as e:
        print(f"❌ 环境名称错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Discord机器人配置管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 显示当前配置
    subparsers.add_parser('current', help='显示当前配置')

    # 列出环境
    subparsers.add_parser('list', help='列出所有可用环境')

    # 显示环境详情
    detail_parser = subparsers.add_parser('show', help='显示特定环境的详细配置')
    detail_parser.add_argument('environment', help='环境名称')

    # 设置环境
    set_parser = subparsers.add_parser('set', help='设置当前环境')
    set_parser.add_argument('environment', help='环境名称')

    # 验证配置
    subparsers.add_parser('validate', help='验证当前配置')

    # 比较环境
    compare_parser = subparsers.add_parser('compare', help='比较两个环境的配置')
    compare_parser.add_argument('env1', help='第一个环境')
    compare_parser.add_argument('env2', help='第二个环境')

    args = parser.parse_args()

    if args.command == 'current':
        show_current_config()
    elif args.command == 'list':
        list_environments()
    elif args.command == 'show':
        show_environment_details(args.environment)
    elif args.command == 'set':
        set_environment(args.environment)
    elif args.command == 'validate':
        validate_config()
    elif args.command == 'compare':
        compare_environments(args.env1, args.env2)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
