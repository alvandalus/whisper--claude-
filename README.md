# IA Audio - Multi-Provider Edition 🚀

> **Transcribe audio a texto con OpenAI, Groq o Whisper Local**  
> Una interfaz gráfica para transcribir audio usando diferentes proveedores de IA

## Características ✨

- 🎯 **Multi-Proveedor**: Usa OpenAI, Groq o Whisper local
- 💰 **Control de Costos**: Monitoreo de gastos y presupuesto diario
- 🎵 **Soporte Multi-Formato**: MP3, WAV, M4A, FLAC, etc.
- 📝 **Exportación SRT**: Genera subtítulos con marcas de tiempo
- 🔊 **VAD**: Eliminación automática de silencios (opcional)
- 📋 **Historial**: Guarda y gestiona tus transcripciones
- 🌐 **Auto-Lenguaje**: Detección automática de idioma
- 🚀 **Procesamiento Paralelo**: División y compresión optimizada

## Instalación 🔧

1. **Instalar FFmpeg**:
   - Windows: `choco install ffmpeg`
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

2. **Instalar Dependencias**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configurar API Keys**:
   - Obtén tus API keys de OpenAI y/o Groq
   - Configúralas en la interfaz (⚙️ Configuración)

## Uso 🎮

1. **Iniciar la Aplicación**:
   ```bash
   python whisper_gui.py
   ```

2. **Transcribir Audio**:
   - Selecciona un archivo de audio
   - Elige el modelo de transcripción
   - Configura opciones (VAD, SRT, etc.)
   - ¡Click en Transcribir!

3. **Gestionar Historial**:
   - Revisa transcripciones anteriores
   - Abre archivos TXT/SRT generados
   - Accede rápidamente al audio original

## Notas Importantes 📌

- 📊 El presupuesto diario por defecto es $2.00
- 🎵 Archivos mayores a 25MB se dividen automáticamente
- 🔊 VAD puede consumir mucha CPU en archivos grandes
- 💾 Las transcripciones se guardan en la carpeta "transcripciones"

## Contribuir 🤝

¿Encontraste un bug o tienes una sugerencia? ¡Abre un issue o envía un pull request!

## Licencia 📄

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para más detalles.

---
Hecho con ❤️ usando Python + Tkinter

---

## ⚡ Instalación Rápida (3 minutos)

### 1️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2️⃣ Instalar FFmpeg

**Windows (con Chocolatey):**
```bash
choco install ffmpeg
```

**O descarga manual:** https://ffmpeg.org/download.html

### 3️⃣ Obtener API Key de Groq (GRATIS)

1. 🌐 Ve a: https://console.groq.com/keys
2. 📝 Crea cuenta (sin tarjeta de crédito)
3. 🔑 Genera API key
4. 📋 Cópiala

### 4️⃣ ¡Listo!

**Windows:**
```bash
INICIAR.bat
```

**Linux/Mac:**
```bash
python whisper_gui.py
```

---

## 🎯 Características Principales

### ✨ Multi-Proveedor
- **Groq**: 50x más barato, 10x más rápido (recomendado)
- **OpenAI**: Calidad premium, más caro
- **Local**: 100% gratis, pero lento sin GPU

### 💰 Ahorro Inteligente
- Comparador visual de costes
- Selector automático del mejor proveedor
- Control de presupuesto diario

### 🚀 Funcionalidades
- ✅ Transcripción de archivo único
- ✅ Procesamiento por lotes (carpetas)
- ✅ Exportación a TXT y SRT
- ✅ VAD (eliminación de silencios)
- ✅ Historial y estadísticas

---

## 💵 Comparación de Costes

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
Groq:   $0.66/mes  💰 Ahorro: $35.34/mes (98%)
Local:  $0.00/mes  💰 Ahorro: $36.00/mes (100%)
```

---

## 🖥️ Capturas de Pantalla

### Pestaña Principal
```
┌─────────────────────────────────────────────────────┐
│ 📂 Abrir archivo  [archivo.mp3]  ▶️ Transcribir     │
├─────────────────────────────────────────────────────┤
│ Transcripción:                                      │
│                                                     │
│ Lorem ipsum dolor sit amet, consectetur adipiscing │
│ elit. Sed do eiusmod tempor incididunt ut labore...│
│                                                     │
│ 💾 Guardar  📋 Copiar  🗑️ Limpiar                   │
└─────────────────────────────────────────────────────┘
```

### Comparador de Costes
```
Duración: [60] minutos  🔄 Calcular

┌────────────────────────────────────────────────────┐
│ Modelo          │ Proveedor │ Coste    │ Ahorro    │
├────────────────────────────────────────────────────┤
│ groq-whisper-v3 │ GROQ      │ $0.0066  │ 98.2% 📉  │
│ groq-distil-en  │ GROQ      │ $0.0012  │ 99.7% 📉  │
│ whisper-1       │ OPENAI    │ $0.3600  │ Ref.      │
└────────────────────────────────────────────────────┘

