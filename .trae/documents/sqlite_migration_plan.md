# SQLite 数据迁移实现计划

## 一、需求分析

### 1.1 用户需求概述

| 需求项 | 描述 | 优先级 |
|--------|------|--------|
| 数据迁移 | 将现有 JSON 文件数据迁移到 SQLite 数据库 | P0 |
| 保留知识库 | `knowledge_base.json` 继续使用，不迁移到数据库 | P1 |
| 延迟用户隔离 | 用户 ID 机制暂时保持现状（使用 `X-User-Id` Header） | P2 |
| 数据库操作封装 | 创建独立的数据库操作模块 `db.py` | P1 |

### 1.2 待迁移数据类型

根据 [app.py](file:///D:/pycharm/python项目/my-first-agent/app.py) 分析，需要迁移以下数据：

| 数据类型 | 当前存储方式 | 迁移目标表 |
|----------|------------|-----------|
| 学习记录 | `log_user_{user_id}.json` | `learning_records` |
| 用户进度 | `kb_user_{user_id}.json` | `user_progress` |
| 当前学习状态 | `current_user_{user_id}.json` | `current_learning` |

---

## 二、数据库表结构设计

### 2.1 学习记录表 (`learning_records`)

```sql
CREATE TABLE IF NOT EXISTS learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,           -- 对应当前的 user_id
    date TEXT NOT NULL,                  -- 学习日期 "YYYY-MM-DD"
    skill TEXT,                          -- 技能名称
    knowledge TEXT,                      -- 知识点名称
    score REAL,                          -- 得分 0-10
    summary TEXT,                        -- AI 评估总结
    strengths TEXT,                      -- 达标之处（JSON 数组）
    weaknesses TEXT,                     -- 不足之处（JSON 数组）
    diary TEXT,                          -- 学习日记
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_records_session ON learning_records(session_id);
CREATE INDEX idx_records_date ON learning_records(date);
```

### 2.2 用户进度表 (`user_progress`)

```sql
CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,           -- 对应当前的 user_id
    skill_name TEXT NOT NULL,            -- 技能名称
    knowledge_name TEXT NOT NULL,        -- 知识点名称
    progress REAL DEFAULT 0,             -- 进度值 0-100
    consecutive_days INTEGER DEFAULT 0,  -- 连续学习天数（技能级）
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, skill_name, knowledge_name)
);

CREATE INDEX idx_progress_session ON user_progress(session_id);
```

### 2.3 当前学习状态表 (`current_learning`)

```sql
CREATE TABLE IF NOT EXISTS current_learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,     -- 对应当前的 user_id
    skill_name TEXT,                     -- 当前技能名称
    knowledge_name TEXT,                 -- 当前知识点名称
    knowledge_text TEXT,                 -- 知识点内容
    question TEXT,                       -- 练习题题目
    reference TEXT,                      -- 参考答案
    question_answered INTEGER DEFAULT 0, -- 是否已答题（0/1）
    skill_consecutive_days INTEGER DEFAULT 0,
    knowledge_progress REAL DEFAULT 0,
    today_count INTEGER DEFAULT 0,
    previous_weaknesses TEXT,            -- 历史薄弱点（JSON 数组）
    previous_strengths TEXT,             -- 历史优势（JSON 数组）
    is_iterative INTEGER DEFAULT 0,      -- 是否迭代学习（0/1）
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_current_session ON current_learning(session_id);
```

---

## 三、文件修改清单

### 3.1 新建文件

| 文件路径 | 功能说明 |
|----------|----------|
| `db.py` | 数据库操作封装模块 |
| `migrate_to_sqlite.py` | 数据迁移脚本 |
| `pm_evolution.db` | SQLite 数据库文件（自动生成） |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `app.py` | 将 JSON 文件读写替换为 SQLite 操作 |

### 3.3 删除文件（可选，迁移完成后）

| 文件路径模式 | 说明 |
|--------------|------|
| `log_user_*.json` | 旧学习记录文件 |
| `kb_user_*.json` | 旧进度文件 |
| `current_user_*.json` | 旧当前学习状态文件 |

---

## 四、实施步骤

### 步骤 1：创建数据库操作模块 `db.py`

```python
# 功能：封装所有 SQLite 操作
# 包含：get_db(), init_db(), 各表的 CRUD 操作
```

### 步骤 2：创建迁移脚本 `migrate_to_sqlite.py`

```python
# 功能：读取 JSON 文件并迁移到 SQLite
# 步骤：
# 1. 初始化数据库表
# 2. 遍历并迁移 log_user_*.json
# 3. 遍历并迁移 kb_user_*.json  
# 4. 遍历并迁移 current_user_*.json
```

### 步骤 3：修改 `app.py`

替换以下函数：
- `load_log()` → 使用 `db.get_user_records()`
- `save_log()` → 使用 `db.add_learning_record()`
- `load_user_knowledge_base()` → 使用 `db.get_user_progress()`
- `save_user_knowledge_base()` → 使用 `db.update_user_progress()`
- `load_current_learning()` → 使用 `db.get_current_learning()`
- `save_current_learning()` → 使用 `db.update_current_learning()`
- `clear_current_learning()` → 使用 `db.clear_current_learning()`

### 步骤 4：在 PythonAnywhere 执行迁移

```bash
# 1. 上传 db.py 和 migrate_to_sqlite.py
# 2. 运行迁移脚本
python migrate_to_sqlite.py
# 3. 验证数据
python -c "import db; print(db.get_db().execute('SELECT COUNT(*) FROM learning_records').fetchone())"
# 4. 修改 wsgi.py 确保正确加载
# 5. Reload web app
```

### 步骤 5：功能测试

| 测试项 | 验证方法 |
|--------|----------|
| 获取今日学习 | 访问 `/api/today` |
| 知识点讲解 | 调用 `/api/knowledge` |
| 练习题生成 | 调用 `/api/question` |
| AI 评估 | 调用 `/api/evaluate` |
| 提交学习 | 调用 `/api/submit` |
| 进度查询 | 访问 `/api/progress` |
| 历史查询 | 访问 `/api/history` |

---

## 五、依赖与环境

### 5.1 依赖检查

```bash
# SQLite 是 Python 标准库，无需额外安装
python -c "import sqlite3; print('SQLite available')"
```

### 5.2 权限要求

| 操作 | 权限要求 |
|------|----------|
| 创建数据库文件 | 项目目录写入权限 |
| 修改 app.py | 文件修改权限 |
| 重启 Web 应用 | PythonAnywhere 管理员权限 |

---

## 六、风险处理

### 6.1 风险清单

| 风险 | 描述 | 应对措施 |
|------|------|----------|
| 数据丢失 | 迁移过程中数据损坏 | 迁移前备份 JSON 文件 |
| 迁移失败 | JSON 格式异常导致迁移中断 | 迁移脚本添加错误处理，跳过损坏记录 |
| 服务中断 | 修改 app.py 引入 bug | 先在本地测试，再部署到线上 |
| 性能问题 | SQLite 查询性能不如预期 | 添加索引优化 |

### 6.2 回滚方案

```bash
# 如果迁移失败，恢复原始文件
git checkout app.py
# 删除数据库文件
rm pm_evolution.db
```

---

## 七、时间预估

| 阶段 | 预计时间 |
|------|----------|
| 创建 db.py | 1 小时 |
| 创建迁移脚本 | 1 小时 |
| 修改 app.py | 2 小时 |
| 本地测试 | 1 小时 |
| 线上迁移 | 30 分钟 |
| **总计** | **~5.5 小时** |

---

## 八、交付物

| 交付物 | 说明 |
|--------|------|
| `db.py` | 数据库操作模块 |
| `migrate_to_sqlite.py` | 数据迁移脚本 |
| `pm_evolution.db` | SQLite 数据库文件 |
| `app.py` | 修改后的主应用文件 |

---

## 九、下一步行动

等待用户确认此计划，然后开始实施。

---

**计划版本**: v1.0  
**创建日期**: 2026-06-10  
**适用项目**: [my-first-agent](file:///D:/pycharm/python项目/my-first-agent/)
