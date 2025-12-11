# -*- coding: utf-8 -*-
"""
去重状态管理（Python 2.7 兼容）

功能说明：
- 我们不希望重复给同一条数据发消息，因此需要记录“上次处理到哪个主键 id”。
- 这里把这个状态保存在一个本地 JSON 文件里，简单可靠，易于迁移。
"""

import os
import json


def ensure_dir(path):
    """
    确保目录存在。如果不存在就创建。
    参数：path 为目录路径。
    """
    if not os.path.isdir(path):
        os.makedirs(path)


def load_last_id(state_path):
    """
    从 JSON 文件读取上次已处理的最大主键 id。

    参数：
    - state_path：状态文件路径，例如 "state/last_seen.json"。

    返回：
    - 整数 id；如果文件不存在或格式异常，返回 0（表示从头开始）。
    """
    try:
        if not os.path.isfile(state_path):
            return 0
        with open(state_path, "r") as f:
            data = json.load(f)
            return int(data.get("last_id", 0))
    except Exception:
        return 0


def save_last_id(state_path, last_id):
    """
    把最新的最大主键 id 写入 JSON 文件，便于下次从这个位置继续。

    参数：
    - state_path：状态文件路径
    - last_id：整数 id
    """
    dir_path = os.path.dirname(state_path) or "."
    ensure_dir(dir_path)
    with open(state_path, "w") as f:
        json.dump({"last_id": int(last_id)}, f)

