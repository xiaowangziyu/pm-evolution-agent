
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

old_user_id = 'user_1780736577934_mftogy'
new_user_id = 'default_user'

# 加载旧数据
old_log_path = os.path.join(BASE_DIR, f'log_user_{old_user_id}.json')
old_kb_path = os.path.join(BASE_DIR, f'kb_user_{old_user_id}.json')

# 加载新数据
new_log_path = os.path.join(BASE_DIR, f'log_user_{new_user_id}.json')
new_kb_path = os.path.join(BASE_DIR, f'kb_user_{new_user_id}.json')


print('=== 正在加载旧数据 ===')
with open(old_log_path, 'r', encoding='utf-8') as f:
    old_log = json.load(f)
with open(old_kb_path, 'r', encoding='utf-8') as f:
    old_kb = json.load(f)

print(f'  - 旧数据有 {len(old_log.get("history", []))} 条学习记录')


print('\n=== 正在加载新数据 ===')
with open(new_log_path, 'r', encoding='utf-8') as f:
    new_log = json.load(f)
with open(new_kb_path, 'r', encoding='utf-8') as f:
    new_kb = json.load(f)

print(f'  - 新数据有 {len(new_log.get("history", []))} 条学习记录')


# 合并历史记录
merged_history = old_log.get('history', []) + new_log.get('history', [])
# 去重（按日期和知识点）
seen = set()
unique_history = []
for item in merged_history:
    key = (item['date'], item['knowledge'])
    if key not in seen:
        unique_history.append(item)
        seen.add(key)

merged_log = {
    'last_date': new_log.get('last_date') or old_log.get('last_date'),
    'history': unique_history
}


print(f'\n=== 合并结果 ===')
print(f'  - 合并后有 {len(unique_history)} 条学习记录')


# 保存合并后的日志（覆盖新用户的）
with open(new_log_path, 'w', encoding='utf-8') as f:
    json.dump(merged_log, f, ensure_ascii=False, indent=2)
print(f'  - 已保存到 {new_log_path}')


# 合并知识库进度（取两者的最大值）
print('\n=== 合并知识库进度 ===')
for old_skill, new_skill in zip(old_kb['skills'], new_kb['skills']):
    for old_kp, new_kp in zip(old_skill['knowledge_points'], new_skill['knowledge_points']):
        # 取更大的进度值
        if old_kp.get('progress', 0) > new_kp.get('progress', 0):
            new_kp['progress'] = old_kp['progress']
            print(f'    - 更新知识点 {old_kp["name"]}: 进度 {old_kp["progress"]}%')
    # 重新计算平均进度
    kps = new_skill['knowledge_points']
    if kps:
        new_skill['avg_progress'] = round(sum(kp['progress'] for kp in kps) / len(kps), 1)

# 保存合并后的知识库
with open(new_kb_path, 'w', encoding='utf-8') as f:
    json.dump(new_kb, f, ensure_ascii=False, indent=2)
print(f'  - 已保存到 {new_kb_path}')


print('\n✅ 数据合并完成！新的学习历史和进度同时包含旧记录和新记录！')

