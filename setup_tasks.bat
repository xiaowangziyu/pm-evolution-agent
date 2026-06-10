@echo off
chcp 65001 >nul
echo ========================================
echo   创建计划任务
echo   注意: 本脚本需要以"管理员身份"运行
echo ========================================
echo.

REM 先检查是否有管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请右键点击本脚本，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo [1/2] 创建冒烟测试任务 (每天 20:00)...
schtasks /Create /F /TN "PM-SmokeTest" ^
    /TR "cmd.exe /c \"D:\pycharm\python项目\my-first-agent\run_smoke.bat\" auto" ^
    /SC DAILY /ST 20:00 /RL HIGHEST
if %errorlevel%==0 echo     OK

echo.
echo [2/2] 创建全量测试任务 (每周日 20:30)...
schtasks /Create /F /TN "PM-FullTest" ^
    /TR "cmd.exe /c \"D:\pycharm\python项目\my-first-agent\run_full.bat\" auto" ^
    /SC WEEKLY /D SUN /ST 20:30 /RL HIGHEST
if %errorlevel%==0 echo     OK

echo.
echo ========================================
echo   创建完成! 当前任务列表:
echo ========================================
schtasks /Query /TN "PM-SmokeTest" /FO LIST
echo.
schtasks /Query /TN "PM-FullTest" /FO LIST

echo.
echo 提示: 你也可以按 Win+R 输入 taskschd.msc 打开任务计划程序查看
echo.
pause
