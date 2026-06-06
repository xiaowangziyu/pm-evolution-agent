
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import json

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("ZHIPU_API_KEY", "")
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 读取知识库中的内容
KB_PATH = Path(__file__).parent / "knowledge_base.json"

with open(KB_PATH, "r", encoding="utf-8") as f:
    kb = json.load(f)

# 查找目标知识点
target_kp = None
target_skill = None

for skill in kb["skills"]:
    if "产品执行" in skill["name"]:
        target_skill = skill
        for kp in skill["knowledge_points"]:
            if "create-prd" in kp["name"]:
                target_kp = kp
                break
        if target_kp:
            break

if not target_kp:
    print("未找到目标知识点！")
    exit()

print("="*80)
print("准备生成知识点讲解")
print("="*80)
print(f"知识点: {target_kp['name']}")
print(f"模块: {target_skill['name']}")
print()

# 构建提示词
context_str = ""
if target_kp.get("content"):
    context_str = f"\n\n参考资料（来自专业产品管理知识库）：\n{target_kp['content']}"
if target_kp.get("description"):
    context_str += f"\n\n技能描述：{target_kp['description']}"

prompt = f"""你是一位资深产品经理导师，请用通俗易懂的语言，深入浅出地讲解以下知识点：{target_kp['name']}。

要求：300-400字左右，可以举例说明。{context_str}
"""

print("="*80)
print("发送给 LLM 的提示词:")
print("="*80)
print(prompt)
print()

if not API_KEY:
    print("⚠️  未配置 ZHIPU_API_KEY，使用模拟内容")
    print()
    print("="*80)
    print("模拟知识点讲解:")
    print("="*80)
    print("""PRD（产品需求文档）是产品经理的核心产出物，它就像产品的「施工蓝图」，定义了产品的需求、目标和实现方案。

一份好的PRD通常包含8个关键部分：1）摘要 - 用2-3句话简要说明文档的目的；2）干系人 - 列出相关人员和他们的角色；3）背景 - 说明为什么要做这个产品，市场发生了什么变化；4）目标 - 定义成功标准，用SMART原则；5）目标用户 - 明确为谁设计，市场是由问题定义的；6）价值主张 - 说明产品能带来什么价值，解决什么痛点；7）解决方案 - 详细描述功能、UX原型和假设；8）发布计划 - 安排时间节点，分阶段上线。

比如做一个签到功能，PRD就要说清楚为什么要做（提升用户留存率）、给谁用（所有活跃用户）、怎么做（签到得积分，连续签到有额外奖励）、什么时候上线（两周后MVP，四周后完整版）。

写PRD时要用简单易懂的语言，避免专业术语，确保工程师、设计师和领导都能看懂。
""")
else:
    print("🚀 正在调用智谱 AI 生成讲解...")
    print()
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        
        print("="*80)
        print("✅ 成功生成知识点讲解！")
        print("="*80)
        print()
        print(text)
        
    except Exception as e:
        print(f"❌ 调用接口失败: {e}")
