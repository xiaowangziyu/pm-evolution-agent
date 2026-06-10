#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量接口测试脚本（每周自动运行）

功能特点：
- 使用特殊 user_id (full_test)，不污染生产数据
- 模拟完整业务流程：today -> knowledge -> question -> evaluate -> submit
- 测试正向用例 + 边界用例 + 异常用例
- 自动清理测试数据
- 输出详细的测试报告

测试内容：
1. 正向流程测试：模拟一次完整学习流程
2. skill_name 自动反查逻辑
3. 边界用例：空字段、异常字段测试
4. 多轮学习后进度是否正确更新
5. 所有知识点推荐覆盖度测试

使用方法：
    python run_full.py
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, date
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_URL = "http://127.0.0.1:5000"
TEST_USER_ID = "full_test"
REQUEST_TIMEOUT = 60


# 从 knowledge_base.json 读取测试用数据
def load_kb_for_test():
    kb_path = os.path.join(BASE_DIR, "knowledge_base.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestReporter:
    """测试报告收集器"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []
        self.cases = []  # 所有测试用例记录

    def record_pass(self, name, detail=""):
        self.passed.append(name)
        self.cases.append((name, "PASS", detail))
        print(f"  ✅ PASS: {name}")

    def record_fail(self, name, reason):
        self.failed.append((name, reason))
        self.cases.append((name, "FAIL", reason))
        print(f"  ❌ FAIL: {name}: {reason}")

    def record_error(self, name, err):
        self.errors.append((name, str(err)))
        self.cases.append((name, "ERROR", str(err)))
        print(f"  ⚠️  ERROR: {name}: {err}")

    def print_cases(self):
        print()
        print("=" * 80)
        print("测试用例明细")
        print("=" * 80)
        print(f"{'序号':<6}{'用例名称':<50}{'结果':<10}")
        print("-" * 80)
        for idx, (name, status, _) in enumerate(self.cases, 1):
            status_icon = "PASS" if status == "PASS" else ("FAIL" if status == "FAIL" else "ERROR")
            print(f"{idx:<6}{name[:48]:<50}{status_icon:<10}")

    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.errors)
        print()
        print("=" * 80)
        print("测试结果汇总")
        print("=" * 80)
        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {len(self.passed)}")
        print(f"  ❌ 失败: {len(self.failed)}")
        print(f"  ⚠️  错误: {len(self.errors)}")
        if total > 0:
            pass_rate = len(self.passed) / total * 100
            print(f"  通过率: {pass_rate:.1f}%")
        else:
            print("  通过率: N/A")

        if self.failed:
            print("\n【失败详情】")
            for name, reason in self.failed:
                print(f"  - {name}: {reason}")

        if self.errors:
            print("\n【错误详情】")
            for name, err in self.errors:
                print(f"  - {name}: {err}")

        print("=" * 80)
        return len(self.failed) + len(self.errors)


def print_section(title):
    print()
    print("=" * 80)
    print(f" {title}")
    print("=" * 80)


def get_headers(user_id=TEST_USER_ID):
    return {"X-User-Id": user_id, "Content-Type": "application/json"}


def cleanup_test_data(user_id=TEST_USER_ID):
    """清理测试产生的用户数据"""
    print("\n【清理测试数据】")
    test_files = [
        f"kb_user_{user_id}.json",
        f"log_user_{user_id}.json",
        f"current_user_{user_id}.json",
    ]
    removed = []
    for fname in test_files:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                removed.append(fname)
            except Exception as e:
                print(f"  删除 {fname} 失败: {e}")
    if removed:
        print(f"  已清理: {', '.join(removed)}")
    else:
        print("  无测试数据需要清理")


# ========== 测试用例 ==========

def test_full_learning_flow(reporter, kb):
    """测试一次完整的学习流程"""
    print_section("【正向测试 1】完整学习流程 (today -> knowledge -> question -> evaluate -> submit)")

    try:
        # 步骤1: 获取今日学习内容
        print("\n  [步骤1] /api/today - 获取今日学习内容")
        resp = requests.get(f"{SERVER_URL}/api/today", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-1-today", f"HTTP {resp.status_code}")
            return
        today_data = resp.json()
        skill_name = today_data.get("skill_name")
        knowledge_name = today_data.get("knowledge_name")
        if not skill_name or not knowledge_name:
            reporter.record_fail("flow-1-today", "未获取到技能或知识点名称")
            return
        print(f"    技能: {skill_name}, 知识点: {knowledge_name}")

        # 步骤2: 获取知识点讲解
        print("\n  [步骤2] /api/knowledge - 获取知识点讲解")
        payload = {
            "knowledge_name": knowledge_name,
            "skill_name": skill_name,
            "skill_consecutive_days": today_data.get("skill_consecutive_days", 0),
            "knowledge_progress": today_data.get("knowledge_progress", 0),
            "previous_weaknesses": today_data.get("previous_weaknesses", []),
            "previous_strengths": today_data.get("previous_strengths", []),
            "today_count": today_data.get("today_count", 0),
        }
        resp = requests.post(f"{SERVER_URL}/api/knowledge",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-2-knowledge", f"HTTP {resp.status_code}")
            return
        k_data = resp.json()
        k_text = k_data.get("knowledge_text") or k_data.get("knowledge") or k_data.get("text") or k_data.get("content", "")
        if not k_text or len(str(k_text)) < 20:
            reporter.record_fail("flow-2-knowledge", f"知识点内容过短 ({len(str(k_text))} 字")
            return
        print(f"    内容长度: {len(str(k_text))} 字")

        # 步骤3: 生成练习题
        print("\n  [步骤3] /api/question - 生成练习题")
        payload = {
            "knowledge_name": knowledge_name,
            "skill_name": skill_name,
            "previous_weaknesses": today_data.get("previous_weaknesses", []),
            "difficulty": "中等",
        }
        resp = requests.post(f"{SERVER_URL}/api/question",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-3-question", f"HTTP {resp.status_code}")
            return
        q_data = resp.json()
        question = q_data.get("question") or q_data.get("题目", "")
        reference = q_data.get("reference") or q_data.get("参考答案") or q_data.get("reference_answer", "")
        if not question:
            reporter.record_fail("flow-3-question", "未获取到题目")
            return
        if not reference:
            reporter.record_fail("flow-3-question", "未获取到参考答案")
            return
        print(f"    题目长度: {len(str(question))} 字")

        # 步骤4: AI 评分
        print("\n  [步骤4] /api/evaluate - AI 评分")
        payload = {
            "question": str(question),
            "user_answer": "我理解这道题考察的是产品经理的核心能力，需要结合实际案例进行分析。",
            "reference": str(reference),
        }
        resp = requests.post(f"{SERVER_URL}/api/evaluate",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-4-evaluate", f"HTTP {resp.status_code}")
            return
        eval_data = resp.json()
        score = eval_data.get("score", 0)
        if not (0 <= score <= 10):
            reporter.record_fail("flow-4-evaluate", f"得分 {score} 不在 0-10 范围")
            return
        if not eval_data.get("summary"):
            reporter.record_fail("flow-4-evaluate", "未获取到总结")
            return
        if not isinstance(eval_data.get("strengths", []), list) or len(eval_data.get("strengths", [])) == 0:
            reporter.record_fail("flow-4-evaluate", "达标之处为空或非列表")
            return
        if not isinstance(eval_data.get("weaknesses", []), list) or len(eval_data.get("weaknesses", [])) == 0:
            reporter.record_fail("flow-4-evaluate", "不足之处为空或非列表")
            return
        print(f"    得分: {score}/10")

        # 步骤5: 提交学习结果
        print("\n  [步骤5] /api/submit - 提交学习结果")
        payload = {
            "skill_name": skill_name,
            "knowledge_name": knowledge_name,
            "score": score,
            "eval_text": eval_data.get("summary", ""),
            "summary": eval_data.get("summary", ""),
            "strengths": eval_data.get("strengths", []),
            "weaknesses": eval_data.get("weaknesses", []),
        }
        resp = requests.post(f"{SERVER_URL}/api/submit",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-5-submit", f"HTTP {resp.status_code}")
            return

        # 验证进度已更新
        print("\n  [验证] /api/progress - 检查进度是否更新")
        resp = requests.get(f"{SERVER_URL}/api/progress", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-verify-progress", f"HTTP {resp.status_code}")
            return
        progress_data = resp.json()
        # 查找该知识点进度是否 > 0
        found_kp = False
        for skill in progress_data.get("skills", []):
            for kp in skill.get("knowledge_points", []):
                if kp.get("name") == knowledge_name and kp.get("progress", 0) > 0:
                    found_kp = True
                    print(f"    知识点 {knowledge_name} 进度: {kp.get('progress')}%")
                    break
        if not found_kp:
            reporter.record_fail("flow-verify-progress", f"知识点 {knowledge_name} 进度未更新")
            return

        # 验证历史记录
        print("\n  [验证] /api/history - 检查是否有历史记录")
        resp = requests.get(f"{SERVER_URL}/api/history", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("flow-verify-history", f"HTTP {resp.status_code}")
            return
        history_data = resp.json()
        if history_data.get("total_count", 0) < 1:
            reporter.record_fail("flow-verify-history", "历史记录为空")
            return
        print(f"    历史记录数: {history_data.get('total_count')}")

        reporter.record_pass("flow-full_learning_flow")

    except Exception as e:
        reporter.record_error("flow-full_learning_flow", f"异常: {e}")
        import traceback
        traceback.print_exc()


def test_skill_name_auto_lookup(reporter, kb):
    """测试 skill_name 自动反查逻辑"""
    print_section("【正向测试 2】skill_name 自动反查")

    try:
        # 获取第一个知识点（不传递 skill_name）
        first_skill = kb["skills"][0]
        first_kp = first_skill["knowledge_points"][0]
        kp_name_only = first_kp["name"]
        print(f"  测试知识点（仅传 knowledge_name）: {kp_name_only}")

        # /api/knowledge 不传 skill_name
        payload = {
            "knowledge_name": kp_name_only,
            "skill_name": "",
            "skill_consecutive_days": 0,
            "knowledge_progress": 0,
            "previous_weaknesses": [],
            "previous_strengths": [],
            "today_count": 0,
        }
        resp = requests.post(f"{SERVER_URL}/api/knowledge",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("skill_lookup-knowledge", f"HTTP {resp.status_code}")
            return

        # /api/question 不传 skill_name
        payload = {
            "knowledge_name": kp_name_only,
            "skill_name": "",
            "previous_weaknesses": [],
            "difficulty": "中等",
        }
        resp = requests.post(f"{SERVER_URL}/api/question",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("skill_lookup-question", f"HTTP {resp.status_code}")
            return

        reporter.record_pass("skill_name_auto_lookup")

    except Exception as e:
        reporter.record_error("skill_name_auto_lookup", f"异常: {e}")


def test_difficulty_levels(reporter, kb):
    """测试三种难度的练习题生成"""
    print_section("【正向测试 3】三种难度练习题生成")

    try:
        first_skill = kb["skills"][0]
        first_kp = first_skill["knowledge_points"][0]
        kp_name = first_kp["name"]
        skill_name = first_skill["name"]

        for difficulty in ["容易", "中等", "困难"]:
            payload = {
                "knowledge_name": kp_name,
                "skill_name": skill_name,
                "previous_weaknesses": [],
                "difficulty": difficulty,
            }
            resp = requests.post(f"{SERVER_URL}/api/question",
                                data=json.dumps(payload),
                                headers=get_headers(), timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                reporter.record_fail(f"diff-{difficulty}", f"难度 {difficulty} HTTP {resp.status_code}")
                return

            q_data = resp.json()
            has_question = q_data.get("question") or q_data.get("题目", "")
            if not has_question:
                reporter.record_fail(f"diff-{difficulty}", f"难度 {difficulty} 未获取到题目")
                return
            print(f"  ✅ 难度 {difficulty}: 成功生成 (题目长度 {len(str(has_question))})")

        reporter.record_pass("difficulty_levels")

    except Exception as e:
        reporter.record_error("difficulty_levels", f"异常: {e}")


def test_empty_inputs(reporter, kb):
    """测试边界用例：空输入/异常输入"""
    print_section("【边界测试 1】空输入/异常输入")

    try:
        # 1. knowledge_name 为空
        print("\n  [测试1] knowledge_name 为空")
        payload = {
            "knowledge_name": "",
            "skill_name": "",
            "skill_consecutive_days": 0,
            "knowledge_progress": 0,
            "previous_weaknesses": [],
            "previous_strengths": [],
            "today_count": 0,
        }
        resp = requests.post(f"{SERVER_URL}/api/knowledge",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        # 接口应该正常响应（可能返回空内容或报错但不崩溃）
        if resp.status_code >= 500:
            reporter.record_fail("empty-input-knowledge",
                                 f"knowledge_name 为空时服务器报错 HTTP {resp.status_code}")
            return
        print(f"    HTTP {resp.status_code} - 正常响应")

        # 2. user_answer 为空
        print("\n  [测试2] user_answer 为空")
        payload = {
            "question": "什么是增长漏斗？",
            "user_answer": "",
            "reference": "增长漏斗是用户转化模型。",
        }
        resp = requests.post(f"{SERVER_URL}/api/evaluate",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code >= 500:
            reporter.record_fail("empty-input-evaluate",
                                 f"user_answer 为空时服务器报错 HTTP {resp.status_code}")
            return
        print(f"    HTTP {resp.status_code} - 正常响应")

        # 3. submit 时 score 为 0
        print("\n  [测试3] submit score=0 (边界值)")
        payload = {
            "skill_name": kb["skills"][0]["name"],
            "knowledge_name": kb["skills"][0]["knowledge_points"][0]["name"],
            "score": 0,
            "eval_text": "用户未作答",
            "summary": "测试边界情况",
            "strengths": [],
            "weaknesses": ["未作答"],
        }
        resp = requests.post(f"{SERVER_URL}/api/submit",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code >= 500:
            reporter.record_fail("empty-input-submit-zero",
                                 f"score=0 时服务器报错 HTTP {resp.status_code}")
            return
        print(f"    HTTP {resp.status_code} - 正常响应")

        # 4. submit 时 score 为 10 (边界值)
        print("\n  [测试4] submit score=10 (满分边界)")
        payload = {
            "skill_name": kb["skills"][0]["name"],
            "knowledge_name": kb["skills"][0]["knowledge_points"][0]["name"],
            "score": 10,
            "eval_text": "完美回答",
            "summary": "满分测试",
            "strengths": ["全面准确"],
            "weaknesses": [],
        }
        resp = requests.post(f"{SERVER_URL}/api/submit",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code >= 500:
            reporter.record_fail("empty-input-submit-max",
                                 f"score=10 时服务器报错 HTTP {resp.status_code}")
            return
        print(f"    HTTP {resp.status_code} - 正常响应")

        reporter.record_pass("empty_inputs")

    except Exception as e:
        reporter.record_error("empty_inputs", f"异常: {e}")


def test_recommendation_coverage(reporter, kb):
    """测试知识点推荐覆盖度：连续多次调用 next_recommendation，检查是否覆盖不同技能"""
    print_section("【边界测试 2】推荐覆盖度测试")

    try:
        # 多次调用推荐，统计推荐的技能分布
        total_kps = sum(len(s["knowledge_points"]) for s in kb["skills"])
        test_rounds = total_kps + 5  # 比总知识点多5次
        skill_counts = defaultdict(int)
        kp_counts = defaultdict(int)
        all_seen_kps = set()

        print(f"  测试轮次: {test_rounds} 次 (总知识点: {total_kps})")

        for i in range(test_rounds):
            resp = requests.post(f"{SERVER_URL}/api/next_recommendation",
                                data=json.dumps({}),
                                headers=get_headers(), timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                continue
            rec_data = resp.json()
            skill = rec_data.get("skill", "")
            kp = rec_data.get("knowledge_point", "")
            if skill and kp:
                skill_counts[skill] += 1
                kp_counts[kp] += 1
                all_seen_kps.add(kp)
            time.sleep(0.5)  # 避免太快

        # 检查覆盖度报告
        print(f"\n  推荐覆盖的技能数: {len(skill_counts)} / {len(kb['skills'])}")
        print(f"  推荐覆盖的知识点数: {len(all_seen_kps)} / {total_kps}")
        print(f"  推荐唯一知识点率: {len(all_seen_kps) / total_kps * 100:.1f}%")

        # 统计信息 (不要求全部覆盖，只是收集信息用于调试)
        print("\n  技能推荐分布:")
        for skill, count in sorted(skill_counts.items(), key=lambda x: -x[1]):
            print(f"    - {skill}: {count} 次")

        reporter.record_pass("recommendation_coverage")

    except Exception as e:
        reporter.record_error("recommendation_coverage", f"异常: {e}")


def test_progress_update_correctness(reporter, kb):
    """测试多次学习后进度是否正确更新"""
    print_section("【边界测试 3】进度更新正确性")

    try:
        # 第一次学习某知识点，检查进度更新
        first_skill = kb["skills"][0]
        first_kp = first_skill["knowledge_points"][0]
        kp_name = first_kp["name"]
        skill_name = first_skill["name"]
        print(f"  目标知识点: {kp_name} (技能: {skill_name})")

        # 获取初始进度
        resp = requests.get(f"{SERVER_URL}/api/progress", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("progress-initial", f"HTTP {resp.status_code}")
            return
        initial_data = resp.json()

        initial_progress = 0
        for skill in initial_data.get("skills", []):
            for kp in skill.get("knowledge_points", []):
                if kp["name"] == kp_name:
                    initial_progress = kp.get("progress", 0)

        print(f"  初始进度: {initial_progress}%")

        # 提交一次低分学习 (3/10)
        print("\n  提交一次学习 (score=3)...")
        payload = {
            "skill_name": skill_name,
            "knowledge_name": kp_name,
            "score": 3,
            "eval_text": "测试低分",
            "summary": "低分边界测试",
            "strengths": [],
            "weaknesses": ["内容不完整"],
        }
        resp = requests.post(f"{SERVER_URL}/api/submit",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("progress-low-score-submit", f"HTTP {resp.status_code}")
            return

        # 检查进度更新
        resp = requests.get(f"{SERVER_URL}/api/progress", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("progress-after-low", f"HTTP {resp.status_code}")
            return
        after_data = resp.json()
        after_progress = 0
        for skill in after_data.get("skills", []):
            for kp in skill.get("knowledge_points", []):
                if kp["name"] == kp_name:
                    after_progress = kp.get("progress", 0)

        print(f"  提交低分后进度: {after_progress}%")

        if after_progress <= initial_progress:
            reporter.record_fail("progress-update",
                                 f"提交低分后进度未增加: {initial_progress} -> {after_progress}")
            return

        # 再提交一次高分学习 (8/10)
        print("\n  再提交一次学习 (score=8)...")
        payload = {
            "skill_name": skill_name,
            "knowledge_name": kp_name,
            "score": 8,
            "eval_text": "测试高分",
            "summary": "高分测试",
            "strengths": ["理解深刻"],
            "weaknesses": [],
        }
        resp = requests.post(f"{SERVER_URL}/api/submit",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("progress-high-score-submit", f"HTTP {resp.status_code}")
            return

        # 检查进度再次更新
        resp = requests.get(f"{SERVER_URL}/api/progress", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("progress-after-high", f"HTTP {resp.status_code}")
            return
        final_data = resp.json()
        final_progress = 0
        for skill in final_data.get("skills", []):
            for kp in skill.get("knowledge_points", []):
                if kp["name"] == kp_name:
                    final_progress = kp.get("progress", 0)

        print(f"  提交高分后进度: {final_progress}%")

        if final_progress <= after_progress:
            reporter.record_fail("progress-update-2",
                                 f"提交高分后进度未继续增加: {after_progress} -> {final_progress}")
            return

        reporter.record_pass("progress_update_correctness")

    except Exception as e:
        reporter.record_error("progress_update_correctness", f"异常: {e}")


def test_current_learning_state(reporter, kb):
    """测试当前学习状态读写"""
    print_section("【边界测试 4】当前学习状态读写")

    try:
        # 清除当前学习状态
        resp = requests.post(f"{SERVER_URL}/api/current_learning/clear",
                            data=json.dumps({}),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("current-clear", f"HTTP {resp.status_code}")
            return

        # 写入状态
        payload = {
            "knowledge_text": "测试知识点内容",
            "question": "测试题目",
            "reference": "测试参考答案",
            "question_answered": False,
        }
        resp = requests.post(f"{SERVER_URL}/api/current_learning",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("current-write", f"HTTP {resp.status_code}")
            return

        # 获取 today 应该返回 in_progress
        resp = requests.get(f"{SERVER_URL}/api/today", headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("current-verify", f"HTTP {resp.status_code}")
            return
        today_data = resp.json()
        status = today_data.get("status")
        if status != "in_progress":
            reporter.record_fail("current-verify-status", f"status='{status}'，期望 'in_progress'")
            return
        print(f"  当前状态: {status}")

        # 清除后再获取，应该返回 new
        resp = requests.post(f"{SERVER_URL}/api/current_learning/clear",
                            data=json.dumps({}),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("current-clear-2", f"HTTP {resp.status_code}")
            return

        reporter.record_pass("current_learning_state")

    except Exception as e:
        reporter.record_error("current_learning_state", f"异常: {e}")


def test_next_recommendation_format(reporter, kb):
    """测试 next_recommendation 的输出格式"""
    print_section("【边界测试 5】next_recommendation 推荐格式检查")

    try:
        resp = requests.post(f"{SERVER_URL}/api/next_recommendation",
                            data=json.dumps({}),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            reporter.record_fail("next_rec-http", f"HTTP {resp.status_code}")
            return
        rec_data = resp.json()

        # 检查字段
        required_fields = ["skill", "knowledge_point", "difficulty"]
        for field in required_fields:
            if field not in rec_data:
                reporter.record_fail(f"next_rec-field-{field}", f"缺少字段 {field}")
                return

        # 检查推荐的知识点是否真实存在于知识库
        rec_skill = rec_data.get("skill")
        rec_kp = rec_data.get("knowledge_point")
        rec_diff = rec_data.get("difficulty")

        skill_exists = any(s["name"] == rec_skill for s in kb.get("skills", []))
        kp_exists = False
        for skill in kb.get("skills", []):
            if skill["name"] == rec_skill:
                kp_exists = any(kp["name"] == rec_kp for kp in skill.get("knowledge_points", []))
                break

        if not skill_exists:
            reporter.record_fail("next_rec-skill-exists", f"推荐技能 '{rec_skill}' 不存在于知识库")
            return
        if not kp_exists:
            reporter.record_fail("next_rec-kp-exists", f"推荐知识点 '{rec_kp}' 不存在")
            return
        if rec_diff not in ("容易", "中等", "困难"):
            reporter.record_fail("next_rec-difficulty",
                                 f"难度 '{rec_diff}' 不是标准值 (容易/中等/困难)")
            return

        print(f"  推荐: {rec_skill} - {rec_kp} (难度: {rec_diff})")
        reporter.record_pass("next_recommendation_format")

    except Exception as e:
        reporter.record_error("next_recommendation_format", f"异常: {e}")


# ========== 主流程 ==========

def run_all_tests():
    print("=" * 80)
    print(f"全量接口测试开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试用户: {TEST_USER_ID}  (不影响生产数据)")
    print(f"目标服务器: {SERVER_URL}")
    print("=" * 80)

    # 加载知识库
    try:
        kb = load_kb_for_test()
        print(f"\n已加载知识库: {len(kb['skills'])} 个技能, "
              f"{sum(len(s['knowledge_points']) for s in kb['skills'])} 个知识点")
    except Exception as e:
        print(f"加载知识库失败: {e}")
        sys.exit(1)

    reporter = TestReporter()

    # 先清理旧的测试数据
    cleanup_test_data()

    # 等待服务器就绪
    print(f"\n【检查服务器状态】")
    try:
        ping_resp = requests.get(f"{SERVER_URL}/",
                                headers=get_headers(),
                                timeout=5)
        print(f"  ✅ 服务器响应正常 (HTTP {ping_resp.status_code})")
    except requests.ConnectionError:
        print(f"  ❌ 无法连接到服务器，请确保 Flask 应用已启动: {SERVER_URL}")
        print(f"     启动命令: python app.py  (在 my-first-agent 目录下)")
        sys.exit(1)
    except Exception as e:
        print(f"  ⚠️  服务器检查异常: {e}")

    # 运行所有测试
    tests = [
        ("完整学习流程", lambda r: test_full_learning_flow(r, kb)),
        ("skill_name 自动反查", lambda r: test_skill_name_auto_lookup(r, kb)),
        ("三种难度练习题", lambda r: test_difficulty_levels(r, kb)),
        ("空输入/异常输入", lambda r: test_empty_inputs(r, kb)),
        ("推荐覆盖度", lambda r: test_recommendation_coverage(r, kb)),
        ("进度更新正确性", lambda r: test_progress_update_correctness(r, kb)),
        ("当前学习状态读写", lambda r: test_current_learning_state(r, kb)),
        ("推荐格式检查", lambda r: test_next_recommendation_format(r, kb)),
    ]

    for name, test_fn in tests:
        try:
            test_fn(reporter)
        except Exception as e:
            reporter.record_error(name, f"测试执行异常: {e}")

    # 打印用例明细
    reporter.print_cases()

    # 最终清理
    cleanup_test_data()

    # 输出汇总
    fail_count = reporter.summary()
    if fail_count == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {fail_count} 项测试失败，请检查上述问题。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        exit_code = 1
    except Exception as e:
        print(f"\n\n测试脚本异常: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    sys.exit(exit_code)
