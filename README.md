# StudyTask 个人学习任务管理系统

StudyTask 是一个单用户学习任务管理 Web 应用，用于记录课程作业、实验和考试准备。项目为《软件工程》实验一交付物，按附录 A 的 SRS 实现，技术栈为 **Python 3.10+ / Flask / SQLite**。

**线上演示：<https://ZYQ.pythonanywhere.com>**（PythonAnywhere 免费实例，首次访问可能稍慢）

## 1. 功能范围

| 编号 | 功能 | 实现说明 |
| --- | --- | --- |
| P1-F01 | 新建任务 | 名称、课程、描述、截止日期、优先级；服务端必填与长度校验 |
| P1-F02 | 查看 / 编辑 / 删除 | 列表、详情、编辑表单；删除使用独立二次确认页 |
| P1-F03 | 任务状态 | 待完成 / 进行中 / 已完成，变更立即持久化 |
| P1-F04 | 组合筛选 | 按课程、状态、优先级筛选，可任意组合 |
| P1-F05 | 逾期提示 | 未完成且早于今天标记“已逾期”；今天起 3 天内标记“即将到期” |
| P1-F06 | 基础统计 | 任务总数、已完成数、完成率（无任务时显示 0%） |
| P1-F07 | 本地持久化 | SQLite 文件存储，重启服务后数据保留 |

不在产品功能范围内：用户注册、多用户权限、任务共享、邮件/短信提醒、第三方日历、移动端 App；线上演示环境见第 8 节。

## 2. 技术栈

- Python 3.10+（本地开发 Python 3.13.2，线上 Python 3.10.12）
- Flask 3.1.2
- SQLite（Python 标准库 `sqlite3`，无额外驱动）
- Jinja2 模板 + 原生 CSS
- pytest 8.4.2

## 3. 目录结构

```text
StudyTask/
├── app.py                  # 应用工厂与路由
├── db.py                   # SQLite 连接、建表
├── task_service.py         # 字段校验、逾期判断、筛选、统计
├── templates/              # 列表、表单、详情、删除确认、404
├── static/style.css        # 页面样式
├── tests/
│   ├── conftest.py         # 测试夹具（临时数据库）
│   └── test_acceptance.py  # 25 条自动化测试
├── docs/
│   ├── 需求验收表.md
│   ├── 实验一报告.docx
│   ├── 实验一演示.pptx
│   └── evidence/           # 运行截图
├── README.md
├── AI_DEV_LOG.md
├── requirements.txt
└── .gitignore
```

## 4. 快速开始

在项目根目录执行（Windows PowerShell）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

浏览器访问 <http://127.0.0.1:5000>。

- 首次启动会自动创建 `instance/studytask.db` 并建表，无需手动初始化。
- 如需清空数据，停止服务后删除 `instance/studytask.db`，再次启动即可重建。
- 生产/局域网访问可执行：`python -c "from app import app; app.run(host='0.0.0.0', port=5000)"`。

## 5. 运行测试

```powershell
python -m pytest -v
```

预期结果：`25 passed`。测试使用临时 SQLite 文件，不会影响本地演示数据。

| 测试类 | 覆盖内容 |
| --- | --- |
| `TestCreate` | T1、T2、必填项、非法日期、非法枚举、超长字段 |
| `TestReadUpdateDelete` | T3、T4、T9、404、超大任务 ID |
| `TestFilter` | T5（单项与组合筛选） |
| `TestDeadline` | T6、T7、已完成任务不提示、今天截止、4 天后不提示 |
| `TestStats` | T8、零任务、非整数完成率 |
| `TestPersistence` | T10（重建应用实例后读取同一数据库） |

## 6. 关键业务规则

1. **逾期**：`status != 已完成` 且 `due_date < 今天`，显示“已逾期 N 天”。
2. **即将到期**：`status != 已完成` 且 `0 <= 截止日期 - 今天 <= 3` 天，显示“即将到期”。
3. **已完成任务**：不显示逾期或即将到期提示（SRS FR-07）。
4. **完成率**：`已完成数 / 总数 × 100%`；没有任务时为 `0%`，结果保留 1 位小数（整数不显示 `.0`）。
5. **输入校验**：名称 1—100 字、课程 1—60 字、描述 ≤1000 字；日期必须是有效的 `YYYY-MM-DD`；优先级与状态必须属于枚举值。校验失败返回 HTTP 400，并保留用户已填内容。
6. **删除**：`GET /tasks/<id>/delete` 只展示确认页，`POST` 才真正删除，取消不会改变数据。

## 7. 文档与证据

- [需求验收表](docs/需求验收表.md)：T1—T10 实际结果、证据与补充校验用例。
- [AI_DEV_LOG.md](AI_DEV_LOG.md)：关键提示词、AI 产出、问题与人工判断。
- [实验一报告.docx](docs/实验一报告.docx)：不超过 4 页的实验报告。
- [实验一演示.pptx](docs/实验一演示.pptx)：演示用 PPT。
- [运行截图](docs/evidence/)：任务列表、筛选、详情、删除确认、表单校验。
- [200 条任务性能验证](docs/evidence/performance_200.txt)：列表平均响应约 19 ms。
- [测试完整输出](docs/evidence/pytest_output.txt)：25 passed 的实际记录。
- [线上端到端验收](docs/evidence/deploy_verify.txt)：创建、状态流转、删除、删除后 404。
- [线上首页截图](docs/evidence/06_online_home.png)：PythonAnywhere 实例首页。

## 8. 线上部署（PythonAnywhere）

线上地址：<https://ZYQ.pythonanywhere.com>

线上已有 6 条与报告截图一致的演示数据（含逾期、今天截止、进行中与已完成），可直接在页面上编辑或删除。

部署步骤：

1. 注册 PythonAnywhere Beginner 免费账号，打开 **Consoles → Bash**。
2. 克隆仓库并安装依赖：

```bash
git clone https://github.com/yq-wcq/24-2-_242806010229_StudyTask.git
cd 24-2-_242806010229_StudyTask
mkvirtualenv studytask --python=/usr/bin/python3.10
pip install -r requirements.txt
```

3. 打开 **Web → Add a new web app → Manual configuration → Python 3.10**。
4. Source code 填 `/home/ZYQ/24-2-_242806010229_StudyTask`，Virtualenv 填 `/home/ZYQ/.virtualenvs/studytask`。
5. 编辑 WSGI 配置文件：

```python
import os
import sys
import time

os.environ["TZ"] = "Asia/Shanghai"
time.tzset()

path = "/home/ZYQ/24-2-_242806010229_StudyTask"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault("SECRET_KEY", "studytask-zyq-2026")

from app import app as application
```

6. 回到 Web 页面点 **Reload**，访问线上地址。
7. 线上数据库位于 `/home/ZYQ/24-2-_242806010229_StudyTask/instance/studytask.db`；免费实例需每 30 天登录续期一次。

## 9. 已知限制

- 按 SRS A.5，系统不包含登录、多用户权限、任务共享和提醒推送。
- 线上使用 PythonAnywhere 免费实例，访问速度与可用性受平台限制，每 30 天需登录续期。
- SQLite 单文件适合单用户使用；若多人并发写入需更换数据库。
- 本地使用 Flask 开发服务器，线上由 PythonAnywhere WSGI 托管。
- 默认 `SECRET_KEY` 有开发默认值；线上已通过 WSGI 环境变量覆盖。
- 截止日期使用浏览器原生日期控件，显示格式随浏览器语言设置变化，但提交值固定为 `YYYY-MM-DD`。
