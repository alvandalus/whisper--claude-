# 🔧 Ejemplos de Uso Programático

Si quieres integrar el motor de transcripción en tus propios scripts, aquí tienes ejemplos:

## 📘 Ejemplo 1: Transcripción Simple con Groq

```python
from pathlib import Path
from core import transcribe_file
import os

# Configurar API key
os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

# Transcribir
audio_path = Path("mi_audio.mp3")
result = transcribe_file(audio_path, model="groq-whisper-large-v3")

# Mostrar resultado
print("Transcripción:")
print(result.text)

# Guardar a archivo
Path("transcripcion.txt").write_text(result.text, encoding='utf-8')
```

## 📘 Ejemplo 2: Con VAD (Recorte de Silencios)

```python
from pathlib import Path
from core import preprocess_vad_ffmpeg, transcribe_file, estimate_cost, probe_duration
import os

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

audio = Path("audio_largo.mp3")

# 1. Aplicar VAD
print("Aplicando VAD...")
audio_vad = preprocess_vad_ffmpeg(audio)

# 2. Estimar coste
duration = probe_duration(audio_vad)
cost = estimate_cost(duration, "groq-whisper-large-v3")
print(f"Duración: {duration}s")
print(f"Coste estimado: ${cost:.4f}")

# 3. Transcribir
print("Transcribiendo...")
result = transcribe_file(audio_vad, model="groq-whisper-large-v3")

# 4. Guardar
Path("resultado.txt").write_text(result.text, encoding='utf-8')
print("✅ Listo!")
```

## 📘 Ejemplo 3: Generar Subtítulos (SRT)

```python
from pathlib import Path
from core import transcribe_file, write_srt
import os

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

# Transcribir con timestamps
result = transcribe_file(
    Path("video.mp4"), 
    model="groq-whisper-large-v3"
)

# Generar SRT
srt_content = write_srt(result)

# Guardar
Path("subtitulos.srt").write_text(srt_content, encoding='utf-8')
print("✅ Subtítulos creados!")
```

## 📘 Ejemplo 4: Procesar Carpeta Completa

```python
from pathlib import Path
from core import transcribe_file, AUDIO_EXT
import os

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

input_dir = Path("audios_input")
output_dir = Path("transcripciones_output")
output_dir.mkdir(exist_ok=True)

# Buscar archivos de audio
audio_files = [f for f in input_dir.glob("*") if f.suffix.lower() in AUDIO_EXT]

print(f"Encontrados {len(audio_files)} archivos")

for i, audio_path in enumerate(audio_files, 1):
    try:
        print(f"[{i}/{len(audio_files)}] {audio_path.name}...")
        
        # Transcribir
        result = transcribe_file(audio_path, model="groq-whisper-large-v3")
        
        # Guardar
        output_file = output_dir / f"{audio_path.stem}.txt"
        output_file.write_text(result.text, encoding='utf-8')
        
        print(f"  ✅ OK")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("🎉 Proceso completado!")
```

## 📘 Ejemplo 5: Comparar Costes antes de Transcribir

```python
from pathlib import Path
from core import probe_duration, estimate_cost, get_all_models_info

audio = Path("audio_grande.mp3")
duration = probe_duration(audio)
minutes = duration / 60

print(f"Audio: {audio.name}")
print(f"Duración: {minutes:.2f} minutos\n")

print("Comparación de costes:")
print("-" * 60)

models_info = get_all_models_info()

for info in models_info[:5]:  # Top 5 más baratos
    cost = info['cost_per_min'] * minutes
    provider = info['provider'].upper()
    model = info['model']
    savings = info['savings_vs_openai']
    
    print(f"{model:<30} {provider:<10} ${cost:.4f}", end="")
    
    if info['is_free']:
        print("  🎉 GRATIS")
    elif savings > 0:
        print(f"  📉 {savings:.1f}% ahorro")
    else:
        print()

print("-" * 60)
```

## 📘 Ejemplo 6: Usar OpenAI en lugar de Groq

