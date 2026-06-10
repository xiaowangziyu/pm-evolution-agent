#!/usr/bin/env python3
"""
推荐系统覆盖度测试脚本

测试目的：
- 验证自动规划算法是否会让知识点选择比较平均
- 防止只有几个知识点被反复训练，而大量知识点未被选择
- 查看多次调用后的进度值分布，确认是否出现过度偏向

功能特点：
- 初始所有技能、知识点进度设为0
- 每次调用生成的评分/进度为随机值
- 真实模拟 app.py 中的推荐算法
- 统计技能/知识点被推荐的频率
- 统计最终各进度值的分布
- 输出可视化统计结果
"""

import json
import os
import sys
import shutil
import random
from collections import defaultdict
from datetime import datetime

# 配置参数
TEST_USER_ID = "test_auto"
TEST_ITERATIONS = 150  # 测试次数，建议150次（74个知识点×2）
TEST_TEMP_DIR = "test_temp"

# 随机种子固定，保证结果可复现
random.seed(42)


def load_real_knowledge_base():
    """加载真实的知识库"""
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_test_knowledge_base(base_kb):
    """创建测试用的知识库，所有进度设为0"""
    test_kb = json.loads(json.dumps(base_kb))  # 深拷贝
    
    for skill in test_kb["skills"]:
        skill["avg_progress"] = 0.0
        skill["consecutive_days"] = 0
        for kp in skill["knowledge_points"]:
            kp["progress"] = 0.0
    
    return test_kb


def select_next_skill_and_knowledge(kb):
    """
    模拟 app.py 中的推荐算法
    返回：(skill_name, knowledge_point_name)
    """
    max_consec = kb.get("max_consecutive_days", 3)
    
    # 步骤1: 筛选未超过连续学习天数的技能
    available_skills = []
    for skill in kb["skills"]:
        if skill.get("consecutive_days", 0) < max_consec:
            available_skills.append(skill)
    
    if not available_skills:
        available_skills = kb["skills"]
    
    # 步骤2: 20%概率从进度<70的知识点中随机选择
    if random.random() < 0.2:
        candidates = []
        for skill in available_skills:
            for kp in skill["knowledge_points"]:
                if kp.get("progress", 0) < 70:
                    candidates.append((skill, kp))
        if candidates:
            selected_skill, selected_kp = random.choice(candidates)
            return selected_skill["name"], selected_kp["name"]
    
    # 步骤3: 80%概率选择进度最低的技能，然后选择该技能下进度最低的知识点
    sorted_skills = sorted(available_skills, key=lambda s: s.get("avg_progress", 0))
    selected_skill = sorted_skills[0]
    
    sorted_kps = sorted(selected_skill["knowledge_points"], key=lambda kp: kp.get("progress", 0))
    selected_kp = sorted_kps[0]
    
    return selected_skill["name"], selected_kp["name"]


def update_progress_for_knowledge(kb, skill_name, kp_name, score):
    """
    更新知识点和技能进度，模拟 app.py 中的指数平滑算法
    """
    for skill in kb["skills"]:
        if skill["name"] == skill_name:
            # 更新知识点进度
            for kp in skill["knowledge_points"]:
                if kp["name"] == kp_name:
                    new_prog = (score / 10) * 100
                    kp["progress"] = round(kp["progress"] * 0.3 + new_prog * 0.7, 1)
            
            # 更新技能平均进度
            total = 0.0
            count = 0
            for kp in skill["knowledge_points"]:
                total += kp["progress"]
                count += 1
            skill["avg_progress"] = round(total / count, 1) if count > 0 else 0.0
            break


