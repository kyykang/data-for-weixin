# -*- coding: utf-8 -*-
"""
入口脚本（Python 2.7 兼容）：查询数据库并向企业微信推送。

用小白能懂的话：
- 这个脚本每次运行会做三件事：1）读配置，2）查数据库，3）有新数据就发企业微信。
- 为了避免重复发，我们会记住“上次处理到的最大 id”。
- 你可以加 --dry-run 做“演习”，只打印消息，不真的发出去。
"""

import os
import sys
import json
import argparse

try:
    from ConfigParser import ConfigParser  # Python 2
except Exception:
    from configparser import ConfigParser  # Python 3 调试兼容

from db_client_py2 import (
    init_demo_if_needed,
    init_demo_jobcodes,
    query_duplicate_jobcodes,
    query_duplicate_jobcodes_sqlserver,
    query_failed_push_mysql,
)
# 注意：为兼容 Python3 的干跑模式，我们在需要时再导入 wecom 客户端


def read_config(path):
    """
    读取 INI 配置文件，返回字典。

    参数：path 为配置文件路径，例如 config/config.ini。
    返回：{"wecom": {...}, "db": {...}, "db_mysql": {...}}
    """
    if not os.path.isfile(path):
        raise Exception("配置文件不存在：%s" % path)
    cp = ConfigParser()
    cp.read(path)
    cfg = {
        "wecom": {
            "corpid": cp.get("wecom", "corpid"),
            "corpsecret": cp.get("wecom", "corpsecret"),
            "agentid": cp.get("wecom", "agentid"),
            "touser": cp.get("wecom", "touser"),
        },
        "db": {
            "driver": cp.get("db", "driver"),
            "sqlite_path": cp.get("db", "sqlite_path") if cp.has_option("db", "sqlite_path") else "",
            # SQL Server / MySQL 可选参数
            "host": cp.get("db", "host") if cp.has_option("db", "host") else "",
            "port": int(cp.get("db", "port")) if cp.has_option("db", "port") else 1433,
            "database": cp.get("db", "database") if cp.has_option("db", "database") else "",
            "user": cp.get("db", "user") if cp.has_option("db", "user") else "",
            "password": cp.get("db", "password") if cp.has_option("db", "password") else "",
        },
    }
    # MySQL 默认端口是 3306
    if cp.get("db", "driver") == "mysql":
        cfg["db"]["port"] = int(cp.get("db", "port")) if cp.has_option("db", "port") else 3306
    
    # 可选的 MySQL 配置（独立配置节）
    if cp.has_section("db_mysql"):
        cfg["db_mysql"] = {
            "enabled": cp.get("db_mysql", "enabled").lower() in ["true", "1", "yes"] if cp.has_option("db_mysql", "enabled") else True,
            "host": cp.get("db_mysql", "host") if cp.has_option("db_mysql", "host") else "",
            "port": int(cp.get("db_mysql", "port")) if cp.has_option("db_mysql", "port") else 3306,
            "database": cp.get("db_mysql", "database") if cp.has_option("db_mysql", "database") else "",
            "user": cp.get("db_mysql", "user") if cp.has_option("db_mysql", "user") else "",
            "password": cp.get("db_mysql", "password") if cp.has_option("db_mysql", "password") else "",
        }
    
    # 可选的消息模板配置
    if cp.has_section("message"):
        msg_cfg = {}
        # text 模板
        for k in ["title_text", "item_text", "footer_text"]:
            if cp.has_option("message", k):
                msg_cfg[k] = cp.get("message", k)
        # markdown 模板
        for k in ["title_markdown", "item_markdown", "footer_markdown"]:
            if cp.has_option("message", k):
                msg_cfg[k] = cp.get("message", k)
        cfg["message"] = msg_cfg
    # 机器人配置为可选
    if cp.has_section("robot") and cp.has_option("robot", "webhook"):
        mentioned = []
        if cp.has_option("robot", "mentioned_list"):
            raw = cp.get("robot", "mentioned_list").strip()
            if raw:
                # 使用 | 分隔以统一风格
                mentioned = [x.strip() for x in raw.split("|") if x.strip()]
        fmt = "markdown"
        if cp.has_option("robot", "format"):
            fmt = cp.get("robot", "format").strip() or "markdown"
        cfg["robot"] = {
            "webhook": cp.get("robot", "webhook"),
            "mentioned_list": mentioned,
            "format": fmt,
        }
    return cfg


