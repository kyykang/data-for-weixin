# -*- coding: utf-8 -*-
"""
数据库查询封装（Python 2.7 兼容，入门示例用 SQLite）

功能说明：
- 为了方便在任何环境跑起来，示例使用 Python 自带的 SQLite。
- 表结构示例：alerts(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)
- 提供：初始化示例库、查询大于 last_id 的新数据。
"""

import os
import sqlite3
import time


def ensure_dir(path):
    """
    确保目录存在，不存在则创建。
    """
    if not os.path.isdir(path):
        os.makedirs(path)


def _connect_sqlite(sqlite_path):
    """
    连接到 SQLite 数据库文件。

    参数：sqlite_path 为数据库文件路径。
    返回：sqlite3.Connection 对象。
    """
    dir_path = os.path.dirname(sqlite_path) or "."
    ensure_dir(dir_path)
    conn = sqlite3.connect(sqlite_path)
    return conn


def init_demo_if_needed(sqlite_path):
    """
    初始化示例表 alerts（如果不存在），并插入一条示例数据。

    参数：sqlite_path 为数据库文件路径。
    """
    conn = _connect_sqlite(sqlite_path)
    try:
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS alerts (\n"
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "  title TEXT,\n"
            "  created_at TEXT\n"
            ")"
        )
        # 插入一条示例数据，便于本地联调
        c.execute(
            "INSERT INTO alerts(title, created_at) VALUES(?, ?)",
            ("示例告警 - %s" % time.strftime("%Y-%m-%d %H:%M:%S"), time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
    finally:
        conn.close()


def query_new_alerts(sqlite_path, last_id, limit):
    """
    查询主键大于 last_id 的新数据，按 id 升序返回前 limit 条。

    参数：
    - sqlite_path：数据库文件路径
    - last_id：上次已处理的最大 id（整数）
    - limit：最多返回的条数（整数）

    返回：
    - 列表，每个元素为字典：{"id": 123, "title": "...", "created_at": "..."}
    """
    conn = _connect_sqlite(sqlite_path)
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, title, created_at FROM alerts WHERE id > ? ORDER BY id ASC LIMIT ?",
            (int(last_id), int(limit)),
        )
        rows = c.fetchall()
        result = []
        for r in rows:
            result.append({"id": int(r[0]), "title": r[1], "created_at": r[2]})
        return result
    finally:
        conn.close()

