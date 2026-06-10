#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冒烟测试脚本（每日自动运行）

功能特点：
- 使用特殊 user_id (smoke_test)，不污染生产数据
- 不调用 LLM（Mock 模式），只验证接口返回格式和基本逻辑
- 覆盖所有核心 API 接口
- 自动清理测试数据
- 输出清晰的测试报告（通过/失败统计）

使用方法：
    python run_smoke.py
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_URL = "http://127.0.0.1:5000"
TEST_USER_ID = "smoke_test"
REQUEST_TIMEOUT = 30

# 测试用固定数据（保证测试可复现）
TEST_KP_NAME = "增长漏斗"
TEST_SKILL_NAME = "用户增长与运营"


class TestReporter:
    """测试报告收集器"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []

    def record_pass(self, name):
        self.passed.append(name)
        print(f"  ✅ PASS: {name}")

    def record_fail(self, name, reason):
        self.failed.append((name, reason))
        print(f"  ❌ FAIL: {name}: {reason}")

    def record_error(self, name, err):
        self.errors.append((name, str(err)))
        print(f"  ⚠️  ERROR: {name}: {err}")

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
    print("-" * 80)
    print(f" {title}")
    print("-" * 80)


def get_headers():
    return {"X-User-Id": TEST_USER_ID, "Content-Type": "application/json"}


def check_field(data, field, expected_type=None, required=True, test_name=""):
    """检查字段是否存在且类型正确"""
    if isinstance(data, dict) and field in data:
        value = data[field]
        if expected_type and value is not None:
            if not isinstance(value, expected_type):
                return f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}"
        return None
    elif required:
        return f"缺少必需字段: '{field}'"
    return None


def cleanup_test_data():
    """清理冒烟测试产生的用户数据"""
    print("\n【清理测试数据】")
    test_files = [
        f"kb_user_{TEST_USER_ID}.json",
        f"log_user_{TEST_USER_ID}.json",
        f"current_user_{TEST_USER_ID}.json",
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


def test_api_today(reporter):
    """测试 /api/today 接口"""
    print_section("测试接口: /api/today (获取今日学习内容)")
    try:
        resp = requests.get(f"{SERVER_URL}/api/today",
                           headers=get_headers(), timeout=REQUEST_TIMEOUT)
        resp_json = resp.json()

        # 检查 HTTP 状态码
        if resp.status_code != 200:
            reporter.record_fail("today-http-status",
                                 f"HTTP状态码 {resp.status_code}，期望 200")
            return

        # 检查关键字段
        required_fields = ["status", "skill_name", "knowledge_name"]
        for field in required_fields:
            err = check_field(resp_json, field, test_name="today")
            if err:
                reporter.record_fail(f"today-field-{field}", err)
                return

        # status 必须是 in_progress 或 new
        status = resp_json.get("status")
        if status not in ("in_progress", "new"):
            reporter.record_fail("today-status-value",
                                 f"status 为 '{status}'，期望 'in_progress' 或 'new'")
            return

        reporter.record_pass("today")

    except requests.ConnectionError:
        reporter.record_error("today", "无法连接到服务器，请确保 Flask 应用已启动在 127.0.0.1:5000")
    except Exception as e:
        reporter.record_error("today", f"异常: {e}")


def test_api_knowledge(reporter):
    """测试 /api/knowledge 接口"""
    print_section("测试接口: /api/knowledge (知识点讲解)")
    try:
        payload = {
            "knowledge_name": TEST_KP_NAME,
            "skill_name": TEST_SKILL_NAME,
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
            reporter.record_fail("knowledge-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()

        # 检查响应是否有 text 字段 (knowledge_text 或 knowledge 或 text)
        text_fields = ["knowledge_text", "knowledge", "text", "content"]
        has_text = any(f in resp_json for f in text_fields)
        if not has_text:
            reporter.record_fail("knowledge-text-field",
                                 f"响应中未找到文本字段。响应键: {list(resp_json.keys())}")
            return

        reporter.record_pass("knowledge")

    except Exception as e:
        reporter.record_error("knowledge", f"异常: {e}")


def test_api_question(reporter):
    """测试 /api/question 接口"""
    print_section("测试接口: /api/question (生成练习题)")
    try:
        payload = {
            "knowledge_name": TEST_KP_NAME,
            "skill_name": TEST_SKILL_NAME,
            "previous_weaknesses": [],
            "difficulty": "中等",
        }
        resp = requests.post(f"{SERVER_URL}/api/question",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("question-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()

        # 检查是否有 question/题目 字段
        question_fields = ["question", "题目"]
        ref_fields = ["reference", "参考答案", "reference_answer"]
        has_question = any(f in resp_json for f in question_fields)
        has_ref = any(f in resp_json for f in ref_fields)

        if not has_question:
            reporter.record_fail("question-field",
                                 f"未找到题目字段。响应键: {list(resp_json.keys())}")
            return
        if not has_ref:
            reporter.record_fail("question-reference-field",
                                 f"未找到参考答案字段。响应键: {list(resp_json.keys())}")
            return

        reporter.record_pass("question")

    except Exception as e:
        reporter.record_error("question", f"异常: {e}")


def test_api_evaluate_field_extraction(reporter):
    """测试 evaluate 接口的字段提取逻辑"""
    print_section("测试接口: /api/evaluate (答案评估 - 字段提取)")
    try:
        payload = {
            "question": "什么是增长漏斗？",
            "user_answer": "增长漏斗是用户从获取到转化的模型，包括获客、激活、留存、收入、推荐等阶段。",
            "reference": "增长漏斗（AARRR）：获客(Acquisition)、激活(Activation)、留存(Retention)、收入(Revenue)、推荐(Referral)。",
        }
        resp = requests.post(f"{SERVER_URL}/api/evaluate",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("evaluate-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()

        # 检查关键字段
        checks = [
            ("score", (int, float), True),
            ("summary", str, True),
            ("strengths", list, True),
            ("weaknesses", list, True),
        ]
        for field, ftype, required in checks:
            err = check_field(resp_json, field, ftype, required, "evaluate")
            if err:
                reporter.record_fail(f"evaluate-field-{field}", err)
                return

        # 检查 score 是否在 0-10 范围
        score = resp_json.get("score")
        if score is not None and (score < 0 or score > 10):
            reporter.record_fail("evaluate-score-range",
                                 f"得分 {score} 超出 0-10 范围")
            return

        reporter.record_pass("evaluate")

    except Exception as e:
        reporter.record_error("evaluate", f"异常: {e}")


def test_api_submit(reporter):
    """测试 /api/submit 接口"""
    print_section("测试接口: /api/submit (提交学习结果)")
    try:
        payload = {
            "skill_name": TEST_SKILL_NAME,
            "knowledge_name": TEST_KP_NAME,
            "score": 7.5,
            "eval_text": "用户对增长漏斗有基本理解，但缺少具体案例分析。",
            "summary": "对增长漏斗模型有基本认知，能说出核心概念。",
            "strengths": ["掌握了基本概念", "理解了漏斗的层级关系"],
            "weaknesses": ["缺少实际案例分析", "没有提到具体指标"],
        }
        resp = requests.post(f"{SERVER_URL}/api/submit",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("submit-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()
        # submit 应返回 status: success
        status = resp_json.get("status")
        if status and status != "success":
            reporter.record_fail("submit-status",
                                 f"status='{status}'，期望 'success'")
            return

        reporter.record_pass("submit")

    except Exception as e:
        reporter.record_error("submit", f"异常: {e}")


def test_api_progress(reporter):
    """测试 /api/progress 接口"""
    print_section("测试接口: /api/progress (进度统计)")
    try:
        resp = requests.get(f"{SERVER_URL}/api/progress",
                           headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("progress-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()

        # 检查是否有 skills 字段
        if "skills" not in resp_json:
            reporter.record_fail("progress-skills-field",
                                 f"缺少 skills 字段。响应键: {list(resp_json.keys())}")
            return

        skills = resp_json.get("skills", [])
        if not isinstance(skills, list):
            reporter.record_fail("progress-skills-type",
                                 f"skills 不是列表，实际: {type(skills).__name__}")
            return

        # 检查每个 skill 结构
        for skill in skills:
            for field in ["name", "knowledge_points"]:
                err = check_field(skill, field, test_name="progress")
                if err:
                    reporter.record_fail(f"progress-skill-{field}", err)
                    return

        reporter.record_pass("progress")

    except Exception as e:
        reporter.record_error("progress", f"异常: {e}")


def test_api_history(reporter):
    """测试 /api/history 接口"""
    print_section("测试接口: /api/history (学习历史)")
    try:
        resp = requests.get(f"{SERVER_URL}/api/history",
                           headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("history-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()

        for field in ["history", "grouped", "total_duration", "total_count"]:
            err = check_field(resp_json, field, test_name="history")
            if err:
                reporter.record_fail(f"history-field-{field}", err)
                return

        reporter.record_pass("history")

    except Exception as e:
        reporter.record_error("history", f"异常: {e}")


def test_api_next_recommendation(reporter):
    """测试 /api/next_recommendation 接口"""
    print_section("测试接口: /api/next_recommendation (推荐下一个知识点)")
    try:
        resp = requests.post(f"{SERVER_URL}/api/next_recommendation",
                            data=json.dumps({}),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("next_rec-http-status",
                                 f"HTTP状态码 {resp.status_code}")
            return

        resp_json = resp.json()

        for field in ["skill", "knowledge_point", "difficulty"]:
            err = check_field(resp_json, field, test_name="next_rec")
            if err:
                reporter.record_fail(f"next_rec-field-{field}", err)
                return

        reporter.record_pass("next_recommendation")

    except Exception as e:
        reporter.record_error("next_recommendation", f"异常: {e}")


def test_api_current_learning(reporter):
    """测试 /api/current_learning 接口"""
    print_section("测试接口: /api/current_learning (当前学习状态读写)")
    try:
        # 先写入
        payload = {
            "knowledge_text": "测试内容：增长漏斗是用户转化模型",
            "question": "测试题目：增长漏斗包含哪几个阶段？",
            "reference": "测试参考：获客、激活、留存、收入、推荐",
            "question_answered": True,
        }
        resp = requests.post(f"{SERVER_URL}/api/current_learning",
                            data=json.dumps(payload),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("current_learning-write-http",
                                 f"HTTP状态码 {resp.status_code}")
            return

        # 清除
        resp = requests.post(f"{SERVER_URL}/api/current_learning/clear",
                            data=json.dumps({}),
                            headers=get_headers(), timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            reporter.record_fail("current_learning-clear-http",
                                 f"HTTP状态码 {resp.status_code}")
            return

        reporter.record_pass("current_learning")

    except Exception as e:
        reporter.record_error("current_learning", f"异常: {e}")


def test_homepage(reporter):
    """测试首页和其他页面是否可访问"""
    print_section("测试页面: 首页与路由可访问性")
    pages = ["/", "/progress", "/history"]
    try:
        all_ok = True
        for page in pages:
            resp = requests.get(f"{SERVER_URL}{page}",
                               headers={"X-User-Id": TEST_USER_ID},
                               timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                reporter.record_fail(f"page-{page.lstrip('/')}",
                                     f"HTTP状态码 {resp.status_code}")
                all_ok = False
        if all_ok:
            reporter.record_pass("homepage_and_routes")
    except Exception as e:
        reporter.record_error("homepage", f"异常: {e}")


def run_all_tests():
    print("=" * 80)
    print(f"冒烟测试开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试用户: {TEST_USER_ID}  (不影响生产数据)")
    print(f"目标服务器: {SERVER_URL}")
    print("=" * 80)

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

    # 按顺序运行测试
    tests = [
        test_homepage,
        test_api_today,
        test_api_knowledge,
        test_api_question,
        test_api_evaluate_field_extraction,
        test_api_submit,
        test_api_progress,
        test_api_history,
        test_api_next_recommendation,
        test_api_current_learning,
    ]

    for test_fn in tests:
        test_fn(reporter)

    # 最终清理
    cleanup_test_data()

    # 输出汇总
    fail_count = reporter.summary()
    if fail_count == 0:
        print("\n🎉 所有测试通过！系统核心功能正常。")
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