def run_tests():
    """运行完整测试"""
    print("=" * 80)
    print("推荐系统覆盖度测试")
    print("=" * 80)
    print(f"测试次数: {TEST_ITERATIONS}")
    print()
    
    # 步骤1: 准备测试环境
    base_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(base_dir, TEST_TEMP_DIR)
    
    print("1. 准备测试环境...")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # 步骤2: 加载并初始化知识库
    print("2. 加载并初始化知识库...")
    real_kb = load_real_knowledge_base()
    test_kb = create_test_knowledge_base(real_kb)
    
    total_skills = len(test_kb["skills"])
    total_kps = 0
    for skill in test_kb["skills"]:
        total_kps += len(skill["knowledge_points"])
    
    print(f"   - 总技能数: {total_skills}")
    print(f"   - 总知识点数: {total_kps}")
    
    # 步骤3: 开始模拟测试
    print("\n3. 开始模拟学习...")
    print("-" * 80)
    
    skill_recommend_count = defaultdict(int)
    kp_recommend_count = defaultdict(int)
    history = []
    
    for i in range(TEST_ITERATIONS):
        # 选择知识点
        skill_name, kp_name = select_next_skill_and_knowledge(test_kb)
        
        # 记录
        skill_recommend_count[skill_name] += 1
        kp_recommend_count[kp_name] += 1
        
        # 模拟评分（3-9分随机，对应30%-90%的初始进度）
        score = random.uniform(3, 9)
        score = round(score, 1)  # 保留一位小数
        
        # 更新进度
        update_progress_for_knowledge(test_kb, skill_name, kp_name, score)
        
        # 记录历史
        history.append({
            "iteration": i + 1,
            "skill": skill_name,
            "knowledge_point": kp_name,
            "score": score
        })
        
        if (i + 1) % 30 == 0:
            print(f"   已完成 {i + 1}/{TEST_ITERATIONS} 次...")
    
    # 步骤4: 统计结果
    print("\n4. 统计结果...")
    print("=" * 80)
    
    # 技能推荐频率
    print("\n【技能推荐频率统计】")
    print("-" * 80)
    print(f"{'技能名称':<30} {'推荐次数':<10} {'占比':<10}")
    print("-" * 60)
    
    sorted_skills = sorted(skill_recommend_count.items(), key=lambda x: (-x[1], x[0]))
    for skill_name, count in sorted_skills:
        pct = (count / TEST_ITERATIONS) * 100
        print(f"{skill_name:<30} {count:<10} {pct:>5.1f}%")
    
    # 知识点推荐频率（只显示前15和后15）
    print("\n【知识点推荐频率 - Top15】")
    print("-" * 80)
    sorted_kps = sorted(kp_recommend_count.items(), key=lambda x: (-x[1], x[0]))
    
    print(f"{'知识点名称':<50} {'推荐次数':<10}")
    print("-" * 60)
    for kp_name, count in sorted_kps[:15]:
        print(f"{kp_name:<50} {count:<10}")
    
    if len(sorted_kps) > 30:
        print("...")
    
    print("\n【知识点推荐频率 - 后15】")
    print("-" * 80)
    for kp_name, count in sorted_kps[-15:]:
        print(f"{kp_name:<50} {count:<10}")
    
    # 未被推荐的知识点
    all_kps = set()
    for skill in test_kb["skills"]:
        for kp in skill["knowledge_points"]:
            all_kps.add(kp["name"])
    not_recommended = all_kps - set(kp_recommend_count.keys())
    
    print("\n【未被推荐的知识点】")
    print("-" * 80)
    if not_recommended:
        print(f"⚠️  警告: 共有 {len(not_recommended)} 个知识点从未被推荐!")
        for kp in sorted(not_recommended):
            print(f"   - {kp}")
    else:
        print("✅ 所有知识点均被推荐过!")
    
    # 最终进度分布
    print("\n【最终进度分布统计】")
    print("-" * 80)
    
    skill_progress_stats = []
    kp_progress_stats = []
    
    for skill in test_kb["skills"]:
        skill_progress_stats.append({
            "name": skill["name"],
            "avg_progress": skill["avg_progress"]
        })
        for kp in skill["knowledge_points"]:
            kp_progress_stats.append({
                "name": kp["name"],
                "progress": kp["progress"]
            })
    
    # 技能进度
    print("\n技能进度 (按平均进度排序):")
    sorted_skill_progress = sorted(skill_progress_stats, key=lambda x: -x["avg_progress"])
    for item in sorted_skill_progress:
        print(f"   {item['name']:<30} {item['avg_progress']:>5.1f}%")
    
    # 知识点进度分布区间
    print("\n知识点进度分布:")
    ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    range_counts = defaultdict(int)
    
    for item in kp_progress_stats:
        for start, end in ranges:
            if start <= item["progress"] < end:
                range_counts[f"{start}-{end}"] += 1
                break
        if item["progress"] >= 100:
            range_counts["100"] += 1
    
    for range_name in sorted(range_counts.keys()):
        count = range_counts[range_name]
        pct = (count / len(kp_progress_stats)) * 100
        print(f"   进度 {range_name}%: {count:>3} 个 ({pct:>4.1f}%)")
    
    # 检查过度偏向
    print("\n【检查过度偏向情况】")
    print("-" * 80)
    
    # 检查是否有知识点进度异常高
    high_progress_kps = [item for item in kp_progress_stats if item["progress"] > 80]
    if len(high_progress_kps) > 10:
        print(f"⚠️  警告: 有 {len(high_progress_kps)} 个知识点进度 > 80%!")
    else:
        print("✅ 进度分布相对均匀，未发现严重过度偏向。")
    
    # 推荐频率方差（简单的不均衡度检查）
    counts = list(kp_recommend_count.values())
    avg_count = sum(counts) / len(counts) if counts else 0
    max_count = max(counts) if counts else 0
    min_count = min(counts) if counts else 0
    
    print(f"\n推荐频率统计:")
    print(f"   - 平均每个知识点被推荐: {avg_count:.1f} 次")
    print(f"   - 最高: {max_count} 次")
    print(f"   - 最低: {min_count} 次")
    
    # 步骤5: 清理环境
    print("\n5. 清理测试环境...")
    shutil.rmtree(temp_dir)
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    exit_code = 0
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n用户中断测试")
        exit_code = 1
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    sys.exit(exit_code)
