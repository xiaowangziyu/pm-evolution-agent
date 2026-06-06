
import os
from dotenv import load_dotenv

# 模拟数据
test_data = {
    "skill_name": "产品执行 (pm-execution)",
    "knowledge_name": "create-prd - 创建PRD",
    "score": 7.5,
    "eval_text": "总结：回答体现了对知识点的基本理解，在产品需求文档的结构上掌握较好，但在实际案例的应用上还可以更深入。\n\n达标之处：\n- 清楚PRD的8个基本结构\n- 理解PRD的作用和价值\n- 语言表达清晰\n\n不足之处：\n- 缺乏具体的产品案例\n- 没有结合实际工作场景\n- 对假设验证的部分阐述不够\n\n建议：建议多结合自己的工作经验，用具体的产品案例来练习写PRD。",
    "summary": "回答体现了对知识点的基本理解，在产品需求文档的结构上掌握较好，但在实际案例的应用上还可以更深入。",
    "strengths": ["清楚PRD的8个基本结构", "理解PRD的作用和价值", "语言表达清晰"],
    "weaknesses": ["缺乏具体的产品案例", "没有结合实际工作场景", "对假设验证的部分阐述不够"]
}

# 测试修复后的提示词构建
knowledge_name = test_data["knowledge_name"]
summary = test_data["summary"]
score = test_data["score"]
strengths = test_data["strengths"]
weaknesses = test_data["weaknesses"]

print("="*80)
print("测试日记生成提示词")
print("="*80)

# 构建提示词
prompt = f"""基于以下信息写一篇详细的学习日记（第一人称，200-300字）
- 今日学习知识点：{knowledge_name}
- 今日总结：{summary}
- 得分：{score}/10
- 今日达标之处：{'、'.join(strengths) if strengths else '无'}
- 今日不足之处：{'、'.join(weaknesses) if weaknesses else '无'}

要求：
1. 开头记录今天的学习心情和状态
2. 描述对知识点的理解和收获
3. 结合达标之处和不足之处分析本次学习
4. 写下后续学习的计划和目标
5. 结尾鼓励自己继续加油

日记内容："""

print(prompt)
print("\n✅ 提示词构建成功！")
