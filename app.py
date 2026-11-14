"""StudyTask —— 单用户学习任务管理系统（Flask + SQLite）。"""

import os

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from db import close_db, init_db
from task_service import (
    PRIORITIES,
    STATUSES,
    STATUS_FLOW,
    STATUS_NEXT_LABEL,
    create_task as create_task_record,
    deadline_state,
    days_left_text,
    delete_task,
    format_rate,
    get_stats,
    get_task,
    list_courses,
    list_tasks,
    set_status,
    update_task,
    validate_task,
)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "studytask-dev-key"),
        DATABASE=os.path.join(app.instance_path, "studytask.db"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(close_db)
    app.jinja_env.filters["deadline_state"] = deadline_state
    app.jinja_env.filters["days_left_text"] = days_left_text
    app.jinja_env.filters["rate_text"] = format_rate

    def safe_next(default):
        target = request.form.get("next") or request.args.get("next") or ""
        if target.startswith("/") and not target.startswith("//"):
            return target
        return default

    @app.get("/")
    def index():
        filters = {
            "course": request.args.get("course", "").strip(),
            "status": request.args.get("status", "").strip(),
            "priority": request.args.get("priority", "").strip(),
        }
        tasks = list_tasks(**filters)
        return render_template(
            "index.html",
            tasks=tasks,
            stats=get_stats(),
            courses=list_courses(),
            filters=filters,
            priorities=PRIORITIES,
            statuses=STATUSES,
            has_filter=any(filters.values()),
        )

    def empty_task():
        return {
            "title": "",
            "course": "",
            "description": "",
            "due_date": "",
            "priority": "中",
            "status": "待完成",
        }

    @app.get("/tasks/new")
    def new_task():
        return render_template(
            "task_form.html",
            task=empty_task(),
            errors={},
            mode="create",
            priorities=PRIORITIES,
            statuses=STATUSES,
            courses=list_courses(),
        )

    @app.post("/tasks")
    def submit_task():
        data, errors = validate_task(request.form)
        if errors:
            task = empty_task()
            task.update(data)
            return (
                render_template(
                    "task_form.html",
                    task=task,
                    errors=errors,
                    mode="create",
                    priorities=PRIORITIES,
                    statuses=STATUSES,
                    courses=list_courses(),
                ),
                400,
            )
        task_id = create_task_record(data)
        flash("任务创建成功", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    @app.get("/tasks/<int:task_id>")
    def task_detail(task_id):
        task = get_task(task_id)
        if task is None:
            abort(404)
        return render_template(
            "task_detail.html",
            task=task,
            next_status=STATUS_FLOW[task["status"]],
            next_label=STATUS_NEXT_LABEL[task["status"]],
            statuses=STATUSES,
        )

    @app.route("/tasks/<int:task_id>/edit", methods=("GET", "POST"))
    def edit_task(task_id):
        existing = get_task(task_id)
        if existing is None:
            abort(404)
        task = dict(existing)
        errors = {}
        if request.method == "POST":
            data, errors = validate_task(request.form)
            task.update(data)
            if not errors:
                update_task(task_id, data)
                flash("任务已更新", "success")
                return redirect(url_for("task_detail", task_id=task_id))
        return (
            render_template(
                "task_form.html",
                task=task,
                errors=errors,
                mode="edit",
                priorities=PRIORITIES,
                statuses=STATUSES,
                courses=list_courses(),
            ),
            400 if errors else 200,
        )

    @app.post("/tasks/<int:task_id>/status")
    def change_status(task_id):
        if get_task(task_id) is None:
            abort(404)
        status = (request.form.get("status") or "").strip()
        if status not in STATUSES:
            flash("非法的任务状态", "error")
            return redirect(url_for("task_detail", task_id=task_id))
        set_status(task_id, status)
        flash(f"任务状态已更新为“{status}”", "success")
        return redirect(safe_next(url_for("task_detail", task_id=task_id)))

    @app.get("/tasks/<int:task_id>/delete")
    def confirm_delete(task_id):
        task = get_task(task_id)
        if task is None:
            abort(404)
        return render_template("task_delete.html", task=task, next=request.args.get("next", ""))

    @app.post("/tasks/<int:task_id>/delete")
    def remove_task(task_id):
        if get_task(task_id) is None:
            abort(404)
        delete_task(task_id)
        flash("任务已删除", "success")
        return redirect(safe_next(url_for("index")))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
