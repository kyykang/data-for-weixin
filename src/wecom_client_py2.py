# -*- coding: utf-8 -*-
"""
企业微信发送客户端（Python 2.7 兼容）

功能说明（用小白能懂的话）：
- 先用企业ID（corpid）和应用密钥（corpsecret）去企业微信拿一个临时的令牌（access_token）。
- 再用这个令牌，把我们要发的文本消息，发送到指定的用户（touser）或部门（toparty）。
- 这里只实现最常用的文本消息发送，足够满足“查询有结果就提醒”的需求。
"""

import json
try:
    import urllib2  # Python 2
except Exception:
    # Python 3 兼容导入（用于本地干跑调试）
    import urllib.request as urllib2


def get_access_token(corpid, corpsecret, timeout=8):
    """
    用企业ID和应用密钥，向企业微信请求 access_token。

    参数：
    - corpid：企业ID（字符串）
    - corpsecret：应用密钥（字符串）
    - timeout：网络请求超时时间（秒）

    返回：
    - 成功时返回 access_token 字符串；失败时抛出异常。
    """
    url = (
        "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + corpsecret
    )
    resp = urllib2.urlopen(url, timeout=timeout)
    body = resp.read()
    data = json.loads(body)
    if data.get("errcode") == 0 and "access_token" in data:
        return data["access_token"]
    raise Exception("Get access_token failed: errcode=%s errmsg=%s" % (data.get("errcode"), data.get("errmsg")))


def send_text(access_token, agentid, touser, content, timeout=8):
    """
    发送文本消息到企业微信。

    参数：
    - access_token：调用接口用的令牌字符串（调用 get_access_token 获得）
    - agentid：企业微信应用的 AgentID（整数或字符串）
    - touser：接收人账号（多个用 | 分隔），示例："zhangsan|lisi"
    - content：文本消息内容（字符串）
    - timeout：网络请求超时时间（秒）

    返回：
    - True 表示发送成功；否则抛出异常。
    """
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + access_token
    payload = {
        "touser": touser,
        "agentid": int(agentid),
        "msgtype": "text",
        "text": {"content": content},
        "safe": 0,
    }
    req = urllib2.Request(url, data=json.dumps(payload))
    req.add_header("Content-Type", "application/json")
    resp = urllib2.urlopen(req, timeout=timeout)
    body = resp.read()
    data = json.loads(body)
    if data.get("errcode") == 0:
        return True
    raise Exception("Send message failed: errcode=%s errmsg=%s" % (data.get("errcode"), data.get("errmsg")))
