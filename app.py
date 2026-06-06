"""
产品经理进化论 Agent - Flask 后端服务
"""
import json
import os
import re
from datetime import date
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import requests

# ==================== 配置 ====================
load_dotenv()
API_KEY = os.getenv("ZHIPU_API_KEY", "")
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"
MAX_CONSECUTIVE_DAYS = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")
LOG_PATH = os.path.join(BASE_DIR, "learning_log.json")

app = Flask(__name__)

# ==================== 工具函数 ====================
def call_llm(prompt):
    """调用智谱AI大模型"""
    if not API_KEY:
        # 演示模式：返回模拟内容
        if "讲解" in prompt or "知识点" in prompt:
            # 判断是否为迭代学习（有strengths）
            if "已掌握" in prompt:
                kp_match = re.search(r'「(.+?)」', prompt)
                kp_name = kp_match.group(1).strip() if kp_match else "该知识点"
                weaknesses_match = re.search(r'不足：(.+?)，但', prompt)
                weaknesses = weaknesses_match.group(1).strip() if weaknesses_match else "部分概念"
                return f"""    「{kp_name}」是在原知识点基础上的深化与扩展。

    你的优势在于已经掌握了基础概念，能够运用核心框架进行分析。本次重点针对「{weaknesses}」进行深入讲解。

    在实际产品工作中，建议你结合具体项目场景进行实践。比如可以思考：在你参与过的产品迭代中，是如何运用这个知识点的？有哪些做得好的地方？有哪些可以优化的地方？

    💡 配置 ZHIPU_API_KEY 后可获得完整的个性化学习体验。"""
            else:
                kp_match = re.search(r'知识点[：:]?\s*(.+?)[。？\n]', prompt)
                kp_name = kp_match.group(1).strip() if kp_match else "该知识点"
                return f"""    「{kp_name}」是产品经理必备的核心能力之一。

    在实际工作中，我们需要理解这个概念的本质：它不仅仅是理论知识，更是解决实际问题的方法论。比如在需求评审中，如何运用这个知识点？需要考虑哪些维度？

    建议结合你当前的项目思考：这个知识点如何帮助解决实际问题？有哪些场景可以应用？

    💡 配置 ZHIPU_API_KEY 后可获得完整的个性化学习体验。"""

        elif "练习题" in prompt or "出题" in prompt or "面试题" in prompt:
            kp_match = re.search(r'「(.+?)」', prompt)
            kp_name = kp_match.group(1) if kp_match else "产品经理能力"
            if "更有挑战性" in prompt or "不足" in prompt:
                return f"""题目：在产品迭代过程中，你如何运用「{kp_name}」解决一个具体的用户痛点？请详细描述你的思考过程和行动方案。

参考答案：
1. 问题识别：明确用户痛点本质
2. 分析框架：运用「{kp_name}」相关理论进行分析
3. 解决方案：提出具体可行的产品方案
4. 执行落地：如何推动方案实施
5. 效果复盘：如何评估方案效果"""
            else:
                return f"""题目：请结合实际工作经验，谈谈你对「{kp_name}」的理解，以及在产品工作中如何应用这个知识点？

参考答案：
1. 理解定义：清晰阐述「{kp_name}」的核心概念
2. 应用场景：列举实际工作中的应用案例
3. 方法总结：总结应用的心得体会
4. 反思改进：指出可以优化提升的方向"""

        elif "打分" in prompt or "评估" in prompt or "达标" in prompt:
            return """总结：回答体现了对知识点的基础理解，但在深度和系统性方面还有提升空间。

达标之处：
- 对核心概念有基本认知
- 能够识别关键要点

不足之处：
- 缺乏具体案例支撑
- 分析框架不够系统

建议：建议结合实际项目经验，用STAR法则组织答案，让回答更具说服力。"""

        elif "日记" in prompt:
            return """今天学习了新的知识点，虽然还有些生疏，但每天都在进步。坚持就是胜利，继续加油！

💡 配置 ZHIPU_API_KEY 后可获得更智能的学习日记。"""

        return "💡 当前为演示模式，请配置 ZHIPU_API_KEY 以获得完整AI功能。"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    # 获取代理配置
    proxies = {}
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if https_proxy:
        proxies["https"] = https_proxy
    if http_proxy:
        proxies["http"] = http_proxy

    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                API_URL,
                headers=headers,
                json=data,
                timeout=60,  # 增加超时时间到60秒
                proxies=proxies if proxies else None
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"API调用超时，正在重试 ({attempt + 1}/{max_retries})...")
                continue
            return "❌ API调用超时，请检查网络连接后重试"
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"API连接失败，正在重试 ({attempt + 1}/{max_retries})...")
                continue
            return f"❌ API连接失败，请检查网络设置"
        except Exception as e:
            return f"❌ API调用失败: {str(e)}"


