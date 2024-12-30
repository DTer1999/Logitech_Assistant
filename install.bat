@echo off
:: ============================================================================
:: Logitech Assistant 安装脚本
:: 作者：DTer1999
:: 项目地址：https://github.com/DTer1999/Logitech_Assistant
:: 邮箱：hshm1999@foxmail.com
:: ============================================================================

:: 检查虚拟环境是否存在
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
) else (
    echo 虚拟环境已存在
)

:: 激活虚拟环境
call venv\Scripts\activate

:: 检查是否已安装依赖（以某个关键包为例，比如 PyQt5）
python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo 安装依赖...
    pip install -r requirements.txt
) else (
    echo 依赖已安装
)

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
        --name "Logitech_Assistant" ^
        --windowed ^
        --icon=resources/assets/2.ico ^
        --add-data "resources;resources" ^
        --add-data "temp;temp" ^
        --add-data "tests;tests" ^
        --noconfirm ^
        src\main.py

    :: 复制必要的文件到 dist 目录
    echo 复制资源文件...
    xcopy /y /s resources "dist\Logitech_Assistant\resources\"
    xcopy /y /s temp "dist\Logitech_Assistant\temp\"
    xcopy /y /s tests "dist\Logitech_Assistant\tests\"

    echo 打包完成！
) else (
    echo 跳过打包步骤
)

pause
