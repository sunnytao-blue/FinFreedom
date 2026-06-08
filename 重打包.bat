@echo off
cd /d "%~dp0"

echo.
echo ================================
echo   财务自由评估 - 重新打包工具
echo ================================
echo.

echo [1/2] 关闭正在运行的程序...
taskkill /f /im 财务自由评估.exe >nul 2>&1

echo [2/2] 开始打包...
python -m PyInstaller --clean --noconfirm FinFreedom.spec

if %errorlevel% equ 0 (
    echo.
    echo ================================
    echo   打包完成！
    echo   输出: dist\财务自由评估\
    echo ================================
) else (
    echo.
    echo 打包失败，请检查上方错误信息。
)

pause
