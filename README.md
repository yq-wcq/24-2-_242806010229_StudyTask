# StudyTask 个人学习任务管理系统

StudyTask 是一个单用户学习任务管理 Web 应用，用于记录课程作业、实验和考试准备。项目为《软件工程》实验一交付物，按附录 A 的 SRS 实现，技术栈为 **Python 3.11+ / Flask / SQLite**。

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

不在范围内：用户注册、多用户权限、任务共享、邮件/短信提醒、第三方日历、移动端 App、云部署。

## 2. 技术栈

- Python 3.11+（开发环境 Python 3.13.2）
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

## 8. 已知限制

- 按 SRS A.5，系统不包含登录、多用户权限、任务共享、提醒推送与云部署。
- 使用 Flask 开发服务器，仅面向本地单用户使用。
- 默认 `SECRET_KEY` 有开发默认值；若未来扩展为对外服务，须通过环境变量覆盖。
- 截止日期使用浏览器原生日期控件，显示格式随浏览器语言设置变化，但提交值固定为 `YYYY-MM-DD`。
