@echo off
REM ============================================================================
REM Logitech_Assistant 安装脚本
REM 作者：DTer1999
REM 项目地址：https://github.com/DTer1999/Logitech_Assistant
REM 邮箱：hshm1999@foxmail.com
REM ============================================================================

:: 安装包及其依赖
pip install -e .

:: 获取版本号和应用名称
for /f "tokens=*" %%i in ('python -c "from src import __version__, __app_name__; print(__version__)"') do set VERSION=%%i
for /f "tokens=*" %%i in ('python -c "from src import __app_name__; print(__app_name__)"') do set APP_NAME=%%i

:: 询问是否需要重新打包
set /p choice=是否需要重新打包程序？(Y/N): 
if /i "%choice%"=="Y" (
    :: 删除旧的构建文件
    echo 清理旧的构建文件...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul

    :: 使用 PyInstaller 打包
    echo 开始打包...
    pyinstaller ^
        --name "%APP_NAME%_v%VERSION%" ^
        --windowed ^
        --icon=resources/assets/2.ico ^
        --add-data "resources;resources" ^
        --add-data "temp;temp" ^
        --add-data "tests;tests" ^
        --noconfirm ^
        src\main.py

    :: 复制必要的文件到 dist 目录
    echo 复制资源文件...
    xcopy /y /s resources "dist\%APP_NAME%_v%VERSION%\resources\"
    xcopy /y /s temp "dist\%APP_NAME%_v%VERSION%\temp\"
    xcopy /y /s tests "dist\%APP_NAME%_v%VERSION%\tests\"

    echo 打包完成！
) else (
    echo 跳过打包步骤
)

pause
