# -*- coding: utf-8 -*-
"""
SQL Server 连通性与查询测试脚本（Python 2.7 兼容）

用小白能懂的话：
- 这个脚本读取 config.ini，如果配置了 SQL Server，就尝试连接并跑一条“重复 jobcode”查询；
- 如果本机没有安装 SQL Server 的 Python 驱动，会提示你安装，并做一个端口连通性小测试；
- 如果还是用 sqlite，则跑本地 demo.sqlite 的同样查询，帮你确认模板渲染没问题。
"""

import sys
import os
import socket
import argparse

try:
    from ConfigParser import ConfigParser  # Python 2
except Exception:
    from configparser import ConfigParser  # Python 3 调试兼容

from db_client_py2 import (
    query_duplicate_jobcodes_sqlserver,
    query_duplicate_jobcodes,
)


def check_port(host, port, timeout=5):
    """
    端口连通性小测试：尝试 TCP 连接 host:port，成功返回 True，失败返回 False。
    这个不等于数据库能用，只是说明网络层能到达。
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, int(port)))
        sock.close()
        return True
    except Exception:
        return False


def read_config(path):
    """
    读取配置文件，返回 wecom/db/robot/message 配置字典。
    """
    if not os.path.isfile(path):
        raise Exception("配置文件不存在：%s" % path)
    cp = ConfigParser()
    cp.read(path)
    db = {
        "driver": cp.get("db", "driver"),
        "sqlite_path": cp.get("db", "sqlite_path") if cp.has_option("db", "sqlite_path") else "",
        "host": cp.get("db", "host") if cp.has_option("db", "host") else "",
        "port": int(cp.get("db", "port")) if cp.has_option("db", "port") else 1433,
        "database": cp.get("db", "database") if cp.has_option("db", "database") else "",
        "user": cp.get("db", "user") if cp.has_option("db", "user") else "",
        "password": cp.get("db", "password") if cp.has_option("db", "password") else "",
    }
    return {"db": db}


def main():
    """
    主流程：读取配置 → 判断驱动 → 执行查询或给出安装提示与端口测试结论。
    """
    parser = argparse.ArgumentParser(description="Test SQL Server connectivity and duplicate jobcode query")
    parser.add_argument("--config", default="config/config.ini", help="配置文件路径")
    args = parser.parse_args()

    cfg = read_config(args.config)
    db = cfg["db"]

    if db["driver"].lower() == "sqlserver":
        # 先做端口连通性测试
        ok_net = check_port(db["host"], db["port"])
        print("网络连通性(10.250.122.101:1433)：%s" % ("OK" if ok_net else "失败"))

        try:
            rows = query_duplicate_jobcodes_sqlserver(db["host"], db["user"], db["password"], db["database"], db["port"])
            print("查询成功，结果条数：%d" % len(rows))
            preview = rows[:5]
            for r in preview:
                print("jobcode=%s dup_count=%d" % (r["jobcode"], r["dup_count"]))
            return 0
        except Exception as e:
            print("查询失败：%s" % e)
            print("可能原因：未安装 SQL Server 驱动（pymssql 或 pyodbc）或数据库连接/权限问题。")
            return 1
    else:
        try:
            rows = query_duplicate_jobcodes(db["sqlite_path"])
            print("SQLite 查询成功，结果条数：%d" % len(rows))
            preview = rows[:5]
            for r in preview:
                print("jobcode=%s dup_count=%d" % (r["jobcode"], r["dup_count"]))
            return 0
        except Exception as e:
            print("SQLite 查询失败：%s" % e)
            return 1


if __name__ == "__main__":
    sys.exit(main())

