"""实验一最低验收用例 T1—T10 的自动化测试。"""

from datetime import date, timedelta

from task_service import get_stats, list_tasks


def html(response):
    return response.get_data(as_text=True)


class TestCreate:
    def test_t1_create_task_and_show_in_list(self, make_task, tomorrow):
        response = make_task(
            title="完成链表实验报告",
            course="数据结构",
            due=tomorrow,
            priority="高",
            description="第 3 章课后实验",
        )
        assert response.status_code == 200
        body = html(response)
        assert "完成链表实验报告" in body
        assert "数据结构" in body
        assert "高" in body
        assert "即将到期" in body
        assert "任务创建成功" in body

    def test_t2_empty_title_is_rejected(self, client, tomorrow):
        response = client.post(
            "/tasks",
            data={
                "title": "   ",
                "course": "软件工程",
                "description": "",
                "due_date": tomorrow,
                "priority": "中",
                "status": "待完成",
            },
        )
        assert response.status_code == 400
        body = html(response)
        assert "任务名称不能为空" in body
        assert "完成链表实验报告" not in body

        with client.application.app_context():
            assert get_stats()["total"] == 0

    def test_missing_required_fields_are_rejected(self, client):
        response = client.post("/tasks", data={})
        assert response.status_code == 400
        body = html(response)
        assert "任务名称不能为空" in body
        assert "所属课程不能为空" in body
        assert "截止日期不能为空" in body

    def test_invalid_date_is_rejected(self, client):
        for bad_date in ("2026-02-30", "2026/03/01", "abc"):
            response = client.post(
                "/tasks",
                data={
                    "title": "非法日期任务",
                    "course": "软件工程",
                    "description": "",
                    "due_date": bad_date,
                    "priority": "中",
                    "status": "待完成",
                },
            )
            assert response.status_code == 400
            assert "截止日期格式应为" in html(response)

    def test_invalid_priority_and_status_are_rejected(self, client, tomorrow):
        response = client.post(
            "/tasks",
            data={
                "title": "非法枚举任务",
                "course": "软件工程",
                "description": "",
                "due_date": tomorrow,
                "priority": "紧急",
                "status": "已归档",
            },
        )
        assert response.status_code == 400
        body = html(response)
        assert "优先级只能是高、中、低" in body
        assert "任务状态只能是待完成、进行中、已完成" in body

    def test_too_long_fields_are_rejected(self, client, tomorrow):
        response = client.post(
            "/tasks",
            data={
                "title": "标" * 101,
                "course": "课" * 61,
                "description": "描" * 1001,
                "due_date": tomorrow,
                "priority": "中",
                "status": "待完成",
            },
        )
        assert response.status_code == 400
        body = html(response)
        assert "任务名称不能超过 100 个字" in body
        assert "所属课程不能超过 60 个字" in body
        assert "任务描述不能超过 1000 个字" in body


