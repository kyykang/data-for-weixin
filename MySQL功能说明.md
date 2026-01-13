# MySQL 查询功能说明

## 功能概述

新增了 MySQL 数据库查询功能，用于查询推送失败的项目。

### 查询逻辑
- **SQL 语句**：`SELECT field0001, field0045 FROM formmain_1559 WHERE field0045='2'`
- **查询条件**：field0045 = '2'（推送失败标记）
- **返回字段**：field0001（项目名称）

### 推送消息
- **标题**：以下项目推送不成功
- **内容**：列出所有 field0001 的值

## 配置方法

### 1. 安装 MySQL 驱动

在虚拟环境中安装：

```bash
# 激活虚拟环境
source /opt/venv/py3/bin/activate

# 安装 pymysql
pip install pymysql

# 退出虚拟环境
deactivate
```

### 2. 配置数据库连接

编辑 `/opt/data-for-weixin/config/config.ini`：

```ini
[wecom]
corpid=你的企业ID
corpsecret=你的应用密钥
agentid=你的应用AgentID
touser=接收人用户ID

[db]
driver=mysql
host=10.250.120.204
port=3306
database=你的数据库名
user=root
password=你的密码

[robot]
webhook=你的群机器人webhook
mentioned_list=@all
format=markdown
```

### 3. 测试运行

```bash
# 干跑测试（不发送消息）
VENV=/opt/venv/py3 ENTRY=/opt/data-for-weixin/src/main_py2.py /opt/data-for-weixin/run_py3.sh --config /opt/data-for-weixin/config/config.ini --dry-run

# 真实运行
VENV=/opt/venv/py3 ENTRY=/opt/data-for-weixin/src/main_py2.py /opt/data-for-weixin/run_py3.sh --config /opt/data-for-weixin/config/config.ini
```

## 消息格式

### 文本格式
```
以下项目推送不成功
——
项目名称1
项目名称2
项目名称3
更多...（已省略 X 条）
```

### Markdown 格式（群机器人）
```markdown
## 以下项目推送不成功

- 项目名称1
- 项目名称2
- 项目名称3

> 更多...（已省略 X 条）
```

## 部署到生产环境

### 方式一：通过 Git 更新（推荐）

```bash
# 1. 登录服务器
ssh user@server

# 2. 进入项目目录
cd /opt/data-for-weixin

# 3. 备份配置文件
cp config/config.ini config/config.ini.backup

# 4. 拉取最新代码
git pull origin main

# 5. 恢复配置文件
cp config/config.ini.backup config/config.ini

# 6. 安装 MySQL 驱动
source /opt/venv/py3/bin/activate
pip install pymysql
deactivate

# 7. 更新配置文件
vi config/config.ini
# 修改 driver=mysql 并填写数据库信息

# 8. 测试运行
VENV=/opt/venv/py3 ENTRY=/opt/data-for-weixin/src/main_py2.py /opt/data-for-weixin/run_py3.sh --config /opt/data-for-weixin/config/config.ini --dry-run
```

### 方式二：手动上传文件

```bash
# 1. 在本地打包需要更新的文件
tar -czf update.tar.gz src/db_client_py2.py src/main_py2.py config/config.ini.example

# 2. 上传到服务器
scp update.tar.gz user@server:/tmp/

# 3. 登录服务器并解压
ssh user@server
cd /opt/data-for-weixin
tar -xzf /tmp/update.tar.gz

# 4. 安装 MySQL 驱动
source /opt/venv/py3/bin/activate
pip install pymysql
deactivate

# 5. 更新配置文件
vi config/config.ini

# 6. 测试运行
VENV=/opt/venv/py3 ENTRY=/opt/data-for-weixin/src/main_py2.py /opt/data-for-weixin/run_py3.sh --config /opt/data-for-weixin/config/config.ini --dry-run
```

## 定时任务

现有的定时任务无需修改，会自动使用新的 MySQL 查询功能：

```bash
0 * * * * VENV=/opt/venv/py3 ENTRY=/opt/data-for-weixin/src/main_py2.py /opt/data-for-weixin/run_py3.sh --config /opt/data-for-weixin/config/config.ini >> /var/log/data-for-weixin/run.log 2>&1
```

## 验证

### 1. 检查 MySQL 驱动

```bash
source /opt/venv/py3/bin/activate
python -c "import pymysql; print('pymysql OK')"
deactivate
```

### 2. 测试数据库连接

```bash
mysql -h 10.250.120.204 -P 3306 -u root -p -e "SELECT COUNT(*) FROM formmain_1559 WHERE field0045='2';"
```

### 3. 查看日志

```bash
tail -f /var/log/data-for-weixin/run.log
```

## 故障排查

### 问题 1：找不到 MySQL 驱动

**错误信息**：`未检测到可用的 MySQL 驱动`

**解决方法**：
```bash
source /opt/venv/py3/bin/activate
pip install pymysql
deactivate
```

### 问题 2：连接数据库失败

**错误信息**：`Can't connect to MySQL server`

**检查项**：
- 数据库地址和端口是否正确
- 用户名和密码是否正确
- 防火墙是否允许连接
- 数据库服务是否运行

### 问题 3：查询无结果

**可能原因**：
- 表名或字段名不正确
- 没有符合条件的数据（field0045='2'）

**验证方法**：
```bash
mysql -h 10.250.120.204 -u root -p -e "SELECT field0001, field0045 FROM formmain_1559 WHERE field0045='2';"
```

## 注意事项

1. **密码安全**：配置文件包含数据库密码，确保文件权限为 600
   ```bash
   chmod 600 /opt/data-for-weixin/config/config.ini
   ```

2. **虚拟环境**：必须在虚拟环境中安装 pymysql，不要在系统 Python 中安装

3. **原有功能保持不变**：SQLite 和 SQL Server 查询功能不受影响

4. **定时任务无需修改**：使用相同的运行方式，只需修改配置文件

## 切换数据库

可以通过修改配置文件的 `driver` 参数切换数据库：

```ini
# 使用 SQLite
[db]
driver=sqlite
sqlite_path=./data/demo.sqlite

# 使用 SQL Server
[db]
driver=sqlserver
host=10.250.122.101
port=1433
database=U8CLOUD202102
user=sa
password=******

# 使用 MySQL
[db]
driver=mysql
host=10.250.120.204
port=3306
database=your_database
user=root
password=******
```

修改后无需重启，下次定时任务执行时自动生效。
