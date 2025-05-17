@echo off
echo 开始编译库文件...
python build_libs.py
if errorlevel 1 (
    echo 编译失败！
    pause
    exit /b 1
)
echo 编译完成！
pause 