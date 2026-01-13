#!/bin/bash
# 快速部署 MySQL 功能到生产环境
# 使用方法：bash 快速部署命令.sh

set -e

echo "=========================================="
echo "MySQL 功能部署脚本"
echo "=========================================="
echo ""

# 项目路径
PROJECT_DIR="/opt/data-for-weixin"
VENV_PATH="/opt/venv/py3"

# 1. 备份配置文件
echo "[1/6] 备份配置文件..."
if [ -f "$PROJECT_DIR/config/config.ini" ]; then
    cp "$PROJECT_DIR/config/config.ini" "$PROJECT_DIR/config/config.ini.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✓ 配置文件已备份"
else
    echo "! 配置文件不存在，跳过备份"
fi

# 2. 更新代码
echo ""
echo "[2/6] 更新代码..."
cd "$PROJECT_DIR"
if [ -d ".git" ]; then
    git pull origin main
    echo "✓ 代码已更新"
else
    echo "! 不是 Git 仓库，请手动上传文件"
    exit 1
fi

# 3. 恢复配置文件
echo ""
echo "[3/6] 恢复配置文件..."
if [ -f "$PROJECT_DIR/config/config.ini.backup."* ]; then
    LATEST_BACKUP=$(ls -t "$PROJECT_DIR/config/config.ini.backup."* | head -1)
    cp "$LATEST_BACKUP" "$PROJECT_DIR/config/config.ini"
    echo "✓ 配置文件已恢复"
fi

# 4. 安装 MySQL 驱动
echo ""
echo "[4/6] 安装 MySQL 驱动..."
source "$VENV_PATH/bin/activate"
pip install pymysql
deactivate
echo "✓ pymysql 已安装"

# 5. 提示更新配置
echo ""
echo "[5/6] 更新配置文件..."
echo "请编辑配置文件添加 MySQL 配置："
echo "  vi $PROJECT_DIR/config/config.ini"
echo ""
echo "添加以下内容："
echo "  [db]"
echo "  driver=mysql"
echo "  host=10.250.120.204"
echo "  port=3306"
echo "  database=你的数据库名"
echo "  user=root"
echo "  password=你的密码"
echo ""
read -p "按回车键继续编辑配置文件..." 
vi "$PROJECT_DIR/config/config.ini"

# 6. 测试运行
echo ""
echo "[6/6] 测试运行..."
echo "执行干跑测试..."
VENV="$VENV_PATH" ENTRY="$PROJECT_DIR/src/main_py2.py" \
  "$PROJECT_DIR/run_py3.sh" \
  --config "$PROJECT_DIR/config/config.ini" \
  --dry-run

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 检查上面的测试输出是否正确"
echo "2. 如果正确，执行真实测试："
echo "   VENV=$VENV_PATH ENTRY=$PROJECT_DIR/src/main_py2.py \\"
echo "     $PROJECT_DIR/run_py3.sh \\"
echo "     --config $PROJECT_DIR/config/config.ini"
echo ""
echo "3. 查看日志："
echo "   tail -f /var/log/data-for-weixin/run.log"
echo ""
echo "定时任务无需修改，会自动使用新功能。"
echo "=========================================="
