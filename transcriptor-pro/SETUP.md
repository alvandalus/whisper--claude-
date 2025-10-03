# Guía de Configuración - Transcriptor Pro 🚀

## 📋 Tabla de Contenidos

- [Instalación Local](#instalación-local)
- [Configuración con Variables de Entorno](#configuración-con-variables-de-entorno)
- [Instalación con Docker](#instalación-con-docker)
- [Ejecutar Tests](#ejecutar-tests)
- [CI/CD](#cicd)

---

## 🖥️ Instalación Local

### 1. Requisitos Previos

- **Python 3.9+** instalado
- **FFmpeg** instalado
- **Git** instalado

### 2. Instalar FFmpeg

#### Windows
```bash
# Con Chocolatey
choco install ffmpeg

# Con Winget
winget install Gyan.FFmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

### 3. Clonar y Configurar

```bash
# Clonar repositorio
git clone https://github.com/alvandalus/whisper--claude-.git
cd whisper--claude-/transcriptor-pro

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🔐 Configuración con Variables de Entorno

### 1. Crear archivo .env

```bash
# Copiar template
cp .env.example .env

# Editar con tus valores
nano .env  # o usa tu editor preferido
```

### 2. Configurar API Keys

Edita `.env` y agrega tus API keys:

```bash
# API Keys
GROQ_API_KEY=tu_api_key_de_groq_aquí
OPENAI_API_KEY=tu_api_key_de_openai_aquí

# Configuración
DEFAULT_MODEL=groq-whisper-large-v3
DAILY_BUDGET=2.0
AUDIO_BITRATE=192
USE_VAD=false
EXPORT_SRT=true
```

### 3. Obtener API Keys

**Groq (Recomendado - 98% más barato):**
1. Visita: https://console.groq.com/keys
2. Crea cuenta gratuita
3. Genera API key
4. Copia y pega en `.env`

**OpenAI (Opcional):**
1. Visita: https://platform.openai.com/api-keys
2. Genera API key
3. Copia y pega en `.env`

### 4. Ejecutar Aplicación

```bash
# Opción 1: Script directo
python -m src.main

# Opción 2: Script de inicio
./run.sh  # Linux/Mac
run.bat   # Windows
```

---

## 🐳 Instalación con Docker

### 1. Construir Imagen

```bash
cd transcriptor-pro

# Construir imagen
docker build -t transcriptor-pro:latest .
```

### 2. Ejecutar con Docker Compose

```bash
# Crear archivo .env con tus API keys
cp .env.example .env
nano .env

# Iniciar servicio
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicio
docker-compose down
```

### 3. Ejecutar Contenedor Individual

```bash
docker run -d \
  --name transcriptor-pro \
  -v $(pwd)/INBOX:/app/INBOX \
  -v $(pwd)/OUT:/app/OUT \
  -v $(pwd)/transcripts:/app/transcripts \
  -e GROQ_API_KEY=tu_api_key \
  transcriptor-pro:latest
```

### 4. Modo Worker (Procesamiento por Lotes)

```bash
# Activar perfil worker
docker-compose --profile worker up -d
```

---

## 🧪 Ejecutar Tests

### 1. Instalación de Dependencias de Test

```bash
pip install pytest pytest-cov pytest-asyncio
```

### 2. Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/test_config.py
pytest tests/test_core.py -v

# Solo tests unitarios
pytest -m unit

# Excluir tests lentos
pytest -m "not slow"
```

### 3. Ver Reporte de Cobertura

```bash
# Generar reporte HTML
pytest --cov=src --cov-report=html

# Abrir en navegador
# Windows:
start htmlcov/index.html
# Linux/Mac:
open htmlcov/index.html
```

---

## 🔄 CI/CD

### 1. GitHub Actions

El proyecto incluye workflows de CI/CD automáticos:

- **Tests**: Se ejecutan en cada push/PR
- **Linting**: Black, Ruff, MyPy
- **Seguridad**: Safety, Bandit
- **Plataformas**: Ubuntu, Windows, macOS
- **Python**: 3.9, 3.10, 3.11, 3.12

### 2. Configurar Secrets en GitHub

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Agrega estos secrets:
   - `GROQ_API_KEY`
   - `OPENAI_API_KEY`

### 3. Workflows Disponibles

```
.github/workflows/
└── ci.yml          # Tests, linting y seguridad
```

### 4. Badge de Estado

Agrega a tu README:

```markdown
![CI](https://github.com/alvandalus/whisper--claude-/workflows/CI/badge.svg)
```

---

## 🛠️ Desarrollo

### 1. Configurar Pre-commit Hooks

```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

### 2. Formateo de Código

```bash
# Formatear con Black
black src/ tests/

# Verificar sin cambios
black --check src/ tests/
```

### 3. Linting

```bash
# Ejecutar Ruff
ruff check src/ tests/

# Autofix
ruff check --fix src/ tests/
```

### 4. Type Checking

```bash
# Ejecutar MyPy
mypy src/ --ignore-missing-imports
```

---

## 📊 Monitoreo

### 1. Logs

Los logs se guardan en:
- **Local**: `%APPDATA%\.transcriptor_pro\logs\`
- **Docker**: `./logs/`

### 2. Configurar Nivel de Logs

En `.env`:
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_MAX_SIZE=10  # MB
LOG_BACKUP_COUNT=5
```

---

## 🚨 Solución de Problemas

### Error: "python-dotenv not found"
```bash
pip install python-dotenv
```

### Error: "FFmpeg not found"
```bash
# Verificar instalación
ffmpeg -version

# Reinstalar si es necesario
choco install ffmpeg  # Windows
brew install ffmpeg   # macOS
```

### Tests fallan por API keys
```bash
# Asegúrate de tener .env configurado
export GROQ_API_KEY=tu_key  # Linux/Mac
set GROQ_API_KEY=tu_key     # Windows
```

### Docker no encuentra volúmenes
```bash
# Crear directorios manualmente
mkdir -p INBOX OUT transcripts logs

# Permisos en Linux
chmod 755 INBOX OUT transcripts logs
```

---

## 📚 Recursos Adicionales

- [README Principal](README.md)
- [Documentación Completa](docs/)
- [Issues de GitHub](https://github.com/alvandalus/whisper--claude-/issues)
- [Groq API Docs](https://console.groq.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs)

---

**¿Necesitas ayuda?** Abre un issue en GitHub o consulta la documentación completa.
