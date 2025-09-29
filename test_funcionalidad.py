"""
Test rápido de funcionalidad - Whisper GUI v3.0
Verifica que los componentes críticos funcionen
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("TEST DE FUNCIONALIDAD - WHISPER GUI v3.0")
print("=" * 60)
print()

# Test 1: Importaciones básicas
print("[TEST 1] Verificando importaciones Python...")
try:
    import tkinter
    print("✓ tkinter (GUI) - OK")
except ImportError:
    print("✗ tkinter NO disponible - La GUI no funcionará")
    sys.exit(1)

try:
    import json
    import datetime
    import threading
    print("✓ Módulos estándar - OK")
except ImportError as e:
    print(f"✗ Error en módulos estándar: {e}")
    sys.exit(1)

# Test 2: Verificar core.py
print("\n[TEST 2] Verificando módulo core...")
try:
    # Si core_fixed.py existe pero core.py no, copiar
    if Path("core_fixed.py").exists() and not Path("core.py").exists():
        print("  Copiando core_fixed.py a core.py...")
        import shutil
        shutil.copy("core_fixed.py", "core.py")
    
    from core import (
        AUDIO_EXT, MODEL_COSTS, PROVIDER_MAP,
        budget_get_remaining, get_provider_info,
        TranscriptionResult
    )
    print("✓ Core importado correctamente")
    print(f"  - Modelos disponibles: {len(MODEL_COSTS)}")
    print(f"  - Extensiones soportadas: {len(AUDIO_EXT)}")
except ImportError as e:
    print(f"✗ Error importando core: {e}")
    print("\nAsegúrate de que core.py existe en el mismo directorio")
    sys.exit(1)

# Test 3: Verificar APIs opcionales
print("\n[TEST 3] Verificando bibliotecas de APIs...")

groq_available = False
try:
    import groq
    print("✓ Groq API - Disponible")
    groq_available = True
except ImportError:
    print("⚠ Groq API - No instalada (pip install groq)")

openai_available = False
try:
    import openai
    print("✓ OpenAI API - Disponible")
    openai_available = True
except ImportError:
    print("⚠ OpenAI API - No instalada (pip install openai)")

whisper_available = False
try:
    import whisper
    print("✓ Whisper local - Disponible")
    whisper_available = True
except ImportError:
    print("⚠ Whisper local - No instalado (pip install openai-whisper)")

if not groq_available and not openai_available:
    print("\n✗ ERROR: Necesitas al menos una API instalada")
    print("  Recomendado: pip install groq")
    sys.exit(1)

# Test 4: Verificar FFmpeg
print("\n[TEST 4] Verificando FFmpeg...")
import subprocess
try:
    result = subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print("✓ FFmpeg instalado")
    else:
        print("⚠ FFmpeg encontrado pero con errores")
except FileNotFoundError:
    print("⚠ FFmpeg NO instalado - El procesamiento de audio será limitado")
    print("  Instala con: choco install ffmpeg (Windows)")
except Exception as e:
    print(f"⚠ Error verificando FFmpeg: {e}")

# Test 5: Verificar configuración
print("\n[TEST 5] Verificando configuración...")
try:
    config_dir = Path.home() / ".whisper4"
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Creado directorio de configuración: {config_dir}")
    else:
        print(f"✓ Directorio de configuración existe: {config_dir}")
    
    # Verificar presupuesto
    remaining = budget_get_remaining()
    print(f"✓ Presupuesto diario restante: ${remaining:.2f}")
    
except Exception as e:
    print(f"⚠ Error en configuración: {e}")

# Test 6: Verificar GUI
print("\n[TEST 6] Verificando interfaz gráfica...")
try:
    import whisper_gui
    print("✓ whisper_gui.py importado correctamente")
    
    # Verificar que la clase App existe
    if hasattr(whisper_gui, 'App'):
        print("✓ Clase App encontrada")
    else:
        print("✗ Clase App no encontrada en whisper_gui")
        
except ImportError as e:
    print(f"✗ Error importando whisper_gui: {e}")
    sys.exit(1)

# Test 7: Test de API keys configuradas
print("\n[TEST 7] Verificando API keys en entorno...")

groq_key = os.getenv('GROQ_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

if groq_key:
    print(f"✓ GROQ_API_KEY configurada ({len(groq_key)} caracteres)")
else:
    print("⚠ GROQ_API_KEY no configurada (configura en la app)")

if openai_key:
    print(f"✓ OPENAI_API_KEY configurada ({len(openai_key)} caracteres)")
else:
    print("⚠ OPENAI_API_KEY no configurada (opcional)")

# Resumen final
print("\n" + "=" * 60)
print("RESUMEN DE RESULTADOS")
print("=" * 60)

issues = []
warnings = []

if not groq_available and not openai_available:
    issues.append("Ninguna API instalada")
    
if not groq_key and not openai_key:
    warnings.append("Ninguna API key configurada")

if issues:
    print("\n❌ ERRORES CRÍTICOS:")
    for issue in issues:
        print(f"  - {issue}")
    print("\nLa aplicación NO funcionará correctamente.")
    print("Ejecuta: pip install groq")
elif warnings:
    print("\n⚠️  ADVERTENCIAS:")
    for warning in warnings:
        print(f"  - {warning}")
    print("\n✅ La aplicación PUEDE ejecutarse.")
    print("   Configura las API keys en la interfaz.")
else:
    print("\n✅ TODO LISTO - La aplicación debería funcionar perfectamente.")

print("\n" + "=" * 60)
print("Para iniciar la aplicación ejecuta:")
print("  python whisper_gui.py")
print("=" * 60)
print()

input("Presiona Enter para continuar...")