class TestReadUpdateDelete:
    def test_t3_edit_description_and_priority_persist(self, client, make_task):
        make_task(title="编辑测试任务", description="旧描述", priority="低")
        with client.application.app_context():
            from task_service import list_tasks

            task_id = list_tasks()[0]["id"]

        response = client.post(
            f"/tasks/{task_id}/edit",
            data={
                "title": "编辑测试任务",
                "course": "软件工程",
                "description": "新描述：补充接口文档",
                "due_date": date.today().isoformat(),
                "priority": "高",
                "status": "待完成",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "任务已更新" in html(response)

        detail = html(client.get(f"/tasks/{task_id}"))
        assert "新描述：补充接口文档" in detail
        assert "高" in detail
        assert "旧描述" not in detail

    def test_t4_status_transitions(self, client, make_task):
        make_task(title="状态流转任务")
        with client.application.app_context():
            from task_service import list_tasks

            task_id = list_tasks()[0]["id"]

        for status in ("进行中", "已完成"):
            response = client.post(
                f"/tasks/{task_id}/status",
                data={"status": status},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert f"任务状态已更新为“{status}”" in html(response)

            with client.application.app_context():
                from task_service import get_task

                assert get_task(task_id)["status"] == status

    def test_t9_delete_requires_confirmation(self, client, make_task):
        make_task(title="待删除任务")
        with client.application.app_context():
            from task_service import list_tasks

            task_id = list_tasks()[0]["id"]

        confirm_page = client.get(f"/tasks/{task_id}/delete")
        assert confirm_page.status_code == 200
        assert "确认删除" in html(confirm_page)

        with client.application.app_context():
            from task_service import get_task

            assert get_task(task_id) is not None

        # 取消：回到详情页，数据仍在
        cancel = client.get(f"/tasks/{task_id}")
        assert cancel.status_code == 200
        with client.application.app_context():
            assert get_task(task_id) is not None

        deleted = client.post(f"/tasks/{task_id}/delete", follow_redirects=True)
        assert "任务已删除" in html(deleted)
        with client.application.app_context():
            assert get_task(task_id) is None

    def test_unknown_task_returns_404(self, client):
        assert client.get("/tasks/9999").status_code == 404
        assert client.get("/tasks/9999/edit").status_code == 404


class TestFilter:
    def _seed(self, make_task):
        make_task(title="任务A", course="数据结构", due="2026-12-01", priority="高")
        make_task(
            title="任务B",
            course="数据结构",
            due="2026-12-02",
            priority="高",
            status="已完成",
        )
        make_task(title="任务C", course="数据库原理", due="2026-12-03", priority="低")
        make_task(title="任务D", course="数据结构", due="2026-12-04", priority="低")

    def test_t5_filter_by_course(self, client, make_task):
        self._seed(make_task)
        body = html(client.get("/?course=数据结构"))
        assert "任务A" in body and "任务B" in body and "任务D" in body
        assert "任务C" not in body

    def test_t5_filter_by_status(self, client, make_task):
        self._seed(make_task)
        body = html(client.get("/?status=已完成"))
        assert "任务B" in body
        assert "任务A" not in body and "任务C" not in body and "任务D" not in body

    def test_t5_filter_by_priority(self, client, make_task):
        self._seed(make_task)
        body = html(client.get("/?priority=低"))
        assert "任务C" in body and "任务D" in body
        assert "任务A" not in body and "任务B" not in body

    def test_t5_combined_filters(self, client, make_task):
        self._seed(make_task)
        body = html(client.get("/?course=数据结构&status=待完成&priority=高"))
        assert "任务A" in body
        for other in ("任务B", "任务C", "任务D"):
            assert other not in body

    def test_empty_filter_result_shows_hint(self, client, make_task):
        make_task(title="任务A", course="数据结构")
        body = html(client.get("/?course=不存在的课程"))
        assert "没有符合条件的任务" in body


class TestDeadline:
    def test_t6_overdue_badge(self, client, make_task, yesterday):
        make_task(title="逾期任务", due=yesterday)
        body = html(client.get("/"))
        assert "逾期任务" in body
        assert "已逾期" in body

    def test_t7_soon_badge(self, client, make_task, tomorrow):
        make_task(title="即将到期任务", due=tomorrow)
        body = html(client.get("/"))
        assert "即将到期" in body

    def test_completed_task_has_no_overdue_badge(self, client, make_task, yesterday):
        make_task(title="已完成旧任务", due=yesterday, status="已完成")
        body = html(client.get(f"/tasks/1"))
        assert "已完成旧任务" in body
        assert "已逾期" not in body

    def test_due_today_is_soon(self, client, make_task):
        make_task(title="今天截止任务", due=date.today().isoformat())
        body = html(client.get("/"))
        assert "今天截止" in body
        assert "即将到期" in body

    def test_due_in_four_days_is_not_soon(self, client, make_task):
        make_task(
            title="四天后任务",
            due=(date.today() + timedelta(days=4)).isoformat(),
        )
        body = html(client.get("/"))
        assert "四天后任务" in body
        assert "即将到期" not in body
        assert "已逾期" not in body


class TestStats:
    def test_t8_stats_total_completed_rate(self, client, make_task):
        for index in range(5):
            status = "已完成" if index < 2 else "待完成"
            make_task(title=f"统计任务{index}", status=status)

        body = html(client.get("/"))
        assert "40%" in body
        with client.application.app_context():
            stats = get_stats()
            assert stats["total"] == 5
            assert stats["completed"] == 2

    def test_empty_stats_rate_is_zero(self, client):
        body = html(client.get("/"))
        assert "0%" in body
        with client.application.app_context():
            assert get_stats() == {"total": 0, "completed": 0, "rate": 0.0}

    def test_fractional_rate_is_rendered(self, client, make_task):
        make_task(title="统计任务1", status="已完成")
        make_task(title="统计任务2")
        make_task(title="统计任务3")
        body = html(client.get("/"))
        assert "33.3%" in body


class TestPersistence:
    def test_t10_data_survives_restart(self, db_path, make_task):
        from app import create_app

        config = {"TESTING": True, "SECRET_KEY": "same", "DATABASE": str(db_path)}
        first = create_app(config)
        first_client = first.test_client()
        first_client.post(
            "/tasks",
            data={
                "title": "重启后仍存在的任务",
                "course": "操作系统",
                "description": "",
                "due_date": (date.today() + timedelta(days=2)).isoformat(),
                "priority": "中",
                "status": "待完成",
            },
            follow_redirects=True,
        )

        second = create_app(config)
        body = html(second.test_client().get("/"))
        assert "重启后仍存在的任务" in body
        with second.app_context():
            assert get_stats()["total"] == 1
