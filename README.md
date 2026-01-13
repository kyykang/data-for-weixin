# 数据库查询并推送到企业微信（Python 2.7 版）

## 目标
- 定时或手动查询数据库（支持 SQLite、SQL Server、MySQL）。
- 查询到满足条件的数据时，自动向企业微信应用推送消息。
- 支持同时查询多个数据库，合并结果后统一推送。
- 在 Linux 环境使用 Python 2.7/3.x 部署，macOS 可本地调试。

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

### 基础配置
```ini
[wecom]
corpid=你的企业ID
corpsecret=你的应用密钥
agentid=你的应用AgentID
touser=接收人用户ID（可多个用竖线分隔）

[db]
# 主数据库配置
driver=sqlserver  # 可选：sqlite、sqlserver、mysql
sqlite_path=./data/demo.sqlite  # SQLite 使用
host=10.250.122.101  # SQL Server/MySQL 使用
port=1433  # SQL Server 默认 1433，MySQL 默认 3306
database=U8CLOUD202102
user=sa
password=******

[db_mysql]
# MySQL 数据库配置（可选，独立配置节）
# 可与 [db] 同时使用，实现多数据库查询
enabled=true  # 是否启用 MySQL 查询
host=10.250.120.204
port=3306
database=your_database
user=root
password=******

[robot]
# 使用企业微信群机器人推送（推荐用于群通知）
webhook=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
mentioned_list=@all  # 可选，被@的成员，多个用 | 分隔
format=markdown  # 消息格式：markdown 或 text

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

### 多数据库配置说明

**同时使用 SQL Server 和 MySQL（推荐）**
```ini
[db]
driver=sqlserver
host=10.250.122.101
port=1433
database=U8CLOUD202102
user=sa
password=******

[db_mysql]
enabled=true
host=10.250.120.204
port=3306
database=your_database
user=root
password=******
```

**只使用 MySQL**
```ini
[db]
driver=mysql
host=10.250.120.204
port=3306
database=your_database
user=root
password=******
```

**禁用 MySQL 查询**
```ini
[db_mysql]
enabled=false
```

## 数据库驱动安装

### SQLite
- Python 自带，无需额外安装

### SQL Server
建议安装以下任一驱动（Python 2.7/3.x 兼容）：
- `pymssql`（推荐，依赖 FreeTDS）：
  ```bash
  pip install pymssql
  ```
- `pyodbc`（需要安装 Microsoft ODBC Driver for SQL Server）：
  ```bash
  pip install pyodbc
  ```
- 在 Linux 上安装 ODBC 驱动示例（Ubuntu）：
  ```bash
  sudo apt-get install msodbcsql17 unixodbc-dev
  ```

### MySQL
安装以下任一驱动：
- `pymysql`（推荐，纯 Python 实现）：
  ```bash
  pip install pymysql
  ```
- `MySQL-python`（需要 MySQL 客户端库）：
  ```bash
  pip install MySQL-python
  ```

### 虚拟环境安装示例
```bash
# 激活虚拟环境
source /opt/venv/py3/bin/activate

# 安装驱动
pip install pymysql pymssql

# 退出虚拟环境
deactivate
```
- 不要把真实密钥提交到仓库；`config.ini` 仅在你的服务器本地保存。
- 脚本默认只读查询，不对业务数据进行任何修改。

## 功能特性

### 多数据库支持
- **SQLite**：本地调试，无需额外配置
- **SQL Server**：查询重复 jobcode
- **MySQL**：查询推送失败的项目（field0045='2'）
- **多数据库同时查询**：可同时配置 SQL Server 和 MySQL，合并结果后统一推送

### 消息推送
- **企业微信应用**：通过 corpid/agentid 推送
- **企业微信群机器人**：通过 webhook 推送（支持 @成员）
- **消息格式**：支持文本和 Markdown 两种格式
- **自定义模板**：可自定义消息标题、内容、尾部格式

### 查询日志
- 显示每个数据库的查询状态
- 显示查询结果数量
- 显示消息生成和发送状态

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

## 更多文档
- [MySQL 功能说明](MySQL功能说明.md) - MySQL 查询功能详细说明
- [功能实现完成](功能实现完成.md) - 功能实现总结和部署指南
- [更新说明](更新说明.md) - 版本更新内容和部署步骤