def compose_message(rows, max_preview, msg_cfg=None):
    """
    组织要发送的文本消息：
    - 标题：本次查询发现多少条新数据
    - 摘要：列出前 max_preview 条的 id、标题、时间
    返回：字符串
    """
    count = len(rows)
    if count == 0:
        return None
    lines = []
    title_tpl = (msg_cfg or {}).get("title_text") or u"数据库告警：检测到 {count} 条新数据"
    item_tpl = (msg_cfg or {}).get("item_text") or u"id={id}，{title}（{created_at}）"
    footer_tpl = (msg_cfg or {}).get("footer_text") or u"更多...（已省略 {omitted} 条）"
    lines.append(title_tpl.format(count=count))
    lines.append(u"——")
    preview = rows[:max_preview]
    for r in preview:
        # 显示每条的关键信息
        lines.append(item_tpl.format(id=r["id"], title=r["title"], created_at=r["created_at"]))
    if count > len(preview):
        lines.append(footer_tpl.format(omitted=(count - len(preview))))
    return u"\n".join(lines)


def compose_markdown_message(rows, max_preview, msg_cfg=None):
    """
    组织要发送的 Markdown 消息：
    - 标题：用二级标题展示总数
    - 列表：前 max_preview 条的 id、标题、时间
    返回：字符串（Markdown）
    """
    count = len(rows)
    if count == 0:
        return None
    lines = []
    title_tpl = (msg_cfg or {}).get("title_markdown") or u"## 数据库告警：检测到 {count} 条新数据"
    item_tpl = (msg_cfg or {}).get("item_markdown") or u"- id={id} ｜ {title} ｜ {created_at}"
    footer_tpl = (msg_cfg or {}).get("footer_markdown") or u"> 更多...（已省略 {omitted} 条）"
    lines.append(title_tpl.format(count=count))
    lines.append("")
    preview = rows[:max_preview]
    for r in preview:
        try:
            lines.append(item_tpl.format(**r))
        except Exception:
            # 回退到常见字段
            lines.append(item_tpl)
            lines.append(item_tpl.format(**r))
        except Exception:
            lines.append(item_tpl)
    if count > len(preview):
        lines.append("")
        lines.append(footer_tpl.format(omitted=(count - len(preview))))
    return u"\n".join(lines)


def compose_jobcode_text(rows, max_preview):
    """
    小白版说明：组装“文本消息”，只展示 jobcode。

    - 做什么：显示总数，并列出前 max_preview 个 jobcode
    - 为什么：你希望只要有数据就推送 jobcode 内容
    - 返回：字符串；无数据时返回 None
    """
    count = len(rows)
    if count == 0:
        return None
    lines = []
    lines.append(u"数据库告警：检测到 %d 个有值的 jobcode" % count)
    lines.append(u"——")
    for r in rows[:max_preview]:
        lines.append(u"jobcode=%s" % (r.get("jobcode") or u""))
    if count > max_preview:
        lines.append(u"更多...（已省略 %d 条）" % (count - max_preview))
    return u"\n".join(lines)


def compose_jobcode_markdown(rows, max_preview):
    """
    小白版说明：组装“Markdown 消息”，只展示 jobcode（群机器人更好看）。

    - 做什么：显示总数为二级标题，并列出前 max_preview 个 jobcode
    - 为什么：你希望只要有数据就推送 jobcode 内容
    - 返回：字符串（Markdown）；无数据时返回 None
    """
    count = len(rows)
    if count == 0:
        return None
    lines = []
    lines.append(u"## 数据库告警：检测到 %d 个有值的 jobcode" % count)
    lines.append("")
    for r in rows[:max_preview]:
        lines.append(u"- jobcode=%s" % (r.get("jobcode") or u""))
    if count > max_preview:
        lines.append("")
        lines.append(u"> 更多...（已省略 %d 条）" % (count - max_preview))
    return u"\n".join(lines)


