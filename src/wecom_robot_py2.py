# -*- coding: utf-8 -*-
"""
企业微信群机器人客户端（Python 2.7 兼容）

用小白能懂的话：
- 企业微信的“群机器人”提供一个 webhook 地址，像一个“邮箱收件地址”。
- 我们把要发的文本内容，用 HTTP POST 的方式提交到这个地址，群里就会收到消息。
- 机器人不需要 corpid/agentid，只需要你在群里创建的 webhook URL。
"""

import json
import sys
try:
    import urllib2  # Python 2
except Exception:
    import urllib.request as urllib2  # Python 3 调试兼容


def send_text(webhook_url, content, mentioned_list=None, timeout=8):
    """
    通过群机器人发送文本消息。

    参数：
    - webhook_url：群机器人提供的完整 webhook 地址（包含 ?key=...）。
    - content：文本消息内容（字符串）。
    - mentioned_list：被@的成员列表（如 ["@all", "zhangsan"]），可选。
    - timeout：网络超时秒数。

    返回：
    - True 表示发送成功；失败抛出异常。
    """
    payload = {"msgtype": "text", "text": {"content": content}}
    if mentioned_list:
        payload["text"]["mentioned_list"] = mentioned_list
    data_bytes = json.dumps(payload)
    if sys.version_info[0] >= 3:
        data_bytes = data_bytes.encode("utf-8")
    req = urllib2.Request(webhook_url, data=data_bytes)
    req.add_header("Content-Type", "application/json")
    resp = urllib2.urlopen(req, timeout=timeout)
    body = resp.read()
    data = json.loads(body)
    # 机器人返回 {"errcode":0,"errmsg":"ok"}
    if data.get("errcode") == 0:
        return True
    raise Exception("Robot send failed: errcode=%s errmsg=%s" % (data.get("errcode"), data.get("errmsg")))


def send_markdown(webhook_url, content, timeout=8):
    """
    通过群机器人发送 Markdown 消息。

    参数：
    - webhook_url：群机器人完整地址。
    - content：Markdown 文本内容。
    - timeout：网络超时秒数。
    """
    payload = {"msgtype": "markdown", "markdown": {"content": content}}
    data_bytes = json.dumps(payload)
    if sys.version_info[0] >= 3:
        data_bytes = data_bytes.encode("utf-8")
    req = urllib2.Request(webhook_url, data=data_bytes)
    req.add_header("Content-Type", "application/json")
    resp = urllib2.urlopen(req, timeout=timeout)
    body = resp.read()
    data = json.loads(body)
    if data.get("errcode") == 0:
        return True
    raise Exception("Robot send failed: errcode=%s errmsg=%s" % (data.get("errcode"), data.get("errmsg")))
