@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0server-ops.ps1" setup %*
