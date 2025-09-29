@echo off
REM =====================================================
REM  INICIADOR - Whisper GUI v3.0
REM =====================================================

echo.
echo ===================================================
echo   WHISPER GUI v3.0 - Multi-Provider Edition
echo ===================================================
echo.

REM Verificación rápida de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado
    echo.
    echo Por favor ejecuta primero: INSTALAR.bat
    echo.
    pause
    exit /b 1
)

REM Usar core_fixed.py si existe y core.py no
if exist "core_fixed.py" (
    if not exist "core.py" (
        echo Actualizando core.py con versión corregida...
        copy /Y core_fixed.py core.py >nul
    )
)

REM Verificar que existen los archivos necesarios
if not exist "whisper_gui.py" (
    echo ERROR: No se encuentra whisper_gui.py
    pause
    exit /b 1
)

if not exist "core.py" (
    echo ERROR: No se encuentra core.py
    echo.
    echo Ejecuta INSTALAR.bat primero
    pause
    exit /b 1
)

echo Iniciando aplicación...
echo.

REM Intentar iniciar con python
python whisper_gui.py

REM Si falla, mostrar error
if %errorlevel% neq 0 (
    echo.
    echo ===================================================
    echo   ERROR AL INICIAR
    echo ===================================================
    echo.
    echo Posibles soluciones:
    echo 1. Ejecuta INSTALAR.bat para instalar dependencias
    echo 2. Instala Groq: pip install groq
    echo 3. Verifica con: python test_funcionalidad.py
    echo.
    pause
)
