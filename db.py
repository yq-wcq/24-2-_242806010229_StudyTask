"""SQLite 数据访问层：连接管理、建表与查询。"""

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    course      TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    due_date    TEXT    NOT NULL,
    priority    TEXT    NOT NULL DEFAULT '中'
                CHECK (priority IN ('高', '中', '低')),
    status      TEXT    NOT NULL DEFAULT '待完成'
                CHECK (status IN ('待完成', '进行中', '已完成')),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
"""


def get_db() -> sqlite3.Connection:
    """获取当前请求的数据库连接（每个请求复用同一个连接）。"""
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """创建数据表；可重复执行。"""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