🏆 Más barato: groq-whisper-v3 ($0.0066)
💰 Ahorrarías: $0.3534 (98.2%) vs OpenAI
```

---

## 📖 Guía de Uso

### Primera Vez

1. Abre la app
2. Ve a **⚙️ Configuración**
3. Pega tu **Groq API Key**
4. Selecciona modelo: `groq-whisper-large-v3`
5. **💾 Guardar configuración**

### Transcribir un Archivo

1. **📄 Archivo único**
2. **📂 Abrir archivo**
3. **▶️ Transcribir**
4. ¡Listo! El texto aparece en segundos

### Procesar Múltiples Archivos

1. **📁 Procesamiento por lotes**
2. Configura carpetas INBOX y OUT
3. Coloca archivos en INBOX
4. **▶️ Procesar carpeta**
5. Los resultados van a OUT

---

## ❓ FAQ

### ¿Es Groq tan bueno como OpenAI?

**SÍ**. Mismo modelo (Whisper Large V3), misma calidad. Solo que Groq lo optimizó en hardware especial (LPU) y puede cobrarlo mucho más barato.

### ¿Necesito tarjeta de crédito?

**NO** para Groq. La cuenta gratuita incluye:
- 14,400 requests/día
- Sin límite de minutos de audio  
- Sin tarjeta requerida

### ¿Funciona sin internet?

Solo el modo **Local** (Whisper en tu PC). Los modos OpenAI y Groq requieren internet.

### ¿Mi PC puede usar modo Local?

Con tus specs (i5-13340P, 16GB RAM, Iris Xe):
- ❌ **NO recomendado**
- Muy lento (1-2 horas por cada hora de audio)
- Mejor usa Groq (rápido y casi gratis)

### ¿Qué modelo elegir?

| Si necesitas... | Usa... |
|----------------|--------|
| Barato + rápido | `groq-whisper-large-v3` |
| Solo inglés | `groq-distil-whisper-large-v3-en` |
| Ya tienes OpenAI | `whisper-1` |
| Gratis total | `local-base` (lento) |

---

## 🔧 Estructura de Archivos

```
whisper-gui-v3/
├── whisper_gui.py       # Interfaz gráfica
├── core.py              # Lógica de transcripción
├── requirements.txt     # Dependencias Python
├── INICIAR.bat         # Script de inicio (Windows)
├── LEEME.md            # Guía completa
└── README.md           # Este archivo
```

---

## 🆘 Solución de Problemas

### Error: "groq not found"
```bash
pip install groq
```

### Error: "ffmpeg not found"
Instala FFmpeg:
```bash
choco install ffmpeg
```

### Error: "API key invalid"
1. Verifica que copiaste la key completa
2. Prueba generando una nueva key
3. Comprueba tu conexión a internet

### Transcripción muy lenta
- ¿Modo local? → Cambia a Groq
- ¿Audio largo? → Activa VAD (recorte de silencios)
- ¿OpenAI? → Groq es 10x más rápido

---

## 🎉 Novedades v3.0

### Nuevo en esta versión:

- ✨ Soporte multi-proveedor (OpenAI/Groq/Local)
- 💰 Comparador visual de costes
- 🔑 Gestor de API keys integrado
- 📊 Estadísticas mejoradas
- ⚡ 10x más rápido con Groq
- 💵 Ahorra 98% en costes

### Comparado con v2.0:

| Característica | v2.0 | v3.0 |
|----------------|------|------|
| Proveedores | 1 (OpenAI) | 3 (OpenAI/Groq/Local) |
| Coste/hora | $0.36 | $0.0066 (con Groq) |
| Velocidad | 2 min | 30 seg (con Groq) |
| Comparador | ❌ | ✅ |

---

## 📝 Licencia

Este proyecto es de código abierto. Úsalo, modifícalo y distribúyelo libremente.

---

## 🌟 ¿Te gustó?

Si esta herramienta te ahorra tiempo y dinero:
- ⭐ Dale una estrella al proyecto
- 🐛 Reporta bugs o sugiere mejoras
- 💬 Comparte con otros

---

## 📞 Soporte

¿Problemas? Revisa:
1. Esta guía (README.md)
2. Guía completa (LEEME.md)
3. Setup de Whisper Local (SETUP_WHISPER_LOCAL.md)
4. Logs en: `%APPDATA%\.whisper4\app.log`

---

## 🎯 Resumen Rápido

**¿Por qué usar esta herramienta?**

✅ Transcripción ultra rápida (30 segundos vs 2 minutos)  
✅ Ahorra 98% en costes ($0.66 vs $36 por 100 horas)  
✅ Misma calidad de OpenAI  
✅ Sin tarjeta de crédito (Groq gratis)  
✅ Interfaz simple y visual  
✅ Procesamiento por lotes  
✅ Exporta a TXT y SRT  

**Tiempo de setup:** 3 minutos  
**Inversión:** $0.00 (Groq gratis)  
**Ahorro anual:** $400+ (si usas mucho)  

---

**¡Empieza ahora!** 🚀

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Ejecutar
python whisper_gui.py

# 3. Configurar Groq API
# 4. ¡Transcribir!
```

---

**Hecho con ❤️ para la comunidad**
