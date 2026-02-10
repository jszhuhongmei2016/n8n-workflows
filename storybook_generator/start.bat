# 快速启动脚本（Windows）

@echo off
echo ========================================
echo 动态绘本生成器 - 启动脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo [1/4] 检查后端依赖...
cd backend
if not exist venv (
    echo 创建Python虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate

if not exist venv\Lib\site-packages\fastapi (
    echo 安装后端依赖...
    pip install -r requirements.txt
)

echo.
echo [2/4] 检查前端依赖...
cd ..\frontend
if not exist node_modules (
    echo 安装前端依赖...
    call npm install
)

echo.
echo [3/4] 启动后端服务...
cd ..\backend
start "后端服务" cmd /k "venv\Scripts\activate && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo [4/4] 启动前端服务...
cd ..\frontend
start "前端服务" cmd /k "npm run dev"

echo.
echo ========================================
echo 启动完成！
echo 后端: http://localhost:8000
echo 前端: http://localhost:3000
echo API文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按任意键退出启动脚本（服务将继续运行）
pause >nul
