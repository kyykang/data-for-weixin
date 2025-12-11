# 数据库查询并推送到企业微信（Python 2.7 版）

## 目标
- 定时或手动查询数据库（入门用 SQLite，本地即可调试）。
- 查询到满足条件的数据时，自动向企业微信应用推送消息。
- 在 Linux 环境使用 Python 2.7 部署，macOS 可本地调试。

## 目录结构
- `src/`：Python 2.7 脚本源码
- `config/config.ini`：配置文件（按示例填写）
- `data/demo.sqlite`：示例数据库文件（可自动初始化）
- `state/last_seen.json`：记录上次已通知的主键 id，避免重复推送
- `logs/`：日志目录（可选）

## 快速开始（macOS 本地干跑）
1. 复制示例配置：
 
   - 默认使用 SQLite 数据库：`data/demo.sqlite`
2. 运行脚本（干跑模式不真正发消息，只打印将要发送的内容）：
   - 如果你的系统只有 Python3，可先试运行：
     ```
     python3 src/main_py2.py --dry-run --init-demo
     ```
     注：代码按 Python 2.7 编写，干跑模式主要验证逻辑与输出。
3. 查看输出：应能看到“将要发送的消息”以及查询到的示例数据摘要。

## Linux 部署（Python 2.7）
1. 确认 Python 版本：
   ```
   python2 --version
   ```
2. 准备配置文件：
   - 复制 `config/config.ini.example` 为 `config/config.ini` 并填写参数。
3. 首次运行（可初始化示例库并进行一次查询与推送）：
   ```
   python2 src/main_py2.py --init-demo
   ```
4. 定时运行（crontab）：
   - 编辑定时任务：`crontab -e`
   - 每分钟执行一次示例：
     ```
     * * * * * /usr/bin/python2 /path/to/project/src/main_py2.py >> /path/to/project/logs/run.log 2>&1
     ```
   - 根据需要调整频率与日志路径。

## 配置说明（config.ini）
```
[wecom]
corpid=你的企业ID
corpsecret=你的应用密钥
agentid=你的应用AgentID
touser=接收人用户ID（可多个用竖线分隔）

[db]
driver=sqlite
sqlite_path=./data/demo.sqlite

[robot]
# 使用企业微信群机器人推送（推荐用于群通知）
# webhook：在群设置里创建机器人后复制的完整地址
webhook=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
# mentioned_list：可选，被@的成员，支持 @all；多个用 | 分隔
mentioned_list=@all
# format：消息格式，可选 markdown 或 text（默认 markdown）。
format=markdown

[message]
# 可选：自定义消息模板（支持占位符）
# 可用占位符：{count} {id} {title} {created_at} {omitted}
title_text=数据库告警：检测到 {count} 条新数据
item_text=id={id}，{title}（{created_at}）
footer_text=更多...（已省略 {omitted} 条）
title_markdown=## 数据库告警：检测到 {count} 条新数据
item_markdown=- id={id} ｜ {title} ｜ {created_at}
footer_markdown=> 更多...（已省略 {omitted} 条）
```
- 如果后续使用 MySQL/PostgreSQL，可拓展 `driver` 和连接参数；当前示例专注 SQLite 以便快速联调。

## 安全与说明
- 不要把真实密钥提交到仓库；`config.ini` 仅在你的服务器本地保存。
- 脚本默认只读查询，不对业务数据进行任何修改。

## 消息规则
- 查询到新数据时：发送一条文本消息，包含总数与前若干条摘要。
- 去重策略：用 `state/last_seen.json` 记录上一次处理的最大主键 id，只处理新插入的数据。

## 使用群机器人
- 如果 `config.ini` 中配置了 `[robot]` 的 `webhook`，将优先通过群机器人发送消息；否则使用企业微信应用接口。
- 群机器人无需 `corpid/agentid`，只需 `webhook`；可通过 `mentioned_list` 实现 `@all` 或指定成员提醒。
- 当 `format=markdown` 时，消息以 Markdown 渲染；如需 `@成员`，请使用 `format=text` 并设置 `mentioned_list`。
 - 如需自定义文本内容，请在 `[message]` 段修改模板；模板中的占位符会被实际数据替换。

## 常见问题
- 企业微信未收到消息：检查 `corpid/corpsecret/agentid/touser` 是否正确，确保应用有“发消息”权限。
- Python 2.7 SSL 问题：服务器需支持现代 TLS；如遇证书报错，升级系统证书或使用离线网络策略。
- 数据库驱动：示例用 SQLite，自带驱动即可运行；若切换到 MySQL，需要安装 `MySQLdb`/`pymysql`。
