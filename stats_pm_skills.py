
import os
from pathlib import Path

PM_SKILLS_DIR = Path(__file__).parent / "pm-skills-source"

def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}
    
    lines = content.split("\n")
    frontmatter = {}
    in_frontmatter = False
    
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        
        if in_frontmatter and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            frontmatter[key] = value
    
    return frontmatter

def get_main_content(content):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content.strip()

def collect_stats():
    all_files = []
    total_word_count = 0
    total_char_count = 0
    file_count = 0
    
    for module_dir in PM_SKILLS_DIR.iterdir():
        if not module_dir.is_dir() or not module_dir.name.startswith("pm-"):
            continue
        
        # 收集 skills
        skills_dir = module_dir / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        main_content = get_main_content(content)
                        
                        # 统计字数和字符数
                        word_count = len(main_content.split())
                        char_count = len(main_content)
                        
                        total_word_count += word_count
                        total_char_count += char_count
                        file_count += 1
                        
                        all_files.append({
                            "path": str(skill_file.relative_to(PM_SKILLS_DIR)),
                            "words": word_count,
                            "chars": char_count,
                            "est_chinese_chars": int(word_count * 1.7)  # 估算翻译后的中文字数
                        })
                    except Exception as e:
                        print(f"Error reading {skill_file}: {e}")
        
        # 收集 commands
        commands_dir = module_dir / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                try:
                    content = cmd_file.read_text(encoding="utf-8")
                    main_content = get_main_content(content)
                    
                    # 统计字数和字符数
                    word_count = len(main_content.split())
                    char_count = len(main_content)
                    
                    total_word_count += word_count
                    total_char_count += char_count
                    file_count += 1
                    
                    all_files.append({
                        "path": str(cmd_file.relative_to(PM_SKILLS_DIR)),
                        "words": word_count,
                        "chars": char_count,
                        "est_chinese_chars": int(word_count * 1.7)  # 估算翻译后的中文字数
                    })
                except Exception as e:
                    print(f"Error reading {cmd_file}: {e}")
    
    # 按字数排序
    all_files_sorted = sorted(all_files, key=lambda x: x["words"], reverse=True)
    
    # 打印统计信息
    print("="*80)
    print("pm-skills 仓库内容统计")
    print("="*80)
    print(f"总文件数: {file_count}")
    print(f"总英文单词数: {total_word_count:,}")
    print(f"总英文字符数: {total_char_count:,}")
    print(f"估算中文总字数: {int(total_word_count * 1.7):,}")
    print()
    print("平均每个文件:")
    print(f"- 英文单词: {int(total_word_count / file_count):,}")
    print(f"- 英文字符: {int(total_char_count / file_count):,}")
    print(f"- 估算中文: {int((total_word_count / file_count) * 1.7):,}")
    print()
    print("="*80)
    print("文件按字数排名（前20）:")
    print("="*80)
    
    for i, f in enumerate(all_files_sorted[:20], 1):
        print(f"{i:2d}. {f['path']:60s} | 英文单词: {f['words']:5d} | 估算中文: {f['est_chinese_chars']:5d}")
    
    print()
    print("="*80)
    print("各范围的文件分布:")
    print("="*80)
    
    ranges = [
        ("0-200", 0, 200),
        ("200-500", 200, 500),
        ("500-1000", 500, 1000),
        ("1000-2000", 1000, 2000),
        ("2000+", 2000, float('inf'))
    ]
    
    for label, min_w, max_w in ranges:
        count = len([f for f in all_files if min_w <= f['words'] < max_w])
        print(f"{label:12s} : {count} 个文件")

if __name__ == "__main__":
    collect_stats()
