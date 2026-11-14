import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# 保证从任意工作目录执行 pytest 时都能导入项目根目录模块
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def app(db_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DATABASE": str(db_path),
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_task(client):
    """按表单字段创建任务，返回创建响应。"""

    def _make(
        title="完成实验报告",
        course="软件工程",
        due=None,
        priority="中",
        status="待完成",
        description="",
    ):
        if due is None:
            due = date.today().isoformat()
        return client.post(
            "/tasks",
            data={
                "title": title,
                "course": course,
                "description": description,
                "due_date": due,
                "priority": priority,
                "status": status,
            },
            follow_redirects=True,
        )

    return _make


@pytest.fixture
def tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


@pytest.fixture
def yesterday():
    return (date.today() - timedelta(days=1)).isoformat()