```python
from pathlib import Path
from core import transcribe_file
import os

# Cambiar a OpenAI
os.environ['OPENAI_API_KEY'] = 'tu-openai-key-aqui'

# Transcribir con OpenAI
result = transcribe_file(
    Path("audio.mp3"), 
    model="whisper-1"  # Modelo de OpenAI
)

print(result.text)
```

## 📘 Ejemplo 7: Control de Presupuesto

```python
from pathlib import Path
from core import (
    transcribe_file, estimate_cost, probe_duration,
    budget_allow, budget_consume, budget_get_remaining,
    budget_set_limit
)
import os

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

# Establecer límite diario de $1.00
budget_set_limit(1.0)

audio = Path("audio.mp3")
duration = probe_duration(audio)
cost = estimate_cost(duration, "groq-whisper-large-v3")

print(f"Coste estimado: ${cost:.4f}")
print(f"Presupuesto restante: ${budget_get_remaining():.2f}")

if budget_allow(cost):
    print("✅ Presupuesto OK, transcribiendo...")
    result = transcribe_file(audio, model="groq-whisper-large-v3")
    budget_consume(cost)
    print(f"✅ Completado. Restante: ${budget_get_remaining():.2f}")
else:
    print("❌ Presupuesto insuficiente")
```

## 📘 Ejemplo 8: Transcripción con Múltiples Idiomas

```python
from pathlib import Path
from core import transcribe_file
import os

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

# Groq detecta automáticamente el idioma
# Pero también puedes forzarlo modificando el código core.py

audios = {
    "español.mp3": "es",
    "english.mp3": "en",
    "francais.mp3": "fr",
}

for filename, language in audios.items():
    audio = Path(filename)
    result = transcribe_file(audio, model="groq-whisper-large-v3")
    
    print(f"\n{filename} ({language}):")
    print(result.text[:100] + "...")
    print(f"Idioma detectado: {result.language}")
```

## 📘 Ejemplo 9: Transcripción Asíncrona (Múltiples a la vez)

```python
from pathlib import Path
from core import transcribe_file
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

def transcribe_one(audio_path):
    """Transcribir un archivo"""
    result = transcribe_file(audio_path, model="groq-whisper-large-v3")
    return audio_path.name, result.text

async def transcribe_multiple(audio_files, max_concurrent=3):
    """Transcribir múltiples archivos en paralelo"""
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, transcribe_one, audio)
            for audio in audio_files
        ]
        results = await asyncio.gather(*tasks)
    return results

# Uso
audio_files = [
    Path("audio1.mp3"),
    Path("audio2.mp3"),
    Path("audio3.mp3"),
]

results = asyncio.run(transcribe_multiple(audio_files))

for filename, text in results:
    print(f"\n{filename}:")
    print(text[:100] + "...")
```

## 📘 Ejemplo 10: Integración con FastAPI

```python
from fastapi import FastAPI, UploadFile, File
from pathlib import Path
from core import transcribe_file
import os
import tempfile

app = FastAPI()

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Endpoint para transcribir audio"""
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Transcribir
        result = transcribe_file(tmp_path, model="groq-whisper-large-v3")
        
        return {
            "success": True,
            "text": result.text,
            "language": result.language
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    
    finally:
        # Limpiar archivo temporal
        tmp_path.unlink(missing_ok=True)

# Ejecutar con: uvicorn script:app --reload
```

## 📘 Ejemplo 11: Webhook Notifications

```python
from pathlib import Path
from core import transcribe_file, estimate_cost, probe_duration
import os
import requests

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

def send_webhook(url, data):
    """Enviar notificación por webhook"""
    requests.post(url, json=data)

def transcribe_with_webhook(audio_path, webhook_url):
    """Transcribir y notificar por webhook"""
    
    # Notificar inicio
    send_webhook(webhook_url, {
        "status": "started",
        "file": audio_path.name
    })
    
    try:
        # Transcribir
        result = transcribe_file(audio_path, model="groq-whisper-large-v3")
        
        # Notificar éxito
        send_webhook(webhook_url, {
            "status": "completed",
            "file": audio_path.name,
            "text": result.text,
            "language": result.language
        })
        
        return result
        
    except Exception as e:
        # Notificar error
        send_webhook(webhook_url, {
            "status": "failed",
            "file": audio_path.name,
            "error": str(e)
        })
        raise

# Uso
audio = Path("audio.mp3")
webhook = "https://tu-servidor.com/webhook"

result = transcribe_with_webhook(audio, webhook)
```

