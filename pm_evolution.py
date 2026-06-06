import json
import os
import re
from datetime import date
from dotenv import load_dotenv
import requests

# ==================== 配置 ====================
load_dotenv()
API_KEY = os.getenv("ZHIPU_API_KEY")
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"
MAX_CONSECUTIVE_DAYS = 3


# ==================== 工具函数 ====================
def call_llm(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return None


def load_knowledge_base():
    with open("knowledge_base.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_knowledge_base(kb):
    with open("knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def load_log():
    try:
        with open("learning_log.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_date": None, "history": []}


def save_log(log):
    with open("learning_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def select_today_knowledge(kb):
    skills = kb["skills"]
    max_days = kb.get("max_consecutive_days", MAX_CONSECUTIVE_DAYS)
    available = [s for s in skills if s["consecutive_days"] < max_days]
    if not available:
        for s in skills:
            s["consecutive_days"] = 0
        available = skills
    target_skill = min(available, key=lambda s: s.get("avg_pass_rate", 0))
    target_skill["consecutive_days"] += 1
    target_kp = min(target_skill["knowledge_points"], key=lambda kp: kp["pass_rate"])
    return target_skill, target_kp


def update_pass_rate(kp, score):
    # score 0-10, 转换为达标率增量，简单版本：得分5对应0%，10对应100%
    new_rate = (score / 10) * 100
    kp["pass_rate"] = new_rate  # 直接设为本次得分折算的达标率，也可以做平滑，先简化
    # 也可以更新能力的平均达标率（略）


def main():
    print("🌟 产品经理进化录 · AI 学习助手 🌟")
    kb = load_knowledge_base()
    log = load_log()
    today = str(date.today())

    if log["last_date"] == today:
        print("✅ 你今天已经学习过了，明天再来吧！")
        return

    skill, kp = select_today_knowledge(kb)
    print(f"\n📚 今日能力：{skill['name']}（连续学习第 {skill['consecutive_days']} 天）")
    print(f"🎯 今日知识点：{kp['name']}\n")

    print("🤖 正在生成知识点讲解...")
    prompt_knowledge = f"你是一位资深产品经理导师。请用通俗易懂的语言，深入浅出地讲解以下知识点：{kp['name']}。要求：200字左右，可以举例说明。"
    knowledge_text = call_llm(prompt_knowledge)
    if not knowledge_text:
        return
    print("\n📖 【知识点讲解】")
    print(knowledge_text)

    print("\n🤖 正在生成今日一题...")
    prompt_question = f"基于知识点「{kp['name']}」，请出一道产品经理面试题，并提供参考答案。输出格式：\n题目：\n参考答案："
    qa_text = call_llm(prompt_question)
    if not qa_text:
        return
    print("\n❓ 【今日一题】")
    print(qa_text)

    if "参考答案" in qa_text:
        question_part = qa_text.split("参考答案")[0].replace("题目：", "").strip()
        reference_part = qa_text.split("参考答案")[1].strip()
    else:
        question_part = qa_text
        reference_part = ""

    print("\n✏️ 请写下你的回答：")
    user_answer = input("> ")

    print("\n🤖 正在评估你的答案...")
    prompt_eval = f"""题目：{question_part}
用户答案：{user_answer}
参考答案（供参考）：{reference_part}
请给用户的答案打分（0-10分），并给出具体改进建议。
输出格式：
得分：X
建议：..."""
    eval_text = call_llm(prompt_eval)
    if not eval_text:
        return
    print("\n📊 【评估结果】")
    print(eval_text)

    score_match = re.search(r'得分：\s*(\d+(?:\.\d+)?)', eval_text)
    if score_match:
        score = float(score_match.group(1))
    else:
        num_match = re.search(r'(\d+(?:\.\d+)?)', eval_text)
        score = float(num_match.group(1)) if num_match else 5.0
    score = max(0, min(10, score))

    update_pass_rate(kp, score)

    print("\n🤖 正在生成今日学习日记...")
    prompt_diary = f"""基于以下信息写一篇简短的学习日记（第一人称，50字左右）：
- 今日学习知识点：{kp['name']}
- 得分：{score}/10
- 简要建议：{eval_text[:100]}
日记内容："""
    diary = call_llm(prompt_diary)
    if diary:
        print("\n📓 【学习日记】")
        print(diary)

    log["last_date"] = today
    log["history"].append({
        "date": today,
        "skill": skill["name"],
        "knowledge": kp["name"],
        "score": score,
        "diary": diary
    })
    save_log(log)
    save_knowledge_base(kb)
    print("\n🎉 今日学习完成！明天见。")


if __name__ == "__main__":
    main()