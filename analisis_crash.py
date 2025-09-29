"""
Script de Análisis Post-Crash
Revisa qué pasó cuando el programa se colgó
"""

import os
from pathlib import Path
import datetime

print("=" * 70)
print("🔍 ANÁLISIS POST-CRASH - Whisper GUI")
print("=" * 70)
print()

# 1. Buscar archivos VAD
print("1. Buscando archivos VAD...")
print()

desktop = Path.home() / "Desktop"
downloads = Path.home() / "Downloads"

vad_files = []
for location in [desktop, downloads, Path.cwd()]:
    if location.exists():
        vad_files.extend(list(location.glob("**/*_vad.*")))

if vad_files:
    print(f"✓ Encontrados {len(vad_files)} archivos VAD:")
    for f in vad_files[:10]:  # Primeros 10
        size_mb = f.stat().st_size / (1024 * 1024)
        modified = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        print(f"  - {f.name}")
        print(f"    Tamaño: {size_mb:.2f} MB")
        print(f"    Modificado: {modified}")
        print(f"    Ruta: {f.parent}")
        print()
else:
    print("  ⚠ No se encontraron archivos VAD")
    print()

# 2. Buscar logs
print("2. Buscando logs de errores...")
print()

log_locations = [
    Path(os.getenv("APPDATA", Path.home())) / ".whisper4" / "app.log",
    Path.cwd() / "whisper_gui.log",
    Path.cwd() / "error.log"
]

for log_path in log_locations:
    if log_path.exists():
        print(f"✓ Log encontrado: {log_path}")
        print(f"  Tamaño: {log_path.stat().st_size} bytes")
        print()
        print("  Últimas 30 líneas:")
        print("  " + "-" * 60)
        
        try:
            lines = log_path.read_text(encoding='utf-8').splitlines()
            for line in lines[-30:]:
                print(f"  {line}")
        except:
            print("  (Error leyendo log)")
        
        print("  " + "-" * 60)
        print()

# 3. Info del sistema
print("3. Información del sistema:")
print()

import platform
import psutil

print(f"  OS: {platform.system()} {platform.release()}")
print(f"  Python: {platform.python_version()}")
print(f"  CPU: {psutil.cpu_count()} cores")
print(f"  RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
print(f"  RAM disponible: {psutil.virtual_memory().available / (1024**3):.1f} GB")
print()

# 4. Recomendaciones
print("=" * 70)
print("📋 DIAGNÓSTICO Y RECOMENDACIONES")
print("=" * 70)
print()

if vad_files:
    print("⚠️ PROBLEMA IDENTIFICADO: Procesamiento VAD")
    print()
    print("El VAD (eliminación de silencios) consume MUCHA CPU/RAM.")
    print()
    print("🔧 SOLUCIONES:")
    print()
    print("1. DESACTIVA VAD en Configuración")
    print("   → Destilda 'VAD (recortar silencios)'")
    print()
    print("2. O procesa audios más cortos")
    print("   → Divide archivos grandes antes")
    print()
    print("3. O aumenta prioridad a 'Baja'")
    print("   → Evita que bloquee el PC")
    print()

print("=" * 70)

input("\nPresiona ENTER para salir...")