## 📘 Ejemplo 12: Cache de Transcripciones

```python
from pathlib import Path
from core import transcribe_file
import os
import hashlib
import json

os.environ['GROQ_API_KEY'] = 'tu-api-key-aqui'

CACHE_DIR = Path(".transcription_cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_file_hash(file_path):
    """Calcular hash del archivo"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def transcribe_with_cache(audio_path, model="groq-whisper-large-v3"):
    """Transcribir con cache para evitar duplicados"""
    
    # Calcular hash
    file_hash = get_file_hash(audio_path)
    cache_file = CACHE_DIR / f"{file_hash}.json"
    
    # Buscar en cache
    if cache_file.exists():
        print(f"✅ Usando cache para {audio_path.name}")
        data = json.loads(cache_file.read_text())
        
        class CachedResult:
            def __init__(self, data):
                self.text = data['text']
                self.language = data['language']
        
        return CachedResult(data)
    
    # Transcribir
    print(f"🔄 Transcribiendo {audio_path.name}...")
    result = transcribe_file(audio_path, model=model)
    
    # Guardar en cache
    cache_file.write_text(json.dumps({
        'text': result.text,
        'language': result.language,
        'model': model
    }), encoding='utf-8')
    
    return result

# Uso
audio = Path("audio.mp3")
result = transcribe_with_cache(audio)  # Primera vez: transcribe
result = transcribe_with_cache(audio)  # Segunda vez: usa cache
```

---

## 🎯 Consejos de Optimización

### 1. Usa VAD para audios largos
```python
audio_vad = preprocess_vad_ffmpeg(audio)  # Reduce duración
result = transcribe_file(audio_vad, model="groq-whisper-large-v3")
```

### 2. Procesa en paralelo (con límite)
```python
# Máximo 3 transcripciones simultáneas
# Más puede causar rate limits
max_concurrent = 3
```

### 3. Maneja errores de rate limit
```python
import time

for attempt in range(3):
    try:
        result = transcribe_file(audio, model="groq-whisper-large-v3")
        break
    except Exception as e:
        if "rate limit" in str(e).lower():
            time.sleep(2 ** attempt)  # Backoff exponencial
        else:
            raise
```

### 4. Usa modelo adecuado según idioma
```python
# Solo inglés -> usa distil (más barato)
if language == "en":
    model = "groq-distil-whisper-large-v3-en"
else:
    model = "groq-whisper-large-v3"
```

---

## 📚 Referencia Rápida

### Modelos Disponibles

| Modelo | Proveedor | Coste/min | Uso |
|--------|-----------|-----------|-----|
| `groq-whisper-large-v3` | Groq | $0.00011 | Multiidioma, mejor precio |
| `groq-distil-whisper-large-v3-en` | Groq | $0.00002 | Solo inglés |
| `whisper-1` | OpenAI | $0.006 | Multiidioma, más caro |
| `local-base` | Local | $0 | Gratis, lento |

### Funciones Principales

```python
# Transcribir
transcribe_file(audio_path, model="groq-whisper-large-v3")

# Procesar audio
preprocess_vad_ffmpeg(audio_path)  # Eliminar silencios
split_for_api(audio_path)          # Dividir en chunks

# Costes
probe_duration(audio_path)                    # Segundos
estimate_cost(duration, model)                # USD
budget_allow(cost)                            # True/False
budget_consume(cost)                          # Consumir

# Subtítulos
write_srt(result)  # Generar SRT

# Info
get_provider_info(model)      # Info de un modelo
get_all_models_info()         # Info de todos
```

---

**¡Feliz codificación! 🚀**
