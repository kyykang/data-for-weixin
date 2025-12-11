# -*- coding: utf-8 -*-
"""
数据库查询封装（Python 2.7 兼容，入门示例用 SQLite）

功能说明：
- 为了方便在任何环境跑起来，示例使用 Python 自带的 SQLite。
- 示例一：alerts(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at TEXT)
- 示例二：bd_jobbasfil(id INTEGER PRIMARY KEY AUTOINCREMENT, jobcode TEXT, created_at TEXT)
- 提供：初始化示例库、查询重复 jobcode 分组。
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


def init_demo_jobcodes(sqlite_path):
    """
    初始化示例表 bd_jobbasfil（如果不存在），并插入一组重复的 jobcode 数据。

    目的：配合如下 SQL 查询产生结果：
    select count(jobcode) as '重复次数', jobcode
    from bd_jobbasfil group by jobcode having count(*)>1 order by jobcode desc;
    """
    conn = _connect_sqlite(sqlite_path)
    try:
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS bd_jobbasfil (\n"
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "  jobcode TEXT,\n"
            "  created_at TEXT\n"
            ")"
        )
        # 插入一组重复 jobcode（两条同一个 jobcode），以及一条不重复数据
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO bd_jobbasfil(jobcode, created_at) VALUES(?, ?)", ("JC-999", now))
        c.execute("INSERT INTO bd_jobbasfil(jobcode, created_at) VALUES(?, ?)", ("JC-999", now))
        c.execute("INSERT INTO bd_jobbasfil(jobcode, created_at) VALUES(?, ?)", ("JC-ABC", now))
        conn.commit()
    finally:
        conn.close()


def query_duplicate_jobcodes(sqlite_path):
    """
    执行重复 jobcode 查询，返回满足条件的分组列表。

    查询语句：
    select count(jobcode) as '重复次数', jobcode
    from bd_jobbasfil group by jobcode having count(*)>1 order by jobcode desc;

    返回：
    - 列表，每个元素为字典：{"jobcode": "JC-999", "dup_count": 2}
    """
    conn = _connect_sqlite(sqlite_path)
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(jobcode) AS dup_count, jobcode "
            "FROM bd_jobbasfil GROUP BY jobcode HAVING COUNT(*)>1 ORDER BY jobcode DESC"
        )
        rows = c.fetchall()
        result = []
        for r in rows:
            # r[0] = dup_count, r[1] = jobcode
            result.append({"dup_count": int(r[0]), "jobcode": r[1]})
        return result
    finally:
        conn.close()
