#!/usr/bin/env python3
"""
快速设置脚本
一键配置监控和测试环境
"""
import sys
import os
import subprocess
import platform
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step, description):
    """打印步骤"""
    print(f"\n📋 步骤 {step}: {description}")

def run_command(command, description, check=True):
    """运行命令"""
    print(f"  🔧 {description}...")
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=check, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ {description} 完成")
            return True
        else:
            print(f"  ❌ {description} 失败: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ {description} 失败: {e}")
        return False
    except Exception as e:
        print(f"  💥 {description} 出错: {e}")
        return False

def check_python_version():
    """检查Python版本"""
    print_step(1, "检查Python环境")
    
    version = sys.version_info
    print(f"  📊 Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ 需要Python 3.8或更高版本")
        return False
    
    print("  ✅ Python版本符合要求")
    return True

def install_dependencies():
    """安装依赖"""
    print_step(2, "安装Python依赖")
    
    requirements_file = project_root / "requirements.txt"
    if not requirements_file.exists():
        print("  ⚠️ requirements.txt 不存在，跳过依赖安装")
        return True
    
    return run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], "安装依赖包")

def setup_directories():
    """设置目录结构"""
    print_step(3, "设置目录结构")
    
    directories = [
        "logs",
        "data",
        "config_backup"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"  📁 创建目录: {directory}")
    
    print("  ✅ 目录结构设置完成")
    return True

def validate_configuration():
    """验证配置"""
    print_step(4, "验证配置系统")
    
    validator_script = project_root / "scripts" / "config_migration_validator.py"
    if not validator_script.exists():
        print("  ⚠️ 配置验证脚本不存在")
        return False
    
    return run_command([sys.executable, str(validator_script)], "验证配置系统")

def run_basic_tests():
    """运行基础测试"""
    print_step(5, "运行基础测试")
    
    test_script = project_root / "scripts" / "basic_monitoring_test.py"
    if not test_script.exists():
        print("  ⚠️ 基础测试脚本不存在")
        return False
    
    return run_command([sys.executable, str(test_script)], "运行基础监控测试")

def setup_monitoring():
    """设置监控"""
    print_step(6, "设置监控系统")
    
    # 检查操作系统
    os_type = platform.system().lower()
    
    if os_type in ['linux', 'darwin']:  # Linux 或 macOS
        monitoring_script = project_root / "scripts" / "system_monitoring_setup.sh"
        if monitoring_script.exists():
            print("  📊 发现系统监控设置脚本")
            print("  💡 要设置完整的系统监控，请运行:")
            print(f"     chmod +x {monitoring_script}")
            print(f"     sudo {monitoring_script}")
        else:
            print("  ⚠️ 系统监控脚本不存在")
    else:
        print(f"  ⚠️ 不支持的操作系统: {os_type}")
    
    print("  ✅ 监控系统配置指导完成")
    return True

def create_env_template():
    """创建环境变量模板"""
    print_step(7, "创建环境变量模板")
    
    env_template = project_root / ".env.template"
    env_content = """# Discord机器人环境变量配置模板
# 复制此文件为 .env 并填入实际值

# Discord机器人令牌 (必需)
DISCORD_TOKEN=your_discord_bot_token_here

# 日志级别 (可选)
LOG_LEVEL=INFO

# 缓存配置 (可选)
USE_REDIS_CACHE=false
REDIS_URL=redis://localhost:6379/0

# 搜索配置 (可选)
MAX_MESSAGES_PER_SEARCH=1000
CONCURRENT_SEARCH_LIMIT=5

# 监控配置 (可选)
DISCORD_WEBHOOK_URL=your_webhook_url_for_alerts

# 数据库配置 (可选)
USE_DATABASE_INDEX=true
DB_PATH=data/forum_search.db
"""
    
    try:
        with open(env_template, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"  ✅ 环境变量模板已创建: {env_template}")
        
        # 检查是否已有 .env 文件
        env_file = project_root / ".env"
        if not env_file.exists():
            print("  💡 请复制 .env.template 为 .env 并配置您的设置")
        
        return True
    except Exception as e:
        print(f"  ❌ 创建环境变量模板失败: {e}")
        return False

def run_performance_test():
    """运行性能测试"""
    print_step(8, "运行性能基准测试")
    
    perf_script = project_root / "scripts" / "performance_benchmark.py"
    if not perf_script.exists():
        print("  ⚠️ 性能测试脚本不存在")
        return False
    
    return run_command([sys.executable, str(perf_script)], "运行性能基准测试")

def show_next_steps():
    """显示后续步骤"""
    print_header("设置完成 - 后续步骤")
    
    print("🎉 快速设置已完成！")
    print("\n📋 后续步骤:")
    print("1. 配置环境变量:")
    print("   cp .env.template .env")
    print("   # 编辑 .env 文件，填入您的Discord机器人令牌")
    
    print("\n2. 运行机器人:")
    print("   python main.py")
    
    print("\n3. 运行完整测试套件:")
    print("   python scripts/test_suite_runner.py --all")
    
    print("\n4. 查看监控仪表板 (Linux/macOS):")
    print("   /opt/discord-bot-monitoring/scripts/dashboard.sh")
    
    print("\n5. 部署到云平台:")
    print("   # 查看 docs/cloud_deployment_comparison.md")
    
    print("\n📚 相关文档:")
    print("   - docs/monitoring_and_testing_guide.md")
    print("   - docs/deployment.md")
    print("   - docs/api.md")
    
    print("\n💡 获取帮助:")
    print("   python scripts/test_suite_runner.py --help")

def main():
    """主函数"""
    print_header("Discord机器人快速设置")
    print("此脚本将帮助您快速设置监控和测试环境")
    
    # 执行设置步骤
    steps = [
        check_python_version,
        install_dependencies,
        setup_directories,
        validate_configuration,
        run_basic_tests,
        setup_monitoring,
        create_env_template,
        run_performance_test
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step_func in steps:
        try:
            if step_func():
                success_count += 1
            else:
                print(f"  ⚠️ 步骤失败，但继续执行...")
        except KeyboardInterrupt:
            print("\n\n⏹️ 用户中断设置")
            sys.exit(1)
        except Exception as e:
            print(f"  💥 步骤执行出错: {e}")
    
    # 显示结果
    print_header("设置结果")
    print(f"📊 完成步骤: {success_count}/{total_steps}")
    
    if success_count == total_steps:
        print("🎉 所有步骤都成功完成！")
        show_next_steps()
        return True
    elif success_count >= total_steps * 0.8:
        print("⚠️ 大部分步骤完成，可以继续使用")
        show_next_steps()
        return True
    else:
        print("❌ 多个步骤失败，请检查错误信息")
        print("\n💡 常见解决方案:")
        print("   - 确保Python 3.8+已安装")
        print("   - 检查网络连接")
        print("   - 确保有足够的磁盘空间")
        print("   - 在Linux/macOS上可能需要sudo权限")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 设置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 设置过程出现未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
