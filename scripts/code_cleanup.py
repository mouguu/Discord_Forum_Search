#!/usr/bin/env python3
"""
代码清理和整合脚本
安全地清理冗余文件并整合零散组件
"""
import sys
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class CodeCleaner:
    """代码清理器"""
    
    def __init__(self):
        self.backup_dir = project_root / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'actions': [],
            'files_removed': [],
            'files_modified': [],
            'files_backed_up': [],
            'errors': []
        }
    
    def create_backup(self, file_path: Path, reason: str = ""):
        """创建文件备份"""
        if not file_path.exists():
            return False
        
        try:
            # 创建备份目录
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 保持相对路径结构
            relative_path = file_path.relative_to(project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(file_path, backup_path)
            
            self.cleanup_report['files_backed_up'].append({
                'original': str(file_path),
                'backup': str(backup_path),
                'reason': reason
            })
            
            print(f"  📦 已备份: {relative_path}")
            return True
            
        except Exception as e:
            error_msg = f"备份文件失败 {file_path}: {e}"
            self.cleanup_report['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
            return False
    
    def remove_file(self, file_path: Path, reason: str = ""):
        """安全删除文件"""
        if not file_path.exists():
            return False
        
        try:
            # 先备份
            if self.create_backup(file_path, f"删除前备份: {reason}"):
                file_path.unlink()
                
                self.cleanup_report['files_removed'].append({
                    'path': str(file_path),
                    'reason': reason
                })
                
                print(f"  🗑️ 已删除: {file_path.relative_to(project_root)}")
                return True
            else:
                print(f"  ⚠️ 备份失败，跳过删除: {file_path.relative_to(project_root)}")
                return False
                
        except Exception as e:
            error_msg = f"删除文件失败 {file_path}: {e}"
            self.cleanup_report['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
            return False
    
    def remove_directory(self, dir_path: Path, reason: str = ""):
        """安全删除目录"""
        if not dir_path.exists() or not dir_path.is_dir():
            return False
        
        try:
            # 备份整个目录
            if self.create_backup(dir_path, f"删除目录前备份: {reason}"):
                shutil.rmtree(dir_path)
                
                self.cleanup_report['files_removed'].append({
                    'path': str(dir_path),
                    'type': 'directory',
                    'reason': reason
                })
                
                print(f"  🗑️ 已删除目录: {dir_path.relative_to(project_root)}")
                return True
            else:
                print(f"  ⚠️ 备份失败，跳过删除目录: {dir_path.relative_to(project_root)}")
                return False
                
        except Exception as e:
            error_msg = f"删除目录失败 {dir_path}: {e}"
            self.cleanup_report['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
            return False
    
    def clean_cache_files(self):
        """清理缓存文件"""
        print("🧹 清理Python缓存文件...")
        
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd"
        ]
        
        removed_count = 0
        
        for pattern in cache_patterns:
            for cache_path in project_root.glob(pattern):
                if cache_path.is_dir():
                    if self.remove_directory(cache_path, "Python缓存目录"):
                        removed_count += 1
                elif cache_path.is_file():
                    if self.remove_file(cache_path, "Python缓存文件"):
                        removed_count += 1
        
        self.cleanup_report['actions'].append({
            'action': 'clean_cache_files',
            'removed_count': removed_count
        })
        
        print(f"  ✅ 清理了 {removed_count} 个缓存文件/目录")
    
    def clean_log_files(self):
        """清理临时日志文件"""
        print("📝 清理临时日志文件...")
        
        logs_dir = project_root / "logs"
        if not logs_dir.exists():
            print("  ℹ️ 日志目录不存在，跳过")
            return
        
        # 保留最新的报告，删除旧的
        log_files = list(logs_dir.glob("*.json"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 保留最新的3个文件
        files_to_keep = 3
        removed_count = 0
        
        for log_file in log_files[files_to_keep:]:
            if self.remove_file(log_file, "旧的测试报告文件"):
                removed_count += 1
        
        self.cleanup_report['actions'].append({
            'action': 'clean_log_files',
            'removed_count': removed_count,
            'kept_count': min(len(log_files), files_to_keep)
        })
        
        print(f"  ✅ 清理了 {removed_count} 个旧日志文件，保留最新 {min(len(log_files), files_to_keep)} 个")
    
    def update_config_py(self):
        """更新config.py为纯兼容层"""
        print("⚙️ 更新config.py为兼容层...")
        
        config_py_path = project_root / "config" / "config.py"
        
        if not config_py_path.exists():
            print("  ℹ️ config.py不存在，跳过")
            return
        
        # 备份原文件
        self.create_backup(config_py_path, "更新为兼容层前备份")
        
        # 新的兼容层内容
        new_content = '''"""
配置文件 - 向后兼容层
此文件已被重构为兼容层，实际配置请使用 config.settings 模块
"""
import warnings
from config.legacy_compat import *

# 发出弃用警告
warnings.warn(
    "config.config 模块已弃用，请使用 'from config.settings import settings'",
    DeprecationWarning,
    stacklevel=2
)

# 所有配置项现在从 legacy_compat 模块导入
# 这确保了向后兼容性，同时引导用户使用新的配置系统
'''
        
        try:
            with open(config_py_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.cleanup_report['files_modified'].append({
                'path': str(config_py_path),
                'action': 'updated_to_compatibility_layer'
            })
            
            print(f"  ✅ 已更新config.py为兼容层")
            
        except Exception as e:
            error_msg = f"更新config.py失败: {e}"
            self.cleanup_report['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def consolidate_monitoring_docs(self):
        """整合监控文档"""
        print("📚 整合监控文档...")
        
        # 检查重复的监控文档
        monitoring_setup_path = project_root / "docs" / "monitoring-setup.md"
        monitoring_guide_path = project_root / "docs" / "monitoring_and_testing_guide.md"
        
        if monitoring_setup_path.exists() and monitoring_guide_path.exists():
            # 备份旧文档
            self.create_backup(monitoring_setup_path, "整合前备份")
            
            # 删除重复的文档
            if self.remove_file(monitoring_setup_path, "内容已整合到monitoring_and_testing_guide.md"):
                print("  ✅ 已删除重复的monitoring-setup.md")
        
        # 检查其他可能重复的文档
        docs_to_check = [
            ("maintenance.md", "维护文档"),
            ("performance_optimization.md", "性能优化文档")
        ]
        
        for doc_name, description in docs_to_check:
            doc_path = project_root / "docs" / doc_name
            if doc_path.exists():
                # 检查文件大小，如果很小可能是空文档
                if doc_path.stat().st_size < 1000:  # 小于1KB
                    if self.remove_file(doc_path, f"空或重复的{description}"):
                        print(f"  ✅ 已删除空的{description}")
    
    def clean_unused_scripts(self):
        """清理未使用的脚本"""
        print("🔧 检查未使用的脚本...")
        
        # 检查是否有重复功能的脚本
        scripts_dir = project_root / "scripts"
        
        # monitoring_test.py 功能已被 basic_monitoring_test.py 替代
        monitoring_test_path = scripts_dir / "monitoring_test.py"
        if monitoring_test_path.exists():
            if self.remove_file(monitoring_test_path, "功能已被basic_monitoring_test.py替代"):
                print("  ✅ 已删除重复的monitoring_test.py")
    
    def create_gitignore_update(self):
        """更新.gitignore文件"""
        print("📝 更新.gitignore文件...")
        
        gitignore_path = project_root / ".gitignore"
        
        # 需要添加的忽略规则
        ignore_rules = [
            "# Python缓存",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "",
            "# 日志文件",
            "logs/*.json",
            "*.log",
            "",
            "# 临时文件",
            ".tmp/",
            "temp/",
            "",
            "# 备份文件",
            "cleanup_backup/",
            "config_backup/",
            "",
            "# 环境变量",
            ".env",
            ".env.local",
            "",
            "# IDE文件",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# 操作系统文件",
            ".DS_Store",
            "Thumbs.db"
        ]
        
        try:
            # 读取现有内容
            existing_content = ""
            if gitignore_path.exists():
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # 检查哪些规则需要添加
            new_rules = []
            for rule in ignore_rules:
                if rule and rule not in existing_content:
                    new_rules.append(rule)
            
            if new_rules:
                # 备份现有文件
                if gitignore_path.exists():
                    self.create_backup(gitignore_path, "更新前备份")
                
                # 添加新规则
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    if existing_content and not existing_content.endswith('\n'):
                        f.write('\n')
                    f.write('\n'.join(new_rules))
                    f.write('\n')
                
                self.cleanup_report['files_modified'].append({
                    'path': str(gitignore_path),
                    'action': 'added_ignore_rules',
                    'new_rules_count': len([r for r in new_rules if r])
                })
                
                print(f"  ✅ 已添加 {len([r for r in new_rules if r])} 条新的忽略规则")
            else:
                print("  ℹ️ .gitignore已是最新状态")
                
        except Exception as e:
            error_msg = f"更新.gitignore失败: {e}"
            self.cleanup_report['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def generate_cleanup_report(self):
        """生成清理报告"""
        print("\n📊 生成清理报告...")
        
        # 保存详细报告
        report_path = project_root / "logs" / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.cleanup_report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 详细报告已保存: {report_path}")
            
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
        
        # 显示摘要
        print("\n📋 清理摘要:")
        print(f"  备份文件数: {len(self.cleanup_report['files_backed_up'])}")
        print(f"  删除文件数: {len(self.cleanup_report['files_removed'])}")
        print(f"  修改文件数: {len(self.cleanup_report['files_modified'])}")
        print(f"  执行操作数: {len(self.cleanup_report['actions'])}")
        print(f"  错误数量: {len(self.cleanup_report['errors'])}")
        
        if self.cleanup_report['errors']:
            print("\n⚠️ 错误详情:")
            for error in self.cleanup_report['errors']:
                print(f"  - {error}")
        
        if self.backup_dir.exists():
            print(f"\n📦 备份位置: {self.backup_dir}")
    
    def run_cleanup(self):
        """执行完整清理"""
        print("🧹 开始代码清理和整合...")
        print("=" * 60)
        
        try:
            # 执行清理步骤
            self.clean_cache_files()
            self.clean_log_files()
            self.update_config_py()
            self.consolidate_monitoring_docs()
            self.clean_unused_scripts()
            self.create_gitignore_update()
            
            # 生成报告
            self.generate_cleanup_report()
            
            print("\n🎉 代码清理完成！")
            return True
            
        except Exception as e:
            error_msg = f"清理过程出错: {e}"
            self.cleanup_report['errors'].append(error_msg)
            print(f"\n❌ {error_msg}")
            return False

def main():
    """主函数"""
    cleaner = CodeCleaner()
    success = cleaner.run_cleanup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
