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

<<<<<<< Updated upstream
from db_client_py2 import init_demo_if_needed, init_demo_jobcodes, query_nonempty_jobcodes, query_nonempty_jobcodes_sqlserver
=======
from db_client_py2 import (
    init_demo_if_needed,
    init_demo_jobcodes,
    query_nonempty_jobcodes,
    query_nonempty_jobcodes_sqlserver,
)
>>>>>>> Stashed changes
# 注意：为兼容 Python3 的干跑模式，我们在需要时再导入 wecom 客户端


def read_config(path):
    """
    读取 INI 配置文件，返回字典。

    参数：path 为配置文件路径，例如 config/config.ini。
    返回：{"wecom": {...}, "db": {...}}
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
            "sqlite_path": cp.get("db", "sqlite_path"),
            # SQL Server 可选参数（仅当 driver=sqlserver 时使用）
            "host": cp.get("db", "host") if cp.has_option("db", "host") else "",
            "port": int(cp.get("db", "port")) if cp.has_option("db", "port") else 1433,
            "database": cp.get("db", "database") if cp.has_option("db", "database") else "",
            "user": cp.get("db", "user") if cp.has_option("db", "user") else "",
            "password": cp.get("db", "password") if cp.has_option("db", "password") else "",
        },
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


def main():
    """
    主流程：读配置→（可选）初始化示例库→查询→（干跑或真实）发送→更新去重状态。
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

    # 根据驱动选择数据源（只要查到任何 jobcode 就推送）
    if cfg["db"]["driver"] == "sqlite":
        rows = query_nonempty_jobcodes(cfg["db"]["sqlite_path"])
    elif cfg["db"]["driver"] == "sqlserver":
        rows = query_nonempty_jobcodes_sqlserver(
            cfg["db"]["host"], cfg["db"]["user"], cfg["db"]["password"], cfg["db"]["database"], cfg["db"].get("port", 1433)
        )
    else:
        raise Exception("不支持的数据库驱动：%s" % cfg["db"]["driver"])

    if not rows:
        print("本次查询没有新的数据，结束。")
        return 0

    # 根据是否使用群机器人且格式为 markdown 来选择消息格式（仅展示 jobcode）
    use_robot = False
    use_markdown = False
    msg = None
    if "robot" in cfg and cfg["robot"].get("webhook"):
        use_robot = True
        fmt = cfg["robot"].get("format") or "markdown"
        if fmt.lower() == "markdown" and 'compose_jobcode_markdown' in globals():
            use_markdown = True
            msg = compose_jobcode_markdown(rows, args.preview)
    if msg is None:
        msg = compose_jobcode_text(rows, args.preview)
    if not msg:
        print("消息内容为空，结束。")
        return 0

    if args.dry_run:
        # Python 2 下 msg 是 unicode，这里编码为 UTF-8 便于终端显示；Python 3 直接使用 str
        if sys.version_info[0] == 2:
            try:
                preview_text = msg.encode("utf-8")
            except Exception:
                preview_text = msg
        else:
            preview_text = msg
        print("干跑模式：将要发送的消息如下\n" + preview_text)
    else:
        # 优先使用群机器人（如果配置了 webhook），否则使用应用接口
        if use_robot:
            if use_markdown:
                from wecom_robot_py2 import send_markdown as robot_send_md
                ok = robot_send_md(cfg["robot"]["webhook"], msg)
            else:
                from wecom_robot_py2 import send_text as robot_send_text
                ok = robot_send_text(cfg["robot"]["webhook"], msg, cfg["robot"].get("mentioned_list"))
            if ok:
                print("企业微信群机器人消息已发送成功。")
        else:
            from wecom_client_py2 import get_access_token, send_text
            token = get_access_token(cfg["wecom"]["corpid"], cfg["wecom"]["corpsecret"])
            ok = send_text(token, cfg["wecom"]["agentid"], cfg["wecom"]["touser"], msg)
            if ok:
                print("企业微信应用消息已发送成功。")

    return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
def compose_jobcode_text(rows, max_preview):
    """
<<<<<<< Updated upstream
    组织基于 jobcode 的文本消息：显示总数与前 max_preview 个 jobcode。
    返回：字符串
=======
    小白版说明：组装“文本消息”，只展示 jobcode。

    - 做什么：显示总数，并列出前 max_preview 个 jobcode
    - 为什么：你希望只要有数据就推送 jobcode 内容
    - 返回：字符串；无数据时返回 None
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    组织基于 jobcode 的 Markdown 消息：显示总数与前 max_preview 个 jobcode。
    返回：字符串（Markdown）
=======
    小白版说明：组装“Markdown 消息”，只展示 jobcode（群机器人更好看）。

    - 做什么：显示总数为二级标题，并列出前 max_preview 个 jobcode
    - 为什么：你希望只要有数据就推送 jobcode 内容
    - 返回：字符串（Markdown）；无数据时返回 None
>>>>>>> Stashed changes
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