def compose_failed_push_text(rows, max_preview):
    """
    组装"推送失败项目"的文本消息。

    参数：
    - rows：查询结果列表，每个元素包含 field0001
    - max_preview：最多展示的条数

    返回：
    - 字符串消息；无数据时返回 None
    """
    count = len(rows)
    if count == 0:
        return None
    lines = []
    lines.append(u"以下项目推送不成功")
    lines.append(u"——")
    for r in rows[:max_preview]:
        field0001 = r.get("field0001") or u""
        lines.append(u"%s" % field0001)
    if count > max_preview:
        lines.append(u"更多...（已省略 %d 条）" % (count - max_preview))
    return u"\n".join(lines)


def compose_failed_push_markdown(rows, max_preview):
    """
    组装"推送失败项目"的 Markdown 消息。

    参数：
    - rows：查询结果列表，每个元素包含 field0001
    - max_preview：最多展示的条数

    返回：
    - Markdown 字符串；无数据时返回 None
    """
    count = len(rows)
    if count == 0:
        return None
    lines = []
    lines.append(u"## 以下项目推送不成功")
    lines.append(u"")
    for r in rows[:max_preview]:
        field0001 = r.get("field0001") or u""
        lines.append(u"- %s" % field0001)
    if count > max_preview:
        lines.append(u"")
        lines.append(u"> 更多...（已省略 %d 条）" % (count - max_preview))
    return u"\n".join(lines)


