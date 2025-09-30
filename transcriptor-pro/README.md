# Transcriptor Pro 🎙️

Sistema profesional de transcripción de audio con soporte multi-proveedor.

## ✨ Características

- 🤖 **Multi-Proveedor**: OpenAI, Groq y Whisper Local
- 💰 **Control de Costes**: Sistema de presupuesto diario
- 🎵 **Multi-Formato**: MP3, WAV, M4A, FLAC, OGG, AAC, etc.
- 📝 **Exportación SRT**: Genera subtítulos con timestamps
- 🔊 **VAD**: Eliminación automática de silencios (opcional)
- 📊 **Comparador**: Análisis de costes entre proveedores
- 🚀 **Procesamiento Paralelo**: División y compresión optimizada

## 📋 Requisitos

- Python 3.8+
- FFmpeg (requerido para procesamiento de audio)

## 🚀 Instalación Rápida

### 1. Instalar FFmpeg

**Windows (con Chocolatey):**
```bash
choco install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 2. Instalar Dependencias Python

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Obtener API Key

**Groq (Recomendado - 98% más barato):**
1. Ve a: https://console.groq.com/keys
2. Crea una cuenta gratuita
3. Genera una API key
4. Configúrala en la aplicación

**OpenAI (Alternativa):**
1. Ve a: https://platform.openai.com/api-keys
2. Genera una API key
3. Configúrala en la aplicación

## 🎮 Uso

### Iniciar la Aplicación

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
./run.sh
```

**O directamente:**
```bash
python -m src.main
```

### Transcribir un Archivo

1. Ve a la pestaña **"📄 Archivo único"**
2. Clic en **"📂 Abrir archivo"**
3. Selecciona tu archivo de audio
4. Clic en **"▶️ Transcribir"**
5. ¡Listo! El texto aparece en segundos

### Procesamiento por Lotes

1. Ve a la pestaña **"📁 Procesamiento por lotes"**
2. Configura carpeta INBOX (archivos de entrada)
3. Configura carpeta OUT (archivos de salida)
4. Clic en **"▶️ Procesar carpeta"**
5. Espera a que termine el procesamiento

### Configuración

1. Ve a la pestaña **"⚙️ Configuración"**
2. Selecciona el modelo a usar
3. Ingresa tus API keys
4. Ajusta opciones (VAD, SRT, bitrate, etc.)
5. Clic en **"💾 GUARDAR CONFIGURACIÓN"**

## 💰 Comparación de Costes

### Audio de 1 hora (60 minutos):

| Proveedor | Coste | Velocidad | Calidad |
|-----------|-------|-----------|---------|
| 🏆 **Groq Whisper V3** | **$0.0066** | 30 seg | ⭐⭐⭐⭐⭐ |
| 🥇 Groq Distil (EN) | $0.0012 | 20 seg | ⭐⭐⭐⭐⭐ |
| OpenAI Whisper | $0.36 | 2 min | ⭐⭐⭐⭐⭐ |
| Local (GPU) | $0.00 | 12 min | ⭐⭐⭐⭐ |
| Local (CPU) | $0.00 | 90 min | ⭐⭐⭐⭐ |

### Para 100 horas/mes:

```
OpenAI: $36.00/mes
Groq:   $0.66/mes   💰 Ahorro: $35.34/mes (98%)
Local:  $0.00/mes   💰 Ahorro: $36.00/mes (100%)
```

## 📁 Estructura del Proyecto

```
transcriptor-pro/
├── src/
│   ├── __init__.py          # Inicialización del paquete
│   ├── main.py              # Interfaz gráfica (GUI)
│   ├── core.py              # Motor de transcripción
│   ├── audio_utils.py       # Utilidades de audio (FFmpeg, VAD)
│   ├── budget.py            # Gestión de presupuesto
│   └── config.py            # Configuración persistente
├── requirements.txt         # Dependencias Python
├── README.md                # Este archivo
├── .gitignore               # Archivos ignorados por Git
├── run.bat                  # Script de inicio (Windows)
└── run.sh                   # Script de inicio (Linux/Mac)
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Puedes configurar las API keys mediante variables de entorno:

```bash
export GROQ_API_KEY="tu_api_key_aqui"
export OPENAI_API_KEY="tu_api_key_aqui"
```

### Archivos de Configuración

La configuración se guarda en:

**Windows:**
```
%APPDATA%\.transcriptor_pro\config.json
```

**Linux/Mac:**
```
~/.transcriptor_pro/config.json
```

### Presupuesto

El sistema de presupuesto se resetea automáticamente cada día. Puedes ajustar el límite diario en la pestaña de configuración.

## ⚠️ Notas Importantes

- 📊 El presupuesto diario por defecto es $2.00
- 🎵 Archivos mayores a 25MB se dividen automáticamente
- 🔊 VAD puede consumir mucha CPU en archivos grandes
- 💾 Las transcripciones se guardan en `%APPDATA%\.transcriptor_pro\transcripts`

## 🆘 Solución de Problemas

### Error: "groq not found"
```bash
pip install groq
```

### Error: "ffmpeg not found"
Instala FFmpeg:
```bash
# Windows
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### Error: "API key invalid"
1. Verifica que copiaste la key completa
2. Prueba generando una nueva key
3. Comprueba tu conexión a internet

### Transcripción muy lenta
- ¿Modo local? → Cambia a Groq
- ¿Audio largo? → Activa VAD (recorte de silencios)
- ¿OpenAI? → Groq es 10x más rápido

## 📝 Licencia

MIT License - Ver archivo LICENSE para más detalles.

## 🤝 Contribuir

¿Encontraste un bug o tienes una sugerencia? ¡Abre un issue!

---

**Hecho con ❤️ usando Python + Tkinter**
