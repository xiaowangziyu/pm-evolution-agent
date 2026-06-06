
import requests
import json

# 先检查后端是否运行
try:
    # 调用获取今日知识点接口
    response = requests.get("http://localhost:5000/api/today")
    print("后端服务状态: 正常运行")
except Exception as e:
    print(f"后端服务可能未运行: {e}")
    print("请先启动 Flask 后端！")
    exit()

# 准备生成知识点讲解的请求数据
knowledge_data = {
    "knowledge_name": "create-prd - 创建PRD",
    "skill_name": "产品执行 (pm-execution)",
    "skill_consecutive_days": 0,
    "knowledge_progress": 0,
    "previous_weaknesses": [],
    "previous_strengths": [],
    "today_count": 0
}

print("\n" + "="*80)
print("正在调用接口生成知识点讲解...")
print("="*80)
print(f"知识点: {knowledge_data['knowledge_name']}")
print(f"模块: {knowledge_data['skill_name']}")
print()

# 调用知识点讲解接口
try:
    response = requests.post(
        "http://localhost:5000/api/knowledge",
        json=knowledge_data,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 知识点讲解生成成功！")
        print("\n" + "="*80)
        print("知识点讲解内容:")
        print("="*80)
        print(result.get("text", "无内容"))
        print()
        print("是否为迭代学习:", result.get("is_iterative", False))
    else:
        print(f"❌ 接口调用失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"❌ 调用接口时出错: {e}")
