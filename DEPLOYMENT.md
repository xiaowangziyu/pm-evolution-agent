# PythonAnywhere 部署指南

本文档介绍如何将产品经理进化论 Agent 部署到 PythonAnywhere。

---

## 前置准备

- ✅ 已有 GitHub 仓库（xiaowangziyu/pm-evolution-agent）
- ✅ 已有 PythonAnywhere 账号
- ✅ 已有智谱 AI API Key

---

## 步骤 1：推送最新代码到 GitHub

（我们刚才已经做了！）

```bash
# 先提交本地修改
git add .
git commit -m "完善部署准备：日志、环境配置"
git push origin master
```

---

## 步骤 2：PythonAnywhere 创建 Web 应用

### 2.1 登录 PythonAnywhere

访问 https://www.pythonanywhere.com/ 并登录

### 2.2 创建新的 Web 应用

1. 点击顶部菜单 "Web" → "Add a new web app"
2. 选择 "Flask" → 选择 Python 版本（建议选 3.10 或 3.11）
3. 选择 "Manual configuration"（手动配置）
4. 应用名称可以自己取（如 `pm-evolution-agent`）

---

## 步骤 3：从 GitHub 拉取代码

### 3.1 打开 PythonAnywhere 的 "Bash" 控制台

1. 点击顶部菜单 "Consoles" → "Bash" 打开新终端
2. 克隆你的 GitHub 仓库：

```bash
cd ~
git clone https://github.com/xiaowangziyu/pm-evolution-agent.git
cd pm-evolution-agent
```

---

## 步骤 4：配置环境和依赖

### 4.1 创建虚拟环境

```bash
mkvirtualenv --python=/usr/bin/python3.10 pm-env  # 选你刚才的 Python 版本
workon pm-env  # 激活虚拟环境
```

### 4.2 安装依赖

```bash
pip install -r requirements.txt
```

---

## 步骤 5：配置 .env 文件

在 pm-evolution-agent 目录下创建 .env 文件：

```bash
nano .env
```

填入以下内容（注意替换你的真实 API Key）：

```
ZHIPU_API_KEY=你的智谱API_KEY
API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
MODEL=glm-4-flash
MAX_CONSECUTIVE_DAYS=3
FLASK_ENV=production
FLASK_DEBUG=0
```

按 Ctrl+O 保存，回车确认，然后 Ctrl+X 退出。

---

## 步骤 6：配置 WSGI 文件

回到 "Web" 页面，点击 "WSGI configuration file" 链接（通常是 `/var/www/你的用户名_pythonanywhere_com_wsgi.py`）

修改 WSGI 文件内容如下：

```python
import sys
import os

# 添加项目路径
path = '/home/你的用户名/pm-evolution-agent'
if path not in sys.path:
    sys.path.append(path)

# 从 app.py 导入 app
from app import app as application
```

**重要**：把 `你的用户名` 替换成你 PythonAnywhere 的真实用户名！

保存文件。

---

## 步骤 7：配置 Web 应用

在 "Web" 页面：

1. **Code** 部分：
   - Source code: `/home/你的用户名/pm-evolution-agent`
   - Working directory: `/home/你的用户名/pm-evolution-agent`
   - Virtualenv: `/home/你的用户名/.virtualenvs/pm-env`

2. **Static files** 部分（添加）：
   - URL: `/static/`
   - Directory: `/home/你的用户名/pm-evolution-agent/static`

---

## 步骤 8：启动应用

1. 在 "Web" 页面顶部，点击 **Reload** 按钮
2. 访问你的应用 URL，比如：`https://你的用户名.pythonanywhere.com/`

---

## 常见问题

### Q1：应用显示 500 错误怎么办？

查看错误日志：在 "Web" 页面 → "Log files" → "Error log"

### Q2：API 调用超时？

免费版可能有网络限制，如果使用代理，在 .env 里配置代理：

```
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port
```

### Q3：数据文件在哪里？

用户数据文件会生成在项目根目录，以 `kb_user_xxx.json` 等命名。

---

## 更新部署（后续代码更新）

当你在本地更新了代码并推送到 GitHub 后：

1. 在 PythonAnywhere 的 Bash 控制台：
   ```bash
   cd ~/pm-evolution-agent
   git pull origin master
   ```
2. 在 "Web" 页面点击 **Reload** 即可

---

祝部署顺利！🚀
