@echo off
REM ============================================================================
REM Logitech_Assistant ��װ�ű�
REM ���ߣ�DTer1999
REM ��Ŀ��ַ��https://github.com/DTer1999/Logitech_Assistant
REM ���䣺hshm1999@foxmail.com
REM ============================================================================

:: ��װ����������
pip install -e .

:: ѯ���Ƿ���Ҫ���´��
set /p choice=�Ƿ���Ҫ���´������(Y/N): 
if /i "%choice%"=="Y" (
    :: ��ȡ�汾�ź�Ӧ������
    for /f "tokens=*" %%i in ('python -c "from src import __version__; print(__version__)"') do set VERSION=%%i
    for /f "tokens=*" %%i in ('python -c "from src import __app_name__; print(__app_name__)"') do set APP_NAME=%%i

    :: ɾ���ɵĹ����ļ�
    echo ����ɵĹ����ļ�...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul

    :: ʹ�� PyInstaller ���
    echo ��ʼ���...
    pyinstaller ^
        --name "Logitech_Assistant" ^
        --windowed ^
        --icon=resources/assets/2.ico ^
        --add-data "resources;resources" ^
        --add-data "temp;temp" ^
        --add-data "tests;tests" ^
        --noconfirm ^
        src\main.py

    :: ���Ʊ�Ҫ���ļ��� dist Ŀ¼
    echo ������Դ�ļ�...
    xcopy /y /s resources "dist\Logitech_Assistant\resources\"
    xcopy /y /s temp "dist\Logitech_Assistant\temp\"
    xcopy /y /s tests "dist\Logitech_Assistant\tests\"

    echo �����ɣ�
) else (
    echo �����������
)

pause
