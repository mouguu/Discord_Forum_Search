#!/usr/bin/env python3
"""
README文档质量验证脚本
验证README.md和README_zh.md的格式和内容质量
"""
import re
import sys
from pathlib import Path

def validate_markdown_file(filepath):
    """验证单个Markdown文件"""
    print(f"🔍 验证文件: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    issues = []
    warnings = []

    # 1. 检查H1标题数量
    h1_count = 0
    in_code_block = False
    for i, line in enumerate(lines, 1):
        # 检查是否在代码块中
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue

        # 只在非代码块中检查H1标题
        if not in_code_block and re.match(r'^# [^#]', line):
            h1_count += 1
            if h1_count > 1:
                issues.append(f"第{i}行: 发现多个H1标题 (MD025)")

    # 2. 检查文件结尾换行符
    if not content.endswith('\n'):
        issues.append("文件应以单个换行符结尾 (MD047)")
    elif content.endswith('\n\n'):
        warnings.append("文件以多个换行符结尾，建议只保留一个")

    # 3. 检查代码块格式
    in_code_block = False
    code_block_lang = None
    for i, line in enumerate(lines, 1):
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                # 检查代码块语言标识
                lang_match = re.match(r'^```(\w+)?', line)
                if lang_match:
                    code_block_lang = lang_match.group(1)
                    if not code_block_lang:
                        warnings.append(f"第{i}行: 代码块缺少语言标识")
            else:
                in_code_block = False
                code_block_lang = None

    # 4. 检查链接格式
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for i, line in enumerate(lines, 1):
        links = re.findall(link_pattern, line)
        for link_text, link_url in links:
            if not link_url.startswith(('http', '#', '/')):
                warnings.append(f"第{i}行: 可能的无效链接 '{link_url}'")

    # 5. 检查表格格式
    for i, line in enumerate(lines, 1):
        if '|' in line and not line.strip().startswith('│'):  # Markdown表格
            if line.count('|') < 2:
                warnings.append(f"第{i}行: 表格格式可能不正确")

    # 6. 检查标题层级
    prev_level = 0
    for i, line in enumerate(lines, 1):
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if level > prev_level + 1:
                warnings.append(f"第{i}行: 标题层级跳跃过大 (从H{prev_level}到H{level})")
            prev_level = level

    # 7. 检查内容质量指标
    word_count = len(content.split())
    line_count = len(lines)

    print(f"  📊 统计信息:")
    print(f"    - 总行数: {line_count}")
    print(f"    - 总字数: {word_count}")
    print(f"    - H1标题数: {h1_count}")

    # 输出问题
    if issues:
        print(f"  ❌ 发现 {len(issues)} 个错误:")
        for issue in issues:
            print(f"    - {issue}")

    if warnings:
        print(f"  ⚠️  发现 {len(warnings)} 个警告:")
        for warning in warnings:
            print(f"    - {warning}")

    if not issues and not warnings:
        print(f"  ✅ 文件格式完美!")

    return len(issues) == 0

def validate_content_completeness(readme_en, readme_zh):
    """验证中英文版本内容完整性"""
    print(f"\n🔄 验证中英文版本一致性:")

    with open(readme_en, 'r', encoding='utf-8') as f:
        en_content = f.read()

    with open(readme_zh, 'r', encoding='utf-8') as f:
        zh_content = f.read()

    # 检查主要章节是否都存在
    en_sections = re.findall(r'^## (.+)', en_content, re.MULTILINE)
    zh_sections = re.findall(r'^## (.+)', zh_content, re.MULTILINE)

    print(f"  📝 英文版章节数: {len(en_sections)}")
    print(f"  📝 中文版章节数: {len(zh_sections)}")

    if len(en_sections) != len(zh_sections):
        print(f"  ⚠️  章节数量不匹配")
    else:
        print(f"  ✅ 章节数量匹配")

    # 检查代码示例数量
    en_code_blocks = len(re.findall(r'```', en_content))
    zh_code_blocks = len(re.findall(r'```', zh_content))

    print(f"  💻 英文版代码块: {en_code_blocks // 2}")
    print(f"  💻 中文版代码块: {zh_code_blocks // 2}")

    if en_code_blocks != zh_code_blocks:
        print(f"  ⚠️  代码块数量不匹配")
    else:
        print(f"  ✅ 代码块数量匹配")

def main():
    """主验证函数"""
    print("🚀 README文档质量验证")
    print("=" * 50)

    project_root = Path(__file__).parent.parent
    readme_en = project_root / "README.md"
    readme_zh = project_root / "README_zh.md"

    # 检查文件是否存在
    if not readme_en.exists():
        print(f"❌ 文件不存在: {readme_en}")
        return False

    if not readme_zh.exists():
        print(f"❌ 文件不存在: {readme_zh}")
        return False

    # 验证各个文件
    en_valid = validate_markdown_file(readme_en)
    print()
    zh_valid = validate_markdown_file(readme_zh)

    # 验证内容一致性
    validate_content_completeness(readme_en, readme_zh)

    # 总结
    print("\n" + "=" * 50)
    if en_valid and zh_valid:
        print("🎉 所有README文档验证通过!")
        print("✅ 格式正确，内容完整，质量优秀")
        return True
    else:
        print("❌ 发现问题，请修复后重新验证")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
