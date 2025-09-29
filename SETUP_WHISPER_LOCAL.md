# 🎯 Guía: Configurar Whisper Local (GRATIS - Sin API)

## ✅ Ventajas de Whisper Local

- ✨ **100% GRATIS** - Sin costes de API
- 🔒 **Privacidad total** - Los archivos nunca salen de tu PC
- 🚀 **Sin límites** - Transcribe todo lo que quieras
- 📡 **Funciona offline** - No requiere internet
- ⚡ **Rápido con GPU** - Si tienes NVIDIA GPU

## 📋 Requisitos

### Mínimos:
- Python 3.8 o superior
- 8GB RAM
- 2GB espacio en disco

### Recomendados:
- 16GB RAM
- GPU NVIDIA con 4GB+ VRAM (opcional pero MUCHO más rápido)
- CUDA instalado (si usas GPU)

---

## 🔧 Instalación Paso a Paso

### **Paso 1: Instalar FFmpeg**

#### Windows:
```powershell
# Opción A: Con Chocolatey (recomendado)
choco install ffmpeg

# Opción B: Manual
# 1. Descargar de: https://ffmpeg.org/download.html
# 2. Extraer a C:\ffmpeg
# 3. Añadir C:\ffmpeg\bin a PATH
```

#### Verificar instalación:
```bash
ffmpeg -version
```

### **Paso 2: Instalar Whisper**

```bash
# Whisper oficial de OpenAI
pip install openai-whisper

# O la versión más rápida (faster-whisper)
pip install faster-whisper
```

### **Paso 3: (Opcional) Instalar CUDA para GPU**

Si tienes GPU NVIDIA:

```bash
# PyTorch con CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verificar que detecta la GPU
python -c "import torch; print(torch.cuda.is_available())"
# Debe mostrar: True
```

### **Paso 4: Instalar dependencias adicionales**

```bash
pip install tiktoken
pip install numba
```

---

## 🎮 Modelos Disponibles

Whisper tiene 5 tamaños de modelo:

| Modelo | Tamaño | VRAM GPU | RAM CPU | Velocidad | Calidad |
|--------|--------|----------|---------|-----------|---------|
| `tiny` | 39 MB | ~1 GB | ~1 GB | ⚡⚡⚡⚡⚡ | ⭐⭐ |
| `base` | 74 MB | ~1 GB | ~1 GB | ⚡⚡⚡⚡ | ⭐⭐⭐ |
| `small` | 244 MB | ~2 GB | ~2 GB | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| `medium` | 769 MB | ~5 GB | ~5 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| `large` | 1550 MB | ~10 GB | ~10 GB | ⚡ | ⭐⭐⭐⭐⭐⭐ |

**Recomendación:**
- Con GPU potente: `large` o `medium`
- GPU normal: `small` o `medium`
- Solo CPU: `base` o `small`
- PC antiguo: `tiny`

---

## 🧪 Prueba Rápida

```python
import whisper

# Cargar modelo (la primera vez descarga ~1.5GB)
model = whisper.load_model("base")

# Transcribir
result = model.transcribe("audio.mp3")

print(result["text"])
```

---

## ⚡ Comparación de Velocidad

### Audio de 10 minutos:

| Configuración | Tiempo | Velocidad Real-Time |
|---------------|--------|---------------------|
| CPU (i7) + tiny | ~5 min | 2x |
| CPU (i7) + base | ~8 min | 1.25x |
| CPU (i7) + small | ~15 min | 0.66x |
| GPU (RTX 3060) + small | ~1 min | 10x |
| GPU (RTX 3060) + medium | ~2 min | 5x |
| GPU (RTX 3060) + large | ~3 min | 3.3x |
| GPU (RTX 4090) + large | ~45 seg | 13x |

---

## 🎛️ Opciones Avanzadas

