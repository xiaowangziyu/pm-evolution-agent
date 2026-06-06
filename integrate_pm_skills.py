
import os
import json
import re
from pathlib import Path

PM_SKILLS_DIR = Path(__file__).parent / "pm-skills-source"
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge_base.json"

MODULE_NAMES = {
    "pm-product-discovery": "产品发现",
    "pm-product-strategy": "产品战略",
    "pm-execution": "产品执行",
    "pm-market-research": "市场研究",
    "pm-data-analytics": "数据分析",
    "pm-marketing-growth": "营销增长",
    "pm-go-to-market": "上市推广",
    "pm-toolkit": "工具包",
    "pm-ai-shipping": "AI 产品交付"
}


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


def collect_pm_skills():
    all_skills = []
    
    for module_dir in PM_SKILLS_DIR.iterdir():
        if not module_dir.is_dir() or not module_dir.name.startswith("pm-"):
            continue
        
        module_name = module_dir.name
        module_name_cn = MODULE_NAMES.get(module_name, module_name)
        
        skills_dir = module_dir / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        frontmatter = parse_frontmatter(content)
                        main_content = get_main_content(content)
                        
                        skill_name = frontmatter.get("name", skill_dir.name)
                        description = frontmatter.get("description", "")
                        
                        all_skills.append({
                            "type": "skill",
                            "module": module_name,
                            "module_cn": module_name_cn,
                            "name": skill_name,
                            "name_cn": skill_name.replace("-", " ").title(),
                            "description": description,
                            "content": main_content,
                            "path": str(skill_file.relative_to(PM_SKILLS_DIR))
                        })
                    except Exception as e:
                        print(f"Error reading {skill_file}: {e}")
        
        commands_dir = module_dir / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                try:
                    content = cmd_file.read_text(encoding="utf-8")
                    frontmatter = parse_frontmatter(content)
                    main_content = get_main_content(content)
                    
                    cmd_name = cmd_file.stem
                    description = frontmatter.get("description", "")
                    
                    all_skills.append({
                        "type": "command",
                        "module": module_name,
                        "module_cn": module_name_cn,
                        "name": cmd_name,
                        "name_cn": cmd_name.replace("-", " ").title(),
                        "description": description,
                        "content": main_content,
                        "path": str(cmd_file.relative_to(PM_SKILLS_DIR))
                    })
                except Exception as e:
                    print(f"Error reading {cmd_file}: {e}")
    
    return all_skills


def update_knowledge_base(skills_data):
    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"knowledge_base.json not found at {KNOWLEDGE_BASE_PATH}")
        return
    
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)
    
    skills_by_module = {}
    for skill in skills_data:
        mod = skill["module"]
        if mod not in skills_by_module:
            skills_by_module[mod] = {}
        skills_by_module[mod][skill["name"]] = skill
    
    updated_count = 0
    
    for module in kb.get("skills", []):
        module_name_full = module.get("name", "")
        
        module_name_en = None
        for mod_en, mod_cn in MODULE_NAMES.items():
            if mod_cn in module_name_full:
                module_name_en = mod_en
                break
        
        if not module_name_en:
            continue
        
        module_skills = skills_by_module.get(module_name_en, {})
        
        for kp in module.get("knowledge_points", []):
            kp_name = kp.get("name", "")
            
            match = None
            for skill_name, skill in module_skills.items():
                if skill_name in kp_name:
                    match = skill
                    break
            
            if not match:
                normalized_kp_name = kp_name.replace(" ", "-").lower()
                for skill_name, skill in module_skills.items():
                    if skill_name in normalized_kp_name:
                        match = skill
                        break
            
            if match:
                kp["description"] = match["description"]
                kp["content"] = match["content"]
                kp["source_path"] = match["path"]
                updated_count += 1
    
    with open(KNOWLEDGE_BASE_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    
    print(f"Updated {updated_count} knowledge points in knowledge_base.json")
    print("Done!")


def main():
    print("Collecting skills from pm-skills-source...")
    skills_data = collect_pm_skills()
    
    print(f"Found {len(skills_data)} skills/commands")
    
    print("Updating knowledge_base.json...")
    update_knowledge_base(skills_data)
    
    print("Done!")


if __name__ == "__main__":
    main()