def main():
    """
    主流程：读配置→（可选）初始化示例库→查询→（干跑或真实）发送→更新去重状态。
    支持同时查询多个数据库（db 和 db_mysql）。
    """
    parser = argparse.ArgumentParser(description="Query DB and notify WeCom (Python 2.7)")
    parser.add_argument("--config", default="config/config.ini", help="配置文件路径")
    parser.add_argument("--state", default="state/last_seen.json", help="去重状态文件路径")
    parser.add_argument("--limit", type=int, default=50, help="单次最多处理的记录数")
    parser.add_argument("--preview", type=int, default=5, help="消息中展示的预览条数")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式：不真正发企业微信，只打印")
    parser.add_argument("--init-demo", action="store_true", help="初始化示例 SQLite 表并插入一条数据")
    args = parser.parse_args()

    cfg = read_config(args.config)

    if args.init_demo and cfg["db"]["driver"] == "sqlite":
        init_demo_if_needed(cfg["db"]["sqlite_path"])
        init_demo_jobcodes(cfg["db"]["sqlite_path"])

    # 收集所有查询结果和消息
    all_messages = []
    
    # 查询主数据库（db 配置节）
    print("正在查询主数据库 [db] driver=%s ..." % cfg["db"]["driver"])
    if cfg["db"]["driver"] == "sqlite":
        rows = query_duplicate_jobcodes(cfg["db"]["sqlite_path"])
    elif cfg["db"]["driver"] == "sqlserver":
        rows = query_duplicate_jobcodes_sqlserver(
            cfg["db"]["host"], cfg["db"]["user"], cfg["db"]["password"], cfg["db"]["database"], cfg["db"].get("port", 1433)
        )
    elif cfg["db"]["driver"] == "mysql":
        rows = query_failed_push_mysql(
            cfg["db"]["host"], cfg["db"]["user"], cfg["db"]["password"], cfg["db"]["database"], cfg["db"].get("port", 3306)
        )
    else:
        raise Exception("不支持的数据库驱动：%s" % cfg["db"]["driver"])

    # 根据数据库类型过滤数据
    if cfg["db"]["driver"] == "mysql":
        # MySQL 查询已经在 SQL 中过滤了 field0045='2'，这里不需要额外过滤
        pass
    else:
        # SQLite 和 SQL Server 查询 jobcode，过滤空值
        rows = [r for r in rows if (r.get("jobcode") or "").strip()]
    
    print("主数据库 [db] 查询结果：%d 条记录" % len(rows))
    
    # 生成主数据库消息
    if rows:
        use_robot = False
        use_markdown = False
        msg = None
        if "robot" in cfg and cfg["robot"].get("webhook"):
            use_robot = True
            fmt = cfg["robot"].get("format") or "markdown"
            if fmt.lower() == "markdown":
                use_markdown = True
                if cfg["db"]["driver"] == "mysql":
                    msg = compose_failed_push_markdown(rows, args.preview)
                else:
                    msg = compose_jobcode_markdown(rows, args.preview)
        
        if msg is None:
            if cfg["db"]["driver"] == "mysql":
                msg = compose_failed_push_text(rows, args.preview)
            else:
                msg = compose_jobcode_text(rows, args.preview)
        
        if msg:
            all_messages.append(msg)
    
    # 查询 MySQL 数据库（db_mysql 配置节，如果启用）
    if "db_mysql" in cfg and cfg["db_mysql"].get("enabled", True):
        print("正在查询 MySQL 数据库 [db_mysql] ...")
        try:
            mysql_rows = query_failed_push_mysql(
                cfg["db_mysql"]["host"], 
                cfg["db_mysql"]["user"], 
                cfg["db_mysql"]["password"], 
                cfg["db_mysql"]["database"], 
                cfg["db_mysql"].get("port", 3306)
            )
            
            print("MySQL 数据库 [db_mysql] 查询结果：%d 条记录" % len(mysql_rows))
            
            if mysql_rows:
                use_robot = False
                use_markdown = False
                mysql_msg = None
                if "robot" in cfg and cfg["robot"].get("webhook"):
                    use_robot = True
                    fmt = cfg["robot"].get("format") or "markdown"
                    if fmt.lower() == "markdown":
                        use_markdown = True
                        mysql_msg = compose_failed_push_markdown(mysql_rows, args.preview)
                
                if mysql_msg is None:
                    mysql_msg = compose_failed_push_text(mysql_rows, args.preview)
                
                if mysql_msg:
                    all_messages.append(mysql_msg)
        except Exception as e:
            print("MySQL 查询失败：%s" % str(e))
    else:
        print("MySQL 数据库 [db_mysql] 未启用或未配置")
    
    # 如果没有任何消息，结束
    if not all_messages:
        print("所有数据库查询均无新数据，结束。")
        return 0
    
    print("共生成 %d 条消息，准备发送..." % len(all_messages))
    
    # 合并所有消息
    final_msg = u"\n\n".join(all_messages)

    if args.dry_run:
        # Python 2 下 msg 是 unicode，这里编码为 UTF-8 便于终端显示；Python 3 直接使用 str
        if sys.version_info[0] == 2:
            try:
                preview_text = final_msg.encode("utf-8")
            except Exception:
                preview_text = final_msg
        else:
            preview_text = final_msg
        print("干跑模式：将要发送的消息如下\n" + preview_text)
    else:
        # 优先使用群机器人（如果配置了 webhook），否则使用应用接口
        if use_robot:
            if use_markdown:
                from wecom_robot_py2 import send_markdown as robot_send_md
                ok = robot_send_md(cfg["robot"]["webhook"], final_msg)
            else:
                from wecom_robot_py2 import send_text as robot_send_text
                ok = robot_send_text(cfg["robot"]["webhook"], final_msg, cfg["robot"].get("mentioned_list"))
            if ok:
                print("企业微信群机器人消息已发送成功。")
        else:
            from wecom_client_py2 import get_access_token, send_text
            token = get_access_token(cfg["wecom"]["corpid"], cfg["wecom"]["corpsecret"])
            ok = send_text(token, cfg["wecom"]["agentid"], cfg["wecom"]["touser"], final_msg)
            if ok:
                print("企业微信应用消息已发送成功。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
