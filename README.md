# StudyTask 个人学习任务管理系统

StudyTask 是一个单用户学习任务管理 Web 应用，用于记录课程作业、实验和考试准备。技术栈为 Python 3.10+、Flask、SQLite。

线上地址：<https://ZYQ.pythonanywhere.com>

## 功能

- 任务创建、查看、编辑、删除
- 状态流转：待完成、进行中、已完成
- 按课程、状态、优先级组合筛选
- 未完成任务逾期提醒、未来 3 天即将到期提醒
- 首页统计任务总数、已完成数与完成率
- SQLite 持久化，重启应用后数据保留
- 表单校验与中文错误提示

不包含账号注册、多用户权限、任务共享、邮件/短信提醒、移动端 App。

## 本地运行

1. 安装 Python 3.10 或更高版本。
2. 获取代码并进入项目目录：

```bash
git clone https://github.com/yq-wcq/24-2-_242806010229_StudyTask.git
cd 24-2-_242806010229_StudyTask
```

3. 创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. 安装依赖：

```bash
pip install -r requirements.txt
```

5. 启动：

```bash
python app.py
```

6. 浏览器访问 <http://127.0.0.1:5000>。

首次启动会自动创建 `instance/studytask.db`；如需清空数据，停止服务后删除该文件再启动。

## 项目结构

```text
app.py              Flask 路由与页面入口
db.py               SQLite 连接与建表
task_service.py     校验、筛选、逾期判断与统计
templates/          Jinja2 页面模板
static/style.css    页面样式
requirements.txt    Python 依赖
README.md           运行说明
```

## 线上部署

线上使用 PythonAnywhere 免费实例，Python 3.10.12，WSGI 入口为 `app:application`，数据库位于项目目录下的 `instance/studytask.db`。

免费实例每 30 天需要在 PythonAnywhere 的 Web 页面点击一次 **Run until 1 month from today** 续期。
