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
import sys

# 优先尝试 pymssql，其次 pyodbc，此外支持 pytds（用于 SQL Server 连接）
_HAS_PYMSSQL = False
_HAS_PYODBC = False
_HAS_PYTDS = False
try:
    import pymssql
    _HAS_PYMSSQL = True
except Exception:
    try:
        import pyodbc
        _HAS_PYODBC = True
    except Exception:
        try:
            import pytds
            _HAS_PYTDS = True
        except Exception:
            pass

# MySQL 驱动检测
_HAS_MYSQLDB = False
_HAS_PYMYSQL = False
try:
    import MySQLdb
    _HAS_MYSQLDB = True
except Exception:
    try:
        import pymysql
        _HAS_PYMYSQL = True
    except Exception:
        pass


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


def _connect_sqlserver(host, user, password, database, port=1433, timeout=8):
    """
    连接到 SQL Server 数据库。

    参数：
    - host：数据库主机地址，例如 "10.250.122.101"
    - user：用户名，例如 "sa"
    - password：密码字符串
    - database：数据库名，例如 "U8CLOUD202102"
    - port：端口（默认 1433）
    - timeout：连接超时时间（秒）

    返回：
    - 连接对象（pymssql.Connection 或 pyodbc.Connection）

    说明：
    - 优先使用 pymssql（推荐 Linux 安装 FreeTDS），否则使用 pyodbc（需安装 Microsoft ODBC Driver）。
    """
    if _HAS_PYMSSQL:
        return pymssql.connect(server=host, user=user, password=password, database=database, port=int(port), login_timeout=timeout, timeout=timeout, charset='utf8')
    if _HAS_PYODBC:
        # 注意：pyodbc 需要系统已安装 ODBC 驱动（如 ODBC Driver 17 for SQL Server）
        dsn = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=%s,%d;DATABASE=%s;UID=%s;PWD=%s;TrustServerCertificate=Yes' % (
            host, int(port), database, user, password
        )
        return pyodbc.connect(dsn, timeout=timeout)
    if _HAS_PYTDS:
        # pytds 为纯 Python 驱动，安装简单；这里启用 autocommit 方便查询
        return pytds.connect(server=host, user=user, password=password, database=database, port=int(port), autocommit=True)
    raise Exception('未检测到可用的 SQL Server 驱动：请安装 pymssql、pyodbc 或 python-tds（pytds）')


def _connect_mysql(host, user, password, database, port=3306, timeout=8):
    """
    连接到 MySQL 数据库。

    参数：
    - host：数据库主机地址
    - user：用户名
    - password：密码字符串
    - database：数据库名
    - port：端口（默认 3306）
    - timeout：连接超时时间（秒）

    返回：
    - 连接对象（MySQLdb.Connection 或 pymysql.Connection）

    说明：
    - 优先使用 MySQLdb，否则使用 pymysql（纯 Python 实现）
    - 安装方式：pip install MySQL-python 或 pip install pymysql
    """
    if _HAS_MYSQLDB:
        import MySQLdb
        return MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=database,
            port=int(port),
            connect_timeout=timeout,
            charset='utf8'
        )
    if _HAS_PYMYSQL:
        import pymysql
        return pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port),
            connect_timeout=timeout,
            charset='utf8'
        )
    raise Exception('未检测到可用的 MySQL 驱动：请安装 MySQL-python 或 pymysql')


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


def query_duplicate_jobcodes_sqlserver(host, user, password, database, port=1433):
    """
    在 SQL Server 上执行重复 jobcode 查询。

    查询语句与 SQLite 保持一致的语义：
    SELECT COUNT(jobcode) AS dup_count, jobcode
    FROM bd_jobbasfil GROUP BY jobcode HAVING COUNT(*)>1 ORDER BY jobcode DESC;

    返回：
    - 列表，每个元素为字典：{"jobcode": "JC-999", "dup_count": 2}
    """
    conn = _connect_sqlserver(host, user, password, database, port)
    try:
        sql = (
            "SELECT COUNT(jobcode) AS dup_count, jobcode "
            "FROM bd_jobbasfil GROUP BY jobcode HAVING COUNT(*)>1 ORDER BY jobcode DESC"
        )
        # 统一使用游标执行
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        result = []
        for r in rows:
            try:
                # 大多数驱动返回 (dup_count, jobcode)
                dup_count = int(r[0])
                jobcode = r[1]
            except Exception:
                # 某些驱动返回字典/Row 对象，做兼容处理
                dup_count = int(getattr(r, 'dup_count', r[0]))
                jobcode = getattr(r, 'jobcode', r[1])
            result.append({"dup_count": dup_count, "jobcode": jobcode})
        return result
    finally:
        try:
            conn.close()
        except Exception:
            pass


def query_nonempty_jobcodes(sqlite_path):
    """
    小白版说明：查询 SQLite 中所有“有值”的 jobcode（去掉空白）。

    - 做什么：找出所有不为空的 jobcode 并去重
    - 为什么：只要查到任何 jobcode，就要推送
    - 返回：列表，如 [{"jobcode": "JC-001"}, ...]
    """
    conn = _connect_sqlite(sqlite_path)
    try:
        c = conn.cursor()
        c.execute(
            "SELECT DISTINCT jobcode FROM bd_jobbasfil WHERE jobcode IS NOT NULL AND TRIM(jobcode)<>''"
        )
        rows = c.fetchall()
        return [{"jobcode": r[0]} for r in rows]
    finally:
        conn.close()


def query_nonempty_jobcodes_sqlserver(host, user, password, database, port=1433):
    """
    小白版说明：查询 SQL Server 中所有“有值”的 jobcode（去掉空白）。

    - 做什么：找出所有不为空的 jobcode 并去重
    - 为什么：只要查到任何 jobcode，就要推送
    - 返回：列表，如 [{"jobcode": "JC-001"}, ...]
    """
    conn = _connect_sqlserver(host, user, password, database, port)
    try:
        sql = (
            "SELECT DISTINCT jobcode FROM bd_jobbasfil "
            "WHERE jobcode IS NOT NULL AND LTRIM(RTRIM(jobcode))<>''"
        )
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        result = []
        for r in rows:
            jobcode = getattr(r, 'jobcode', None)
            if jobcode is None:
                jobcode = r[0]
            result.append({"jobcode": jobcode})
        return result
    finally:
        try:
            conn.close()
        except Exception:
            pass


def query_failed_push_mysql(host, user, password, database, port=3306):
    """
    查询 MySQL 中推送失败的项目（field0045='2'）。

    查询语句：
    SELECT field0001, field0045 FROM formmain_1559 WHERE field0045='2'

    参数：
    - host：MySQL 主机地址
    - user：用户名
    - password：密码
    - database：数据库名
    - port：端口（默认 3306）

    返回：
    - 列表，每个元素为字典：{"field0001": "项目名称", "field0045": "2"}
    """
    conn = _connect_mysql(host, user, password, database, port)
    try:
        sql = "SELECT field0001, field0045 FROM formmain_1559 WHERE field0045='2'"
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        result = []
        for r in rows:
            # r[0] = field0001, r[1] = field0045
            if r[1] == '2':  # 确认 field0045 是 '2'
                result.append({"field0001": r[0], "field0045": r[1]})
        return result
    finally:
        try:
            conn.close()
        except Exception:
            pass
