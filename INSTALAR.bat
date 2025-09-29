@echo off
REM =====================================================
REM  INSTALADOR Y VERIFICADOR - Whisper GUI v3.0
REM =====================================================

echo.
echo ===================================================
echo   WHISPER GUI v3.0 - INSTALADOR Y VERIFICADOR
echo ===================================================
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo.
    echo Por favor instala Python 3.8+ desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca la opción "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)
python --version
echo OK - Python instalado
echo.

REM Verificar FFmpeg
echo [2/4] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ADVERTENCIA: FFmpeg no está instalado
    echo.
    echo FFmpeg es necesario para procesar audio. Instálalo con:
    echo   - Chocolatey: choco install ffmpeg
    echo   - O descarga desde: https://ffmpeg.org/download.html
    echo.
    echo Continuando sin FFmpeg (limitado)...
) else (
    echo OK - FFmpeg instalado
)
echo.

REM Instalar dependencias Python
echo [3/4] Instalando dependencias Python...
echo.

REM Crear requirements_minimal.txt con solo lo esencial
echo groq>=0.4.0 > requirements_minimal.txt
echo openai>=1.0.0 >> requirements_minimal.txt

REM Instalar dependencias básicas
pip install --upgrade pip >nul 2>&1
pip install groq --no-warn-script-location
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar groq
    echo Intentando con pip3...
    pip3 install groq
)

pip install openai --no-warn-script-location 2>nul
echo.
echo OK - Dependencias instaladas
echo.

REM Verificar archivos necesarios
echo [4/4] Verificando archivos...
if not exist "whisper_gui.py" (
    echo ERROR: No se encuentra whisper_gui.py
    echo Por favor asegúrate de tener todos los archivos del proyecto.
    pause
    exit /b 1
)

if not exist "core.py" (
    if exist "core_fixed.py" (
        echo Usando core_fixed.py como core.py...
        copy /Y core_fixed.py core.py >nul
    ) else (
        echo ERROR: No se encuentra core.py
        pause
        exit /b 1
    )
)

echo OK - Archivos verificados
echo.

echo ===================================================
echo   INSTALACIÓN COMPLETADA CON ÉXITO
echo ===================================================
echo.
echo Para iniciar la aplicación, ejecuta:
echo   python whisper_gui.py
echo.
echo O simplemente haz doble clic en INICIAR.bat
echo.
echo SIGUIENTE PASO:
echo 1. Obtén tu API key gratuita de Groq en:
echo    https://console.groq.com/keys
echo.
echo 2. Configúrala en la aplicación (pestaña Configuración)
echo.
pause
