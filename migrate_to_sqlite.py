#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本 - 从 JSON 文件迁移到 SQLite

运行方式：
    python migrate_to_sqlite.py

注意：
    1. 运行前确保所有 JSON 文件都在项目目录中
    2. 迁移前会自动备份 JSON 文件到 backup/ 目录
    3. 如果数据库已存在，会跳过已存在的记录
"""

import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 导入数据库模块
import db

def backup_json_files():
    """备份 JSON 文件"""
    backup_dir = os.path.join(BASE_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_count = 0
    for fname in os.listdir(BASE_DIR):
        if (fname.startswith("log_user_") or 
            fname.startswith("kb_user_") or 
            fname.startswith("current_user_")) and fname.endswith(".json"):
            src = os.path.join(BASE_DIR, fname)
            dst = os.path.join(backup_dir, fname)
            shutil.copy(src, dst)
            backup_count += 1
    
    if backup_count > 0:
        print(f"[备份] 已备份 {backup_count} 个 JSON 文件到 backup/")
    return backup_count

def migrate_log_files():
    """迁移学习记录文件"""
    count = 0
    for fname in os.listdir(BASE_DIR):
        if fname.startswith("log_user_") and fname.endswith(".json"):
            user_id = fname.replace("log_user_", "").replace(".json", "")
            fpath = os.path.join(BASE_DIR, fname)
            
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                history = data.get("history", [])
                for record in history:
                    db.add_learning_record(
                        session_id=user_id,
                        date=record.get("date"),
                        skill=record.get("skill"),
                        knowledge=record.get("knowledge"),
                        score=record.get("score"),
                        summary=record.get("summary"),
                        strengths=record.get("strengths", []),
                        weaknesses=record.get("weaknesses", []),
                        diary=record.get("diary")
                    )
                    count += 1
                
                print(f"[迁移] {fname}: {len(history)} 条记录")
            except Exception as e:
                print(f"[错误] 迁移 {fname} 失败: {e}")
    
    return count

def migrate_kb_files():
    """迁移用户进度文件"""
    count = 0
    for fname in os.listdir(BASE_DIR):
        if fname.startswith("kb_user_") and fname.endswith(".json"):
            user_id = fname.replace("kb_user_", "").replace(".json", "")
            fpath = os.path.join(BASE_DIR, fname)
            
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                skills = data.get("skills", [])
                for skill in skills:
                    skill_name = skill.get("name")
                    consecutive_days = skill.get("consecutive_days", 0)
                    
                    for kp in skill.get("knowledge_points", []):
                        db.update_user_progress(
                            session_id=user_id,
                            skill_name=skill_name,
                            knowledge_name=kp.get("name"),
                            progress=kp.get("progress", 0),
                            consecutive_days=consecutive_days
                        )
                        count += 1
                
                print(f"[迁移] {fname}: {len(skills)} 个技能, {count} 个知识点")
            except Exception as e:
                print(f"[错误] 迁移 {fname} 失败: {e}")
    
    return count

def migrate_current_files():
    """迁移当前学习状态文件"""
    count = 0
    for fname in os.listdir(BASE_DIR):
        if fname.startswith("current_user_") and fname.endswith(".json"):
            user_id = fname.replace("current_user_", "").replace(".json", "")
            fpath = os.path.join(BASE_DIR, fname)
            
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data:
                    db.update_current_learning(session_id=user_id, data=data)
                    count += 1
                    print(f"[迁移] {fname}")
            except Exception as e:
                print(f"[错误] 迁移 {fname} 失败: {e}")
    
    return count

def verify_migration():
    """验证迁移结果"""
    print("\n[验证] 迁移结果：")
    
    # 统计学习记录
    conn = db.get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM learning_records')
    record_count = cursor.fetchone()[0]
    print(f"  学习记录: {record_count} 条")
    
    cursor.execute('SELECT COUNT(*) FROM user_progress')
    progress_count = cursor.fetchone()[0]
    print(f"  用户进度: {progress_count} 条")
    
    cursor.execute('SELECT COUNT(*) FROM current_learning')
    current_count = cursor.fetchone()[0]
    print(f"  当前学习状态: {current_count} 条")
    
    conn.close()
    return record_count + progress_count + current_count

def migrate_knowledge_base():
    """迁移知识库（从 knowledge_base.json）"""
    kb_path = os.path.join(BASE_DIR, "knowledge_base.json")
    if not os.path.exists(kb_path):
        print(f"  未找到 knowledge_base.json")
        return 0
    
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
    
    skill_count = 0
    kp_count = 0
    
    for skill in kb_data.get("skills", []):
        skill_name = skill.get("name")
        skill_desc = skill.get("description", "")
        
        db.add_skill(skill_name, skill_desc)
        skill_count += 1
        
        for kp in skill.get("knowledge_points", []):
            db.add_knowledge_point(
                skill_name=skill_name,
                name=kp.get("name"),
                description=kp.get("description", ""),
                content=kp.get("content", "")
            )
            kp_count += 1
    
    print(f"  迁移 {skill_count} 个技能, {kp_count} 个知识点")
    return skill_count + kp_count

def main():
    print("=" * 60)
    print("数据迁移脚本 - JSON → SQLite")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 备份
    print("[步骤1/6] 备份 JSON 文件...")
    backup_json_files()
    
    # 2. 初始化数据库
    print("\n[步骤2/6] 初始化数据库表...")
    db.init_db()
    
    # 3. 迁移知识库
    print("\n[步骤3/6] 迁移知识库...")
    migrate_knowledge_base()
    
    # 4. 迁移学习记录
    print("\n[步骤4/6] 迁移学习记录...")
    migrate_log_files()
    
    # 5. 迁移用户进度
    print("\n[步骤5/6] 迁移用户进度...")
    migrate_kb_files()
    
    # 6. 迁移当前学习状态
    print("\n[步骤6/6] 迁移当前学习状态...")
    migrate_current_files()
    
    # 验证
    total = verify_migration()
    
    print("\n" + "=" * 60)
    if total > 0:
        print(f"✓ 迁移完成！共迁移 {total} 条记录")
        print(f"数据库文件: {db.DB_PATH}")
    else:
        print("⚠️  没有找到可迁移的数据")
    print("=" * 60)

if __name__ == "__main__":
    main()
