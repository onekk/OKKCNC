@echo off
set DIR=%~dp0
set DIR=%DIR%OKKCNC\
set PYTHONPATH=%DIR%lib;%DIR%plugins;%PYTHONPATH%
cd %~dp0
start python -m OKKCNC
