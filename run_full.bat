@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================================================
REM 全量测试启动脚本 (每周自动运行)
REM 功能: 1. 启动 Flask 服务器 (如未启动)  2. 运行全量测试  3. 保存报告
REM ========================================================================

echo ============================================================
echo   全量接口测试 - 每周检查所有接口
echo   时间: %date% %time%
echo ============================================================
echo.

cd /d "%~dp0"

REM 设置虚拟环境路径 (如果使用 venv)
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    echo [信息] 使用虚拟环境 Python
) else (
    set "PYTHON_CMD=python"
    echo [信息] 使用系统 Python
)

REM 检查服务器是否已启动
echo [检查] 检查 Flask 服务器状态...
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:5000/ >nul 2>&1
if %errorlevel%==0 (
    echo [OK] 服务器已在运行
) else (
    echo [启动] 服务器未启动，正在启动 Flask 应用...
    start "Flask-Server" cmd /c ""%PYTHON_CMD%" app.py"
    echo [等待] 等待服务器就绪 (约 5 秒)...
    timeout /t 5 /nobreak >nul

    REM 再次检查
    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:5000/ >nul 2>&1
    if not %errorlevel%==0 (
        echo [重试] 服务器仍未就绪，再等待 5 秒...
        timeout /t 5 /nobreak >nul
    )
)

echo.
echo ============================================================
echo   开始运行全量接口测试
echo   (测试可能需要几分钟，请耐心等待)
echo ============================================================
echo.

REM 运行测试，并将输出同时保存到文件和控制台
set "REPORT_FILE=%~dp0reports\full_test_%date:/=-%_%time::=-%.txt"
set "REPORT_FILE=!REPORT_FILE: =0!"

REM 创建报告目录
if not exist "reports" mkdir reports

"%PYTHON_CMD%" run_full.py
set TEST_EXIT_CODE=%errorlevel%

echo.
echo ============================================================
if %TEST_EXIT_CODE%==0 (
    echo   ✅ 全量测试通过
    echo   测试结果已保存: reports\ 目录
) else (
    echo   ❌ 全量测试发现问题 (错误代码: %TEST_EXIT_CODE%)
    echo   请查看上方输出了解详情
)
echo ============================================================
echo.

REM 保存退出码到文件，供调度任务读取
echo %TEST_EXIT_CODE% > "reports\full_test_last_exit_code.txt"

REM 无人值守模式（由计划任务调用，传参数 auto）时跳过 pause
if "%~1" == "auto" goto end_batch
echo.
echo 按任意键关闭此窗口...
pause >nul

:end_batch
endlocal
exit /b %TEST_EXIT_CODE%
