#!/bin/bash

echo "========================================"
echo "动态绘本生成器 - 启动脚本"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python，请先安装Python 3.9+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到Node.js，请先安装Node.js 16+"
    exit 1
fi

echo "[1/4] 检查后端依赖..."
cd backend

if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -d "venv/lib/python*/site-packages/fastapi" ]; then
    echo "安装后端依赖..."
    pip install -r requirements.txt
fi

echo ""
echo "[2/4] 检查前端依赖..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo ""
echo "[3/4] 启动后端服务..."
cd ../backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

sleep 3

echo ""
echo "[4/4] 启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "启动完成！"
echo "后端: http://localhost:8000"
echo "前端: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
