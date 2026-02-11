@echo off
chcp 65001 > nul
REM 获取 bat 文件所在目录的父目录（即项目根目录）
set PROJECT_DIR=%~dp0..
cd /d "%PROJECT_DIR%"
python python_tool\local_build.py
pause