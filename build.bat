@echo off
echo =========================================
echo  GraFix build
echo =========================================

python -m PyInstaller --noconfirm --onefile --windowed ^
    --name GraFix ^
    --add-data "GraFix1.ui;." ^
    --add-data "success.ui;." ^
    --add-data "config/config.json;config" ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo Copying config folder next to exe...
if not exist dist\config mkdir dist\config
copy /Y config\config.json dist\config\config.json

echo.
echo =========================================
echo  BUILD COMPLETE
echo  Exe:    dist\GraFix.exe
echo  Config: dist\config\config.json
echo =========================================
echo  Szerkesztheto config: dist\config\config.json
echo =========================================
pause
