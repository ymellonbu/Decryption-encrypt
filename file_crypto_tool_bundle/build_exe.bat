@echo off
REM 빌드를 위해 PyInstaller가 필요합니다: pip install pyinstaller
pyinstaller --onefile --windowed --name FileCryptoTool file_crypto_tool.py
pause
