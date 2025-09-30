@echo off
REM Script de inicio para Transcriptor Pro (Windows)
REM Activa el entorno virtual y ejecuta la aplicación

echo ========================================
echo  Transcriptor Pro v1.0
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist ".venv" (
    echo ERROR: No se encontro el entorno virtual
    echo.
    echo Por favor ejecuta primero:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activar entorno virtual
echo Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Verificar que FFmpeg esta instalado
where ffmpeg >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ADVERTENCIA: FFmpeg no esta instalado
    echo El procesamiento de audio no funcionara correctamente
    echo.
    echo Instala FFmpeg con:
    echo   choco install ffmpeg
    echo.
    pause
)

REM Ejecutar la aplicacion
echo Iniciando Transcriptor Pro...
echo.
python -m src.main

REM Si hay error, pausar para ver el mensaje
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: La aplicacion termino con errores
    pause
)