```python
result = model.transcribe(
    "audio.mp3",
    language="es",           # Forzar idioma (más rápido)
    task="transcribe",       # o "translate" (traduce a inglés)
    temperature=0.0,         # Menos aleatorio = más consistente
    best_of=5,              # Mejor de 5 intentos (más lento pero mejor)
    beam_size=5,            # Búsqueda de beam (mejor calidad)
    patience=1.0,           # Paciencia en búsqueda
    word_timestamps=True,   # Timestamps por palabra
    initial_prompt="Contexto previo..."  # Ayuda al modelo
)
```

---

## 🚀 Faster-Whisper (Alternativa MÁS RÁPIDA)

Si quieres aún más velocidad:

```bash
pip install faster-whisper
```

```python
from faster_whisper import WhisperModel

# 4x más rápido que whisper original
model = WhisperModel("base", device="cuda", compute_type="float16")

segments, info = model.transcribe("audio.mp3", language="es")

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

**Ventajas de faster-whisper:**
- ⚡ 4x más rápido
- 💾 Usa menos memoria
- 🎯 Misma calidad

---

## 📊 Comparación: Local vs API

### Audio de 1 hora:

| Método | Coste | Tiempo | Privacidad | Offline |
|--------|-------|--------|------------|---------|
| **OpenAI API** | $0.36 | ~2 min | ❌ | ❌ |
| **Groq API** | $0.0066 | ~30 seg | ❌ | ❌ |
| **Local GPU (RTX 3060)** | $0 | ~12 min | ✅ | ✅ |
| **Local CPU (i7)** | $0 | ~45 min | ✅ | ✅ |

### Para 100 horas/mes:

| Método | Coste Mensual |
|--------|---------------|
| OpenAI API | **$36.00** |
| Groq API | **$0.66** |
| Local | **$0.00** 🎉 |

---

## 🔥 Código de Integración con tu GUI

```python
# En core.py - añadir función para Whisper local

def transcribe_file_local(audio_path: Path, model_size: str = "base") -> dict:
    """
    Transcribir usando Whisper local (gratis)
    
    Args:
        audio_path: Ruta al archivo de audio
        model_size: tiny, base, small, medium, large
    
    Returns:
        dict con 'text' y 'segments'
    """
    import whisper
    
    # Cargar modelo (cachea automáticamente)
    model = whisper.load_model(model_size)
    
    # Transcribir
    result = model.transcribe(
        str(audio_path),
        language="es",  # Cambiar según necesites
        word_timestamps=True,
        fp16=torch.cuda.is_available()  # Usar float16 si hay GPU
    )
    
    return {
        'text': result['text'],
        'segments': result['segments'],
        'language': result['language']
    }
```

---

## 🎨 Añadir a la GUI

En `whisper_gui.py`, añadir opción:

```python
# En ConfiguraciónTab
ttk.Label(cfg, text="Modo transcripción:").grid(row=0, column=0)
self.mode_var = tk.StringVar(value="local")
ttk.Combobox(cfg, 
    values=["local", "openai-api", "groq-api"],
    textvariable=self.mode_var
).grid(row=0, column=1)

# Si modo=local, elegir tamaño de modelo
ttk.Label(cfg, text="Modelo local:").grid(row=1, column=0)
self.local_model_var = tk.StringVar(value="base")
ttk.Combobox(cfg,
    values=["tiny", "base", "small", "medium", "large"],
    textvariable=self.local_model_var
).grid(row=1, column=1)
```

---

## ⚠️ Troubleshooting

### "No module named 'whisper'"
```bash
pip install --upgrade openai-whisper
```

### "CUDA not available" (con GPU NVIDIA)
```bash
# Reinstalar PyTorch con CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### "Out of memory" (GPU)
- Usar modelo más pequeño (`small` en vez de `large`)
- O cambiar a CPU: `model = whisper.load_model("base", device="cpu")`

### Muy lento en CPU
- Usa `tiny` o `base` model
- Considera actualizar a GPU
- O usa APIs (Groq es barato)

---

## 🎯 Siguiente Paso

1. ✅ Instalar FFmpeg
2. ✅ `pip install openai-whisper`
3. ✅ Probar con audio corto
4. ✅ Integrar en tu GUI

**¿Necesitas ayuda con algún paso?** 🚀