def get_user_id():
    """从请求中获取 user_id"""
    user_id = request.args.get('user_id')
    if not user_id:
        user_id = request.headers.get('X-User-Id')
    if not user_id:
        user_id = 'default_user'
    # 清理文件名，只保留安全字符
    return ''.join(c for c in user_id if c.isalnum() or c in '_-')


def load_knowledge_base():
    """加载原始知识库（只读）"""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_user_knowledge_base(user_id):
    """加载用户的知识库进度（会复制原始知识库的数据）"""
    user_kb_path = os.path.join(BASE_DIR, f"kb_user_{user_id}.json")
    try:
        with open(user_kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果用户还没有进度，复制原始知识库
        kb = load_knowledge_base()
        # 给每个技能添加连续学习天数字段
        for skill in kb["skills"]:
            if "consecutive_days" not in skill:
                skill["consecutive_days"] = 0
        return kb


def save_user_knowledge_base(kb, user_id):
    """保存用户的知识库进度"""
    user_kb_path = os.path.join(BASE_DIR, f"kb_user_{user_id}.json")
    with open(user_kb_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def load_log(user_id):
    """加载用户的学习记录"""
    user_log_path = os.path.join(BASE_DIR, f"log_user_{user_id}.json")
    try:
        with open(user_log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_date": None, "history": []}


def save_log(log, user_id):
    """保存用户的学习记录"""
    user_log_path = os.path.join(BASE_DIR, f"log_user_{user_id}.json")
    with open(user_log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def load_current_learning(user_id):
    """加载用户的当前学习状态"""
    current_path = os.path.join(BASE_DIR, f"current_user_{user_id}.json")
    try:
        with open(current_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_current_learning(data, user_id):
    """保存用户的当前学习状态"""
    current_path = os.path.join(BASE_DIR, f"current_user_{user_id}.json")
    with open(current_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clear_current_learning(user_id):
    """清除用户的当前学习状态"""
    current_path = os.path.join(BASE_DIR, f"current_user_{user_id}.json")
    try:
        os.remove(current_path)
    except Exception:
        pass


def recalc_skill_avg(skill):
    """重新计算技能的平均进度值"""
    kps = skill["knowledge_points"]
    if kps:
        skill["avg_progress"] = round(sum(kp["progress"] for kp in kps) / len(kps), 1)
    else:
        skill["avg_progress"] = 0


def select_today_knowledge(kb):
    """选择今日学习知识点（轮换策略）"""
    skills = kb["skills"]
    max_days = kb.get("max_consecutive_days", MAX_CONSECUTIVE_DAYS)

    # 过滤出连续学习天数未达上限的技能
    available = [s for s in skills if s["consecutive_days"] < max_days]
    if not available:
        for s in skills:
            s["consecutive_days"] = 0
        available = skills

    # 20%概率随机选择（从进度值<70的知识点中）
    import random
    weak_kps = []
    for s in skills:
        for kp in s["knowledge_points"]:
            if kp["progress"] < 70:
                weak_kps.append((s, kp))
    if weak_kps and random.random() < 0.2:
        skill, kp = random.choice(weak_kps)
    else:
        # 优先选择平均进度值最低的技能，再选其中进度值最低的知识点
        target_skill = min(available, key=lambda s: s.get("avg_progress", 0))
        target_kp = min(target_skill["knowledge_points"], key=lambda kp: kp["progress"])

        # 查找该kp所属的skill
        skill = target_skill
        kp = target_kp

    return skill, kp


def update_progress(kp, score):
    """更新知识点进度值（带平滑）"""
    new_progress = (score / 10) * 100
    # 指数平滑：保留30%历史，70%新值
    kp["progress"] = round(kp["progress"] * 0.3 + new_progress * 0.7, 1)


# ==================== 页面路由 ====================
@app.route("/")
def index():
    """首页 - 今日学习"""
    return render_template("index.html")


@app.route("/progress")
def progress():
    """技能进度总览"""
    return render_template("progress.html")


@app.route("/history")
def history():
    """学习历史记录"""
    return render_template("history.html")


# ==================== API 路由 ====================
@app.route("/api/today", methods=["GET"])
def get_today():
    """获取今日学习内容"""
    user_id = get_user_id()
    kb = load_user_knowledge_base(user_id)
    log = load_log(user_id)
    today = str(date.today())

    # 检查是否有正在进行的知识点（用户刷新页面时恢复）
    current_learning = load_current_learning(user_id)
    if current_learning:
        # 有正在进行的知识点，返回它（不重新生成）
        return jsonify({
            "status": "in_progress",
            "skill_name": current_learning["skill_name"],
            "skill_consecutive_days": current_learning["skill_consecutive_days"],
            "knowledge_name": current_learning["knowledge_name"],
            "knowledge_progress": current_learning["knowledge_progress"],
            "knowledge_text": current_learning.get("knowledge_text"),  # 返回保存的知识点详解
            "is_iterative": current_learning.get("is_iterative", False),  # 返回是否为迭代学习
            "previous_weaknesses": current_learning.get("previous_weaknesses", []),
            "previous_strengths": current_learning.get("previous_strengths", []),
            "today_count": current_learning.get("today_count", 0),
            "is_resumed": True,  # 标记为恢复的进度
            "question": current_learning.get("question"),  # 返回缓存的练习题
            "question_answered": current_learning.get("question_answered", False)  # 返回练习题是否已回答
        })

    # 没有正在进行的知识点，获取新知识点
    today_records = [r for r in log["history"] if r["date"] == today]
    today_count = len(today_records)

    skill, kp = select_today_knowledge(kb)
    save_user_knowledge_base(kb, user_id)

    # 查找该知识点的历史学习记录
    previous_records = [
        r for r in log["history"]
        if r["knowledge"] == kp["name"] and r.get("weaknesses")
    ]

    # 获取上次的strengths
    previous_strengths = []
    if previous_records:
        previous_strengths = previous_records[-1].get("strengths", [])

    return jsonify({
        "status": "ready",
        "skill_name": skill["name"],
        "skill_consecutive_days": skill["consecutive_days"],
        "knowledge_name": kp["name"],
        "knowledge_progress": kp["progress"],
        "previous_weaknesses": previous_records[-1]["weaknesses"] if previous_records else [],
        "previous_strengths": previous_strengths,
        "today_count": today_count,
        "is_resumed": False  # 新知识点
    })


@app.route("/api/knowledge", methods=["POST"])
def get_knowledge():
    """生成知识点讲解"""
    user_id = get_user_id()
    data = request.get_json()
    kp_name = data.get("knowledge_name", "")
    skill_name = data.get("skill_name", "")
    skill_consecutive_days = data.get("skill_consecutive_days", 0)
    knowledge_progress = data.get("knowledge_progress", 0)
    previous_weaknesses = data.get("previous_weaknesses", [])
    previous_strengths = data.get("previous_strengths", [])
    today_count = data.get("today_count", 0)
    
    # 从 knowledge_base.json 中查找该知识点的已有内容
    kb = load_knowledge_base()
    kp_content = None
    kp_description = None
    
    for skill in kb.get("skills", []):
        if skill["name"] == skill_name:
            for kp in skill.get("knowledge_points", []):
                if kp["name"] == kp_name:
                    kp_content = kp.get("content")
                    kp_description = kp.get("description")
                    break
            break

    # 构建提示词
    context_str = ""
    if kp_content:
        context_str = f"\n\n参考资料（来自专业产品管理知识库）：\n{kp_content}"
    if kp_description:
        context_str += f"\n\n技能描述：{kp_description}"

    if previous_weaknesses:
        # 有历史记录，迭代学习
        weaknesses_str = "、".join(previous_weaknesses)
        strengths_str = "、".join(previous_strengths) if previous_strengths else "基本概念"
        prompt = (
            f"你是一位资深产品经理导师。用户之前学习「{kp_name}」时存在这些不足：{weaknesses_str}，但{strengths_str}已掌握。"
            f"请肯定用户已掌握的部分，并针对不足之处，重新深入讲解该知识点，重点弥补不足。"
            f"要求：400-500字左右，可以举例说明。{context_str}"
        )
    else:
        # 首次学习
        prompt = (
            f"你是一位资深产品经理导师，请用通俗易懂的语言，深入浅出地讲解以下知识点：{kp_name}。"
            f"要求：300-400字左右，可以举例说明。{context_str}"
        )
    text = call_llm(prompt)
    is_iterative = bool(previous_weaknesses)

    # 去掉首行缩进
    text = text.strip()
    if text.startswith('  ') or text.startswith('　　'):
        text = text.lstrip()

    # 保存当前正在进行的知识点（用于刷新页面后恢复）
    save_current_learning({
        "skill_name": skill_name,
        "skill_consecutive_days": skill_consecutive_days,
        "knowledge_name": kp_name,
        "knowledge_progress": knowledge_progress,
        "knowledge_text": text,  # 保存知识点详解
        "is_iterative": is_iterative,  # 保存是否为迭代学习
        "previous_weaknesses": previous_weaknesses,
        "previous_strengths": previous_strengths,
        "today_count": today_count
    }, user_id)

    return jsonify({"text": text, "is_iterative": is_iterative})


@app.route("/api/custom_knowledge", methods=["POST"])
def get_custom_knowledge():
    """生成迭代知识点（新知识点）"""
    data = request.get_json()
    kp_name = data.get("knowledge_name", "")
    previous_weaknesses = data.get("previous_weaknesses", [])
    original_explanation = data.get("original_explanation", "")

    if previous_weaknesses:
        weaknesses_str = "、".join(previous_weaknesses)
        prompt = (
            f"原知识点讲解：{original_explanation}\n\n"
            f"用户之前学习「{kp_name}」时存在这些不足：{weaknesses_str}。"
            f"请结合原知识点讲解，针对这些不足之处，生成一个新的知识点名称和对应的讲解内容。"
            f"新知识点应该是在原知识点基础上的深化或扩展，重点弥补用户的不足。"
            f"要求：新知识点名称20字以内，讲解内容300-400字左右，不要首行缩进。"
            f"输出格式：\n新知识点：[名称]\n讲解内容：[内容]"
        )
        text = call_llm(prompt)

        # 解析新知识点名称和讲解内容
        custom_kp_name = kp_name  # 默认使用原知识点名
        custom_content = text

        if "新知识点：" in text:
            parts = text.split("新知识点：", 1)
            if len(parts) > 1:
                remaining = parts[1]
                if "讲解内容：" in remaining:
                    kp_and_content = remaining.split("讲解内容：", 1)
                    custom_kp_name = kp_and_content[0].strip()
                    custom_content = kp_and_content[1].strip()
                else:
                    custom_kp_name = remaining.strip()
        
        # 去掉首行缩进
        custom_content = custom_content.strip()
        if custom_content.startswith('  ') or custom_content.startswith('　　'):
            custom_content = custom_content.lstrip()

        return jsonify({
            "custom_kp_name": custom_kp_name,
            "custom_content": custom_content
        })
    else:
        return jsonify({
            "custom_kp_name": kp_name,
            "custom_content": original_explanation
        })


@app.route("/api/question", methods=["POST"])
def get_question():
    """生成练习题"""
    user_id = get_user_id()
    data = request.get_json()
    kp_name = data.get("knowledge_name", "")
    skill_name = data.get("skill_name", "")
    custom_kp_name = data.get("custom_kp_name", kp_name)
    previous_weaknesses = data.get("previous_weaknesses", [])
    
    # 从 knowledge_base.json 中查找该知识点的已有内容
    kb = load_knowledge_base()
    kp_content = None
    kp_description = None
    
    for skill in kb.get("skills", []):
        if skill["name"] == skill_name:
            for kp in skill.get("knowledge_points", []):
                if kp["name"] == kp_name:
                    kp_content = kp.get("content")
                    kp_description = kp.get("description")
                    break
            break

    # 构建提示词
    context_str = ""
    if kp_content:
        context_str = f"\n\n参考资料（来自专业产品管理知识库）：\n{kp_content}"
    if kp_description:
        context_str += f"\n\n技能描述：{kp_description}"

    if previous_weaknesses:
        # 有历史记录，迭代学习（方式二：基于新知识点生成练习题）
        prompt = (
            f"基于知识点「{custom_kp_name}」，请出一道更有挑战性的产品经理面试题，并提供参考答案。"
            f"输出格式：\n题目：\n参考答案：{context_str}"
        )
    else:
        # 首次学习
        prompt = (
            f"基于知识点「{kp_name}」，请出一道产品经理练习题，并提供参考答案。"
            f"输出格式：\n题目：\n参考答案：{context_str}"
        )
    text = call_llm(prompt)

    # 解析题目和参考答案
    question_part = ""
    reference_part = ""
    if "参考答案" in text:
        parts = text.split("参考答案", 1)
        question_part = parts[0].replace("题目：", "").strip()
        reference_part = parts[1].strip()
    else:
        question_part = text.strip()

    # 获取当前学习状态并保存题目
    current_data = load_current_learning(user_id) or {}
    current_data["question"] = question_part
    current_data["reference"] = reference_part
    current_data["question_answered"] = False
    save_current_learning(current_data, user_id)

    return jsonify({
        "question": question_part,
        "reference": reference_part,
        "raw": text
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate_answer():
    """评估用户答案"""
    user_id = get_user_id()
    data = request.get_json()
    question = data.get("question", "")
    user_answer = data.get("user_answer", "")
    reference = data.get("reference", "")

    prompt = f"""题目：{question}
用户答案：{user_answer}
参考答案（供参考）：{reference}

请给用户的答案打分（0-10分），并按要求输出：
1. 总结：对达标之处和不足之处进行综合总结（100-150字）
2. 达标之处：3-5个要点，提取用户回答中的共同优点
3. 不足之处：3-5个要点，提取用户回答中的共同不足
4. 建议：针对不足之处给出具体、可操作的改进建议（50-100字）

输出格式：
总结：...

达标之处：
- ...
- ...
- ...
不足之处：
- ...
- ...
- ...
建议：..."""
    eval_text = call_llm(prompt)

    # 提取得分
    score = 5.0
    score_match = re.search(r'得分[：:]\s*(\d+(?:\.\d+)?)', eval_text)
    if score_match:
        score = float(score_match.group(1))
    else:
        num_match = re.search(r'(\d+(?:\.\d+)?)', eval_text)
        score = float(num_match.group(1)) if num_match else 5.0
    score = max(0, min(10, score))

    # 提取总结
    summary = ""
    summary_match = re.search(r'总结[：:]\s*([^达标之处\n]+)', eval_text)
    if summary_match:
        summary = summary_match.group(1).strip()

    # 提取达标之处和不足之处
    strengths = []
    weaknesses = []

    strengths_match = re.search(r'达标之处[：:]\s*\n((?:[-*]\s*.+\n?)*)', eval_text)
    if strengths_match:
        strengths = [line.strip(' -*') for line in strengths_match.group(1).strip().split('\n') if line.strip()]

    weaknesses_match = re.search(r'不足之处[：:]\s*\n((?:[-*]\s*.+\n?)*)', eval_text)
    if weaknesses_match:
        weaknesses = [line.strip(' -*') for line in weaknesses_match.group(1).strip().split('\n') if line.strip()]

    # 保存评估结果到当前学习状态
    current_data = load_current_learning(user_id) or {}
    current_data["score"] = score
    current_data["eval_text"] = eval_text
    current_data["strengths"] = strengths
    current_data["weaknesses"] = weaknesses
    current_data["summary"] = summary
    save_current_learning(current_data, user_id)

    return jsonify({
        "eval_text": eval_text,
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "summary": summary
    })


@app.route("/api/submit", methods=["POST"])
def submit_learning():
    """提交今日学习结果（更新进度值、生成日记、记录历史）"""
    user_id = get_user_id()
    data = request.get_json()
    skill_name = data.get("skill_name", "")
    knowledge_name = data.get("knowledge_name", "")
    score = data.get("score", 0)
    eval_text = data.get("eval_text", "")
    summary = data.get("summary", "")
    strengths = data.get("strengths", [])
    weaknesses = data.get("weaknesses", [])

    # 更新进度值
    kb = load_user_knowledge_base(user_id)
    for skill in kb["skills"]:
        if skill["name"] == skill_name:
            for kp in skill["knowledge_points"]:
                if kp["name"] == knowledge_name:
                    update_progress(kp, score)
            recalc_skill_avg(skill)
            break
    save_user_knowledge_base(kb, user_id)

    # 生成日记
    prompt = f"""基于以下信息写一篇详细的学习日记（第一人称，200-300字）
- 今日学习知识点：{knowledge_name}
- 今日总结：{summary if summary else eval_text[:200]}
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
    diary = call_llm(prompt)

    # 记录历史
    log = load_log(user_id)
    today = str(date.today())

    # 检查今天是否是新的一天，重置计数
    if log.get("last_date") != today:
        log["last_date"] = today

    log["history"].append({
        "date": today,
        "skill": skill_name,
        "knowledge": knowledge_name,
        "score": score,
        "diary": diary,
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses
    })

    # 清除当前正在进行的知识点（学习完成）
    clear_current_learning(user_id)
    save_log(log, user_id)

    # 计算今日已学习数量
    today_count = len([r for r in log["history"] if r["date"] == today])

    return jsonify({
        "status": "success",
        "diary": diary,
        "score": score,
        "today_count": today_count
    })


@app.route("/api/current_learning", methods=["POST"])
def update_current_learning():
    """更新当前学习进度（保存练习题状态）"""
    user_id = get_user_id()
    data = request.get_json()
    current_data = load_current_learning(user_id) or {}
    
    # 更新现有数据
    if "knowledge_text" in data:
        current_data["knowledge_text"] = data["knowledge_text"]
    if "question" in data:
        current_data["question"] = data["question"]
    if "reference" in data:
        current_data["reference"] = data["reference"]
    if "question_answered" in data:
        current_data["question_answered"] = data["question_answered"]
    
    save_current_learning(current_data, user_id)
    
    return jsonify({"status": "success"})


@app.route("/api/progress", methods=["GET"])
def get_progress():
    """获取技能进度数据"""
    user_id = get_user_id()
    kb = load_user_knowledge_base(user_id)
    return jsonify(kb)


@app.route("/api/history", methods=["GET"])
def get_history():
    """获取学习历史（按日期分组）"""
    user_id = get_user_id()
    log = load_log(user_id)
    history = log.get("history", [])

    # 按日期分组
    grouped = {}
    for record in history:
        date = record["date"]
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(record)

    # 计算总学习时长（每次学习约5分钟）
    total_duration = len(history) * 5  # 分钟

    return jsonify({
        "history": history,
        "grouped": grouped,  # 按日期分组的历史
        "total_duration": total_duration,
        "total_count": len(history)
    })


@app.route("/evaluate", methods=["GET"])
def evaluate_page():
    """AI评估页面"""
    return render_template("evaluate.html")


@app.route("/diary", methods=["GET"])
def diary_page():
    """学习日记页面"""
    return render_template("diary.html")


# ==================== 启动 ====================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
