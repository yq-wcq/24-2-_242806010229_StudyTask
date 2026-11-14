"""任务领域逻辑：字段校验、逾期判断、筛选与统计。"""

from datetime import date, datetime, timedelta

from db import get_db

TITLE_MAX = 100
COURSE_MAX = 60
DESCRIPTION_MAX = 1000

PRIORITIES = ("高", "中", "低")
STATUSES = ("待完成", "进行中", "已完成")

# 顺序决定下拉框与筛选器的展示顺序
STATUS_FLOW = {"待完成": "进行中", "进行中": "已完成", "已完成": "待完成"}
STATUS_NEXT_LABEL = {"待完成": "开始任务", "进行中": "标记完成", "已完成": "重新打开"}


def today() -> date:
    """便于测试替换的“今天”。"""
    return date.today()


def parse_date(value: str):
    """严格解析 YYYY-MM-DD，非法日期返回 None。"""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def validate_task(form, *, partial: bool = False):
    """校验并归一化表单数据。

    partial=True 时只校验提交的字段（用于局部更新，当前未使用）。
    返回 (data, errors)：errors 为 {字段: 错误信息}。
    """
    data = {
        "title": (form.get("title") or "").strip(),
        "course": (form.get("course") or "").strip(),
        "description": (form.get("description") or "").strip(),
        "due_date": (form.get("due_date") or "").strip(),
        "priority": (form.get("priority") or "中").strip(),
        "status": (form.get("status") or "待完成").strip(),
    }
    errors = {}

    if not data["title"]:
        errors["title"] = "任务名称不能为空"
    elif len(data["title"]) > TITLE_MAX:
        errors["title"] = f"任务名称不能超过 {TITLE_MAX} 个字"

    if not data["course"]:
        errors["course"] = "所属课程不能为空"
    elif len(data["course"]) > COURSE_MAX:
        errors["course"] = f"所属课程不能超过 {COURSE_MAX} 个字"

    if len(data["description"]) > DESCRIPTION_MAX:
        errors["description"] = f"任务描述不能超过 {DESCRIPTION_MAX} 个字"

    if not data["due_date"]:
        errors["due_date"] = "截止日期不能为空"
    elif parse_date(data["due_date"]) is None:
        errors["due_date"] = "截止日期格式应为 YYYY-MM-DD，且必须是有效日期"

    if data["priority"] not in PRIORITIES:
        errors["priority"] = "优先级只能是高、中、低"

    if data["status"] not in STATUSES:
        errors["status"] = "任务状态只能是待完成、进行中、已完成"

    return data, errors


def create_task(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    cur = db.execute(
        """INSERT INTO tasks
           (title, course, description, due_date, priority, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["title"],
            data["course"],
            data["description"],
            data["due_date"],
            data["priority"],
            data["status"],
            now,
            now,
        ),
    )
    db.commit()
    return cur.lastrowid


def update_task(task_id, data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    cur = db.execute(
        """UPDATE tasks
           SET title = ?, course = ?, description = ?, due_date = ?,
               priority = ?, status = ?, updated_at = ?
           WHERE id = ?""",
        (
            data["title"],
            data["course"],
            data["description"],
            data["due_date"],
            data["priority"],
            data["status"],
            now,
            task_id,
        ),
    )
    db.commit()
    return cur.rowcount > 0


def set_status(task_id, status):
    db = get_db()
    cur = db.execute(
        "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
        (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id),
    )
    db.commit()
    return cur.rowcount > 0


def delete_task(task_id):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return cur.rowcount > 0


def get_task(task_id):
    return get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def list_tasks(course="", status="", priority=""):
    """按课程、状态、优先级组合筛选，未完成且紧急的任务排在前面。"""
    sql = "SELECT * FROM tasks WHERE 1 = 1"
    params = []
    if course:
        sql += " AND course = ?"
        params.append(course)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if priority:
        sql += " AND priority = ?"
        params.append(priority)
    sql += " ORDER BY CASE status WHEN '已完成' THEN 1 ELSE 0 END, due_date ASC, id ASC"
    return get_db().execute(sql, params).fetchall()


def list_courses():
    rows = get_db().execute("SELECT DISTINCT course FROM tasks ORDER BY course").fetchall()
    return [row["course"] for row in rows]


def get_stats():
    row = get_db().execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END), 0) AS completed
           FROM tasks"""
    ).fetchone()
    total = row["total"]
    completed = row["completed"]
    rate = round(completed / total * 100, 1) if total else 0.0
    return {"total": total, "completed": completed, "rate": rate}


def deadline_state(task, base_day=None):
    """返回 None / 'overdue' / 'soon'。已完成任务不再提示。"""
    if task["status"] == "已完成":
        return None
    due = parse_date(task["due_date"])
    if due is None:
        return None
    base_day = base_day or today()
    days_left = (due - base_day).days
    if days_left < 0:
        return "overdue"
    if days_left <= 3:
        return "soon"
    return None


def days_left_text(task, base_day=None):
    due = parse_date(task["due_date"])
    if due is None:
        return ""
    days = (due - (base_day or today())).days
    if days < 0:
        return f"已逾期 {abs(days)} 天"
    if days == 0:
        return "今天截止"
    if days == 1:
        return "明天截止"
    return f"剩余 {days} 天"


def format_rate(rate):
    """40.0 -> '40%'，33.3 -> '33.3%'。"""
    if float(rate).is_integer():
        return f"{int(rate)}%"
    return f"{rate:.1f}%"
