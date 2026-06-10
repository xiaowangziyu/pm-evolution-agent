"""
数据库操作模块 - SQLite 封装

功能：
- 初始化数据库表
- 学习记录 CRUD
- 用户进度 CRUD  
- 当前学习状态 CRUD
"""

import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pm_evolution.db")

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典形式
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 知识库表（技能-知识点结构）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(skill_id, name),
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    ''')
    
    # 学习记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            date TEXT NOT NULL,
            skill TEXT,
            knowledge TEXT,
            score REAL,
            summary TEXT,
            strengths TEXT,
            weaknesses TEXT,
            diary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 用户进度表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            knowledge_name TEXT NOT NULL,
            progress REAL DEFAULT 0,
            consecutive_days INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, skill_name, knowledge_name)
        )
    ''')
    
    # 当前学习状态表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            skill_name TEXT,
            knowledge_name TEXT,
            knowledge_text TEXT,
            question TEXT,
            reference TEXT,
            question_answered INTEGER DEFAULT 0,
            skill_consecutive_days INTEGER DEFAULT 0,
            knowledge_progress REAL DEFAULT 0,
            today_count INTEGER DEFAULT 0,
            previous_weaknesses TEXT,
            previous_strengths TEXT,
            is_iterative INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kp_skill ON knowledge_points(skill_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_records_session ON learning_records(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_records_date ON learning_records(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_session ON user_progress(session_id)')
    
    conn.commit()
    conn.close()
    print("[DB] 数据库表初始化完成")

# ==================== 知识库操作 ====================

def add_skill(name, description=""):
    """添加技能"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT OR IGNORE INTO skills (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
    finally:
        conn.close()

def add_knowledge_point(skill_name, name, description="", content=""):
    """添加知识点"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 获取技能ID
        cursor.execute('SELECT id FROM skills WHERE name = ?', (skill_name,))
        row = cursor.fetchone()
        if not row:
            return False
        
        skill_id = row["id"]
        cursor.execute('''
            INSERT OR IGNORE INTO knowledge_points 
            (skill_id, name, description, content) VALUES (?, ?, ?, ?)
        ''', (skill_id, name, description, content))
        conn.commit()
        return True
    finally:
        conn.close()

def get_all_skills():
    """获取所有技能及其知识点"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM skills ORDER BY name')
    skill_rows = cursor.fetchall()
    
    skills = []
    for skill_row in skill_rows:
        cursor.execute('SELECT * FROM knowledge_points WHERE skill_id = ? ORDER BY name', (skill_row["id"],))
        kp_rows = cursor.fetchall()
        
        knowledge_points = []
        for kp_row in kp_rows:
            knowledge_points.append({
                "name": kp_row["name"],
                "description": kp_row["description"],
                "content": kp_row["content"]
            })
        
        skills.append({
            "id": skill_row["id"],
            "name": skill_row["name"],
            "description": skill_row["description"],
            "knowledge_points": knowledge_points
        })
    
    conn.close()
    return skills

def get_skill_by_name(skill_name):
    """根据名称获取技能"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM skills WHERE name = ?', (skill_name,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    cursor.execute('SELECT * FROM knowledge_points WHERE skill_id = ? ORDER BY name', (row["id"],))
    kp_rows = cursor.fetchall()
    
    knowledge_points = []
    for kp_row in kp_rows:
        knowledge_points.append({
            "name": kp_row["name"],
            "description": kp_row["description"],
            "content": kp_row["content"]
        })
    
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "knowledge_points": knowledge_points
    }

def get_knowledge_point(skill_name, knowledge_name):
    """获取特定知识点"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM skills WHERE name = ?', (skill_name,))
    skill_row = cursor.fetchone()
    
    if not skill_row:
        conn.close()
        return None
    
    cursor.execute('''
        SELECT * FROM knowledge_points 
        WHERE skill_id = ? AND name = ?
    ''', (skill_row["id"], knowledge_name))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "name": row["name"],
            "description": row["description"],
            "content": row["content"]
        }
    return None

def get_knowledge_count():
    """获取知识点总数"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM knowledge_points')
    row = cursor.fetchone()
    
    conn.close()
    return row[0] if row else 0

# ==================== 学习记录操作 ====================

def add_learning_record(session_id, date, skill, knowledge, score, summary, strengths, weaknesses, diary):
    """添加学习记录"""
    conn = get_db()
    cursor = conn.cursor()
    strengths_json = json.dumps(strengths, ensure_ascii=False) if strengths else "[]"
    weaknesses_json = json.dumps(weaknesses, ensure_ascii=False) if weaknesses else "[]"
    
    cursor.execute('''
        INSERT INTO learning_records 
        (session_id, date, skill, knowledge, score, summary, strengths, weaknesses, diary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, date, skill, knowledge, score, summary, strengths_json, weaknesses_json, diary))
    
    conn.commit()
    conn.close()

def get_user_records(session_id):
    """获取用户所有学习记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM learning_records WHERE session_id = ? ORDER BY date DESC', (session_id,))
    rows = cursor.fetchall()
    
    records = []
    for row in rows:
        records.append({
            "date": row["date"],
            "skill": row["skill"],
            "knowledge": row["knowledge"],
            "score": row["score"],
            "summary": row["summary"],
            "strengths": json.loads(row["strengths"]) if row["strengths"] else [],
            "weaknesses": json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            "diary": row["diary"]
        })
    
    conn.close()
    return {"last_date": records[0]["date"] if records else None, "history": records}

def get_today_records(session_id, today):
    """获取今日学习记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM learning_records WHERE session_id = ? AND date = ?', (session_id, today))
    rows = cursor.fetchall()
    
    records = []
    for row in rows:
        records.append({
            "date": row["date"],
            "skill": row["skill"],
            "knowledge": row["knowledge"],
            "score": row["score"],
            "summary": row["summary"],
            "strengths": json.loads(row["strengths"]) if row["strengths"] else [],
            "weaknesses": json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            "diary": row["diary"]
        })
    
    conn.close()
    return records

# ==================== 用户进度操作 ====================

def update_user_progress(session_id, skill_name, knowledge_name, progress, consecutive_days):
    """更新用户进度（插入或更新）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_progress 
        (session_id, skill_name, knowledge_name, progress, consecutive_days, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, skill_name, knowledge_name, progress, consecutive_days, datetime.now()))
    
    conn.commit()
    conn.close()

def get_user_progress(session_id, skill_name=None, knowledge_name=None):
    """获取用户进度"""
    conn = get_db()
    cursor = conn.cursor()
    
    if skill_name and knowledge_name:
        cursor.execute('''
            SELECT * FROM user_progress 
            WHERE session_id = ? AND skill_name = ? AND knowledge_name = ?
        ''', (session_id, skill_name, knowledge_name))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "progress": row["progress"],
                "consecutive_days": row["consecutive_days"]
            }
        return None
    
    # 获取所有进度
    cursor.execute('SELECT * FROM user_progress WHERE session_id = ?', (session_id,))
    rows = cursor.fetchall()
    
    # 按技能分组
    result = {}
    for row in rows:
        skill = row["skill_name"]
        if skill not in result:
            result[skill] = {
                "name": skill,
                "consecutive_days": row["consecutive_days"],
                "knowledge_points": []
            }
        result[skill]["knowledge_points"].append({
            "name": row["knowledge_name"],
            "progress": row["progress"]
        })
    
    conn.close()
    return result

def get_knowledge_progress(session_id, skill_name, knowledge_name):
    """获取特定知识点进度"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT progress FROM user_progress 
        WHERE session_id = ? AND skill_name = ? AND knowledge_name = ?
    ''', (session_id, skill_name, knowledge_name))
    row = cursor.fetchone()
    
    conn.close()
    return row["progress"] if row else 0.0

def get_skill_consecutive_days(session_id, skill_name):
    """获取技能连续学习天数"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT consecutive_days FROM user_progress 
        WHERE session_id = ? AND skill_name = ? LIMIT 1
    ''', (session_id, skill_name))
    row = cursor.fetchone()
    
    conn.close()
    return row["consecutive_days"] if row else 0

# ==================== 当前学习状态操作 ====================

def update_current_learning(session_id, data):
    """更新当前学习状态"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO current_learning 
        (session_id, skill_name, knowledge_name, knowledge_text, question, reference,
         question_answered, skill_consecutive_days, knowledge_progress, today_count,
         previous_weaknesses, previous_strengths, is_iterative, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        data.get("skill_name"),
        data.get("knowledge_name"),
        data.get("knowledge_text"),
        data.get("question"),
        data.get("reference"),
        1 if data.get("question_answered") else 0,
        data.get("skill_consecutive_days", 0),
        data.get("knowledge_progress", 0),
        data.get("today_count", 0),
        json.dumps(data.get("previous_weaknesses", []), ensure_ascii=False),
        json.dumps(data.get("previous_strengths", []), ensure_ascii=False),
        1 if data.get("is_iterative") else 0,
        datetime.now()
    ))
    
    conn.commit()
    conn.close()

def get_current_learning(session_id):
    """获取当前学习状态"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM current_learning WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    
    conn.close()
    if not row:
        return None
    
    return {
        "skill_name": row["skill_name"],
        "skill_consecutive_days": row["skill_consecutive_days"],
        "knowledge_name": row["knowledge_name"],
        "knowledge_progress": row["knowledge_progress"],
        "knowledge_text": row["knowledge_text"],
        "question": row["question"],
        "reference": row["reference"],
        "question_answered": bool(row["question_answered"]),
        "today_count": row["today_count"],
        "is_iterative": bool(row["is_iterative"]),
        "previous_weaknesses": json.loads(row["previous_weaknesses"]) if row["previous_weaknesses"] else [],
        "previous_strengths": json.loads(row["previous_strengths"]) if row["previous_strengths"] else []
    }

def clear_current_learning(session_id):
    """清除当前学习状态"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM current_learning WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

# ==================== 统计操作 ====================

def get_total_learning_count(session_id):
    """获取用户学习总次数"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM learning_records WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    
    conn.close()
    return row[0] if row else 0

def get_today_learning_count(session_id, today):
    """获取今日学习次数"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM learning_records WHERE session_id = ? AND date = ?', (session_id, today))
    row = cursor.fetchone()
    
    conn.close()
    return row[0] if row else 0

# 初始化（每次导入时都确保表存在）
init_db()
