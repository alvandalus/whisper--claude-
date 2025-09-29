"""
Script de configuración para Whisper GUI
Verifica e instala todas las dependencias necesarias
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def check_ffmpeg():
    """Verificar si FFmpeg está instalado"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print("✓ FFmpeg está instalado")
        return True
    except FileNotFoundError:
        print("✗ FFmpeg no está instalado")
        print("Por favor instale FFmpeg:")
        print("  Windows: choco install ffmpeg")
        print("  Mac: brew install ffmpeg")
        print("  Linux: sudo apt install ffmpeg")
        return False

def setup_venv():
    """Crear y configurar entorno virtual"""
    venv_path = Path('.venv')
    
    if not venv_path.exists():
        print("Creando entorno virtual...")
        venv.create(venv_path, with_pip=True)
    
    # Activar venv
    if sys.platform == 'win32':
        python = venv_path / 'Scripts' / 'python.exe'
    else:
        python = venv_path / 'bin' / 'python'
    
    # Instalar dependencias
    print("Instalando dependencias...")
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', 'requirements.txt'])

def main():
    """Verificar e instalar todo lo necesario"""
    print("=== Configuración de Whisper GUI ===\n")
    
    # 1. Verificar Python
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}")
    if sys.version_info < (3, 8):
        print("✗ Se requiere Python 3.8 o superior")
        return
    
    # 2. Verificar FFmpeg
    if not check_ffmpeg():
        return
    
    # 3. Configurar entorno virtual y dependencias
    setup_venv()
    
    print("\n=== Configuración completada ===")
    print("Puede ejecutar la aplicación con:")
    print("  1. Doble clic en INICIAR.bat")
    print("  2. O desde VS Code: whisper_gui.py > Run")

if __name__ == '__main__':
    main()