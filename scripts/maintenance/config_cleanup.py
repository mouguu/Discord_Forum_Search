#!/usr/bin/env python3
"""
配置文件清理脚本 (已弃用)
配置系统已完全整合到 config/settings.py
此脚本仅用于历史参考，不再需要运行
"""
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def backup_config_files():
    """备份现有配置文件"""
    print("📦 备份现有配置文件...")

    backup_dir = project_root / "config_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)

    config_files = [
        "config/config.py",
        "config/large_server.py"
    ]

    backed_up_files = []
    for config_file in config_files:
        source = project_root / config_file
        if source.exists():
            dest = backup_dir / source.name
            shutil.copy2(source, dest)
            backed_up_files.append(str(dest))
            print(f"  ✅ 备份: {config_file} -> {dest}")

    if backed_up_files:
        print(f"✅ 配置文件已备份到: {backup_dir}")
        return backup_dir
    else:
        print("⚠️ 没有找到需要备份的配置文件")
        return None

def update_config_py():
    """更新 config.py 为兼容层"""
    print("🔄 更新 config.py 为兼容层...")

    config_py_path = project_root / "config" / "config.py"

    new_content = '''"""
配置文件 - 向后兼容层
此文件已被弃用，请使用 config.settings 模块
"""
import warnings
from config.legacy_compat import *

warnings.warn(
    "config.config 模块已弃用，请使用 'from config.settings import settings'",
    DeprecationWarning,
    stacklevel=2
)

# 为了完全向后兼容，保留所有原始常量
# 这些常量现在从 legacy_compat 模块导入
'''

    try:
        with open(config_py_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 已更新 {config_py_path}")
        return True
    except Exception as e:
        print(f"❌ 更新 config.py 失败: {e}")
        return False

def scan_and_report_imports():
    """扫描并报告需要更新的导入"""
    print("🔍 扫描需要更新的导入...")

    python_files = []
    for pattern in ["*.py", "**/*.py"]:
        python_files.extend(project_root.glob(pattern))

    files_with_old_imports = []

    for py_file in python_files:
        if py_file.name.startswith('.') or 'config_backup' in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查旧的导入模式
            old_patterns = [
                'from config.config import',
                'import config.config',
                'from config import config'
            ]

            found_patterns = []
            for pattern in old_patterns:
                if pattern in content:
                    found_patterns.append(pattern)

            if found_patterns:
                files_with_old_imports.append({
                    'file': py_file,
                    'patterns': found_patterns
                })

        except Exception as e:
            print(f"⚠️ 无法读取文件 {py_file}: {e}")

    if files_with_old_imports:
        print("\n📋 发现以下文件仍使用旧的导入模式:")
        for item in files_with_old_imports:
            print(f"  📄 {item['file'].relative_to(project_root)}")
            for pattern in item['patterns']:
                print(f"    - {pattern}")

        print("\n💡 建议手动更新这些文件的导入语句:")
        print("   旧: from config.config import SETTING_NAME")
        print("   新: from config.settings import settings")
        print("   使用: settings.category.setting_name")
    else:
        print("✅ 没有发现使用旧导入模式的文件")

    return files_with_old_imports

def create_migration_guide():
    """创建迁移指南"""
    print("📖 创建迁移指南...")

    guide_content = '''# 配置系统迁移指南

## 概述
配置系统已从分散的配置文件迁移到统一的 `config.settings` 模块。

## 迁移映射

### 旧的导入方式
```python
from config.config import (
    MAX_MESSAGES_PER_SEARCH,
    MESSAGES_PER_PAGE,
    CONCURRENT_SEARCH_LIMIT,
    EMBED_COLOR,
    REACTION_TIMEOUT
)
```

### 新的导入方式
```python
from config.settings import settings

# 使用方式:
settings.search.max_messages_per_search  # 替代 MAX_MESSAGES_PER_SEARCH
settings.search.messages_per_page        # 替代 MESSAGES_PER_PAGE
settings.search.concurrent_limit         # 替代 CONCURRENT_SEARCH_LIMIT
settings.bot.embed_color                 # 替代 EMBED_COLOR
settings.bot.reaction_timeout            # 替代 REACTION_TIMEOUT
```

## 配置分类

### Bot配置 (settings.bot)
- command_prefix
- log_level
- embed_color
- reaction_timeout

### 搜索配置 (settings.search)
- max_messages_per_search
- messages_per_page
- concurrent_limit
- guild_concurrent_searches
- user_search_cooldown
- search_timeout
- max_embed_field_length
- min_reactions
- reaction_cache_ttl

### 缓存配置 (settings.cache)
- use_redis
- redis_url
- ttl
- thread_cache_size
- max_items

### 数据库配置 (settings.database)
- use_database_index
- db_path
- connection_pool_size

## 环境变量支持
所有配置项都支持通过环境变量覆盖，环境变量名与原配置常量名相同。

## 向后兼容
为了确保平滑迁移，旧的导入方式仍然可用，但会显示弃用警告。
建议尽快迁移到新的配置系统。

## 验证迁移
运行以下命令验证迁移是否成功:
```bash
python scripts/config_migration_validator.py
```
'''

    guide_path = project_root / "docs" / "config_migration_guide.md"

    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print(f"✅ 迁移指南已创建: {guide_path}")
        return True
    except Exception as e:
        print(f"❌ 创建迁移指南失败: {e}")
        return False

def main():
    """主清理函数"""
    print("🧹 开始配置文件清理...")
    print("=" * 50)

    # 1. 备份现有配置文件
    backup_dir = backup_config_files()

    # 2. 更新 config.py 为兼容层
    if not update_config_py():
        print("❌ 配置清理失败")
        return False

    # 3. 扫描需要更新的导入
    old_imports = scan_and_report_imports()

    # 4. 创建迁移指南
    create_migration_guide()

    print("=" * 50)
    print("🎉 配置文件清理完成！")

    if backup_dir:
        print(f"\n📦 备份位置: {backup_dir}")

    if old_imports:
        print(f"\n⚠️ 发现 {len(old_imports)} 个文件需要手动更新导入")
        print("   请查看上面的详细列表并手动更新")
    else:
        print("\n✅ 所有导入已是最新格式")

    print("\n📖 查看迁移指南: docs/config_migration_guide.md")
    print("🔧 运行验证脚本: python scripts/config_migration_validator.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
