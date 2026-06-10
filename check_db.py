import db

# 检查技能数
skills = db.get_all_skills()
print(f"技能数: {len(skills)}")

for skill in skills:
    print(f"- {skill['name']}: {len(skill['knowledge_points'])}个知识点")
