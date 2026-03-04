@echo off
echo =========================================
echo  GraFix build
echo =========================================

python create_icon.py
python -m PyInstaller --noconfirm --onefile --windowed ^
    --icon "assets/icon.ico" ^
    --name GraFix ^
    --add-data "GraFix1.ui;." ^
    --add-data "success.ui;." ^
    --add-data "config/config.json;config" ^
    --hidden-import Crypto ^
    --hidden-import Crypto.Hash ^
    --hidden-import Crypto.Hash.MD4 ^
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
