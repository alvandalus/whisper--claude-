# Transcriptor Pro - Audio Transcription System 🎙️

Sistema profesional de transcripción de audio con soporte multi-proveedor (OpenAI, Groq, Whisper Local).

---

## 📦 Proyecto Actual

### **➡️ Usar: `transcriptor-pro/`**

Esta es la **versión limpia y refactorizada** del proyecto con:

- ✅ Código modular y mantenible
- ✅ Arquitectura separada por responsabilidades
- ✅ Logging profesional
- ✅ Documentación completa
- ✅ Sin código duplicado
- ✅ Todas las funcionalidades originales

**📖 Ver documentación completa:** [`transcriptor-pro/README.md`](transcriptor-pro/README.md)

---

## 🚀 Inicio Rápido

```bash
cd transcriptor-pro

# Instalar dependencias
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Ejecutar
run.bat  # Windows
# o
./run.sh  # Linux/Mac
```

---

## 📂 Estructura del Repositorio

```
.
├── transcriptor-pro/        ⭐ PROYECTO PRINCIPAL (usar este)
│   ├── src/                 # Código fuente modular
│   │   ├── main.py         # Interfaz GUI
│   │   ├── core.py         # Motor de transcripción
│   │   ├── audio_utils.py  # Utilidades de audio
│   │   ├── budget.py       # Control de presupuesto
│   │   └── config.py       # Configuración
│   ├── tests/              # 🧪 Tests unitarios y de integración
│   ├── .env.example        # 🔐 Template de variables de entorno
│   ├── Dockerfile          # 🐳 Containerización
│   ├── docker-compose.yml  # 🐳 Orquestación de contenedores
│   ├── pytest.ini          # ⚙️ Configuración de tests
│   ├── README.md           # Documentación completa
│   ├── SETUP.md            # 📚 Guía de instalación detallada
│   ├── CONTRIBUTING.md     # 🤝 Guía de contribución
│   ├── requirements.txt    # Dependencias
│   └── run.bat / run.sh    # Scripts de inicio
│
├── .github/
│   └── workflows/
│       └── ci.yml          # 🔄 CI/CD automatizado
│
├── archive-original/        📦 Archivos originales (backup)
│   ├── whisper_gui.py      # GUI original
│   ├── core.py             # Core original
│   └── ...
│
├── LICENSE                  # Licencia MIT
└── requirements.txt         # Dependencias compatibles
```

---

## ✨ Características

### Funcionalidades Core
- 🤖 **Multi-Proveedor**: OpenAI, Groq, Whisper Local
- 💰 **Control de Costes**: Sistema de presupuesto diario
- 🎵 **Multi-Formato**: MP3, WAV, M4A, FLAC, OGG, etc.
- 📝 **Exportación SRT**: Subtítulos con timestamps
- 🔊 **VAD**: Eliminación de silencios (opcional)
- 📊 **Comparador**: Análisis de costes entre proveedores
- 🚀 **Procesamiento Paralelo**: División y compresión optimizada
- 📁 **Procesamiento por Lotes**: Múltiples archivos simultáneos

### 🆕 Mejoras de Calidad y Desarrollo
- 🔐 **Gestión Segura de Credenciales**: Variables de entorno con `.env`
- 🧪 **Suite de Tests**: Tests unitarios y de integración con pytest
- 🐳 **Docker Ready**: Dockerfile y docker-compose incluidos
- 🔄 **CI/CD**: GitHub Actions para tests automáticos
- 📦 **Dependencias Versionadas**: Requirements con versiones específicas
- 🛡️ **Análisis de Seguridad**: Safety y Bandit integrados
- 📊 **Cobertura de Código**: Reports automáticos con pytest-cov
- 🎨 **Code Quality**: Black, Ruff y MyPy configurados

---

## 💰 Comparación de Costes

| Proveedor | 1 hora | 100 horas/mes | Velocidad |
|-----------|--------|---------------|-----------|
| **Groq Whisper V3** | $0.0066 | $0.66 | 30 seg |
| Groq Distil (EN) | $0.0012 | $0.12 | 20 seg |
| OpenAI Whisper | $0.36 | $36.00 | 2 min |
| Local (GPU) | $0.00 | $0.00 | 12 min |
| Local (CPU) | $0.00 | $0.00 | 90 min |

**💡 Ahorro con Groq: 98% vs OpenAI**

---

## 📋 Requisitos

- Python 3.8+
- FFmpeg (para procesamiento de audio)
- API Key de Groq o OpenAI (opcional si usas modo local)

---

## 📖 Documentación

### Documentación de Usuario
- **Documentación Principal**: [`transcriptor-pro/README.md`](transcriptor-pro/README.md)
- **Guía de Instalación**: [`transcriptor-pro/SETUP.md`](transcriptor-pro/SETUP.md)
- **Guía de Migración**: [`transcriptor-pro/MIGRATION.md`](transcriptor-pro/MIGRATION.md)
- **Historial de Cambios**: [`transcriptor-pro/CHANGELOG.md`](transcriptor-pro/CHANGELOG.md)

### Documentación de Desarrollo
- **Guía de Contribución**: [`transcriptor-pro/CONTRIBUTING.md`](transcriptor-pro/CONTRIBUTING.md)
- **Configuración de Tests**: [`transcriptor-pro/pytest.ini`](transcriptor-pro/pytest.ini)
- **CI/CD Workflows**: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

---

## 🔄 Migración desde Versión Anterior

Si estabas usando la versión anterior del proyecto:

1. Tus configuraciones y API keys se mantienen
2. Las transcripciones anteriores siguen disponibles
3. La interfaz es prácticamente idéntica
4. Todas las funcionalidades están preservadas

**Ver guía completa**: [`transcriptor-pro/MIGRATION.md`](transcriptor-pro/MIGRATION.md)

---

## 📞 Soporte

- **Issues**: Abre un issue en GitHub
- **Documentación**: Lee el README en `transcriptor-pro/`
- **Preguntas**: Revisa la sección FAQ en la documentación

---

## 📝 Licencia

MIT License - Ver archivo [LICENSE](LICENSE) para más detalles.

---

## 🎯 Versiones

- **v1.0.0** (Actual): Refactorización completa, código modular
- **v0.x** (Legacy): Versión original (en `archive-original/`)

---

**Hecho con ❤️ usando Python + Tkinter**
