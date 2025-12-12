#!/usr/bin/env bash
set -euo pipefail

# 小白版说明：
# - 这个脚本帮你用 Python3 的虚拟环境来跑项目，不会影响系统的 Python2。
# - 如果你已经有虚拟环境，把环境路径写到环境变量 VENV；没有的话，它会在项目内自动创建 .venv。
# - 默认入口脚本是 src/main_py2.py，你也可以用 ENTRY 指定别的入口。
# 使用示例：
#   1）直接运行（自动创建本地 .venv）：
#       ./run_py3.sh --dry-run --init-demo
#   2）指定服务器上的虚拟环境和入口：
#       VENV=/opt/venv/py3 ENTRY=src/main_py2.py ./run_py3.sh --dry-run

VENV_PATH="${VENV:-/opt/venv/py3}"
ENTRY_SCRIPT="${ENTRY:-src/main_py2.py}"

if [ -f "$VENV_PATH/bin/activate" ]; then
  . "$VENV_PATH/bin/activate"
else
  if command -v python3 >/dev/null 2>&1; then
    if [ ! -f ".venv/bin/activate" ]; then
      python3 -m venv .venv
    fi
    . ".venv/bin/activate"
  else
    echo "python3 未找到，请先在系统安装 Python 3（CentOS7 可用：yum install -y python3）"
    exit 1
  fi
fi

python -m pip install --upgrade pip >/dev/null 2>&1 || true
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

if [ -n "${CONFIG:-}" ]; then
  set -- --config "$CONFIG" "$@"
fi

echo "[$(date '+%F %T')] START"
python "$ENTRY_SCRIPT" "$@"
code=$?
echo "[$(date '+%F %T')] END code=$code"
exit $code
