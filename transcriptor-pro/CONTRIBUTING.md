# Guía de Contribución 🤝

Gracias por tu interés en contribuir a Transcriptor Pro. Esta guía te ayudará a empezar.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
- [Configuración de Desarrollo](#configuración-de-desarrollo)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Guías de Estilo](#guías-de-estilo)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Mejoras](#sugerir-mejoras)

---

## 📜 Código de Conducta

Este proyecto sigue el [Contributor Covenant](https://www.contributor-covenant.org/). Al participar, se espera que respetes este código.

---

## 🚀 ¿Cómo Puedo Contribuir?

### Reportar Bugs

- Usa el template de issues de GitHub
- Describe claramente el problema
- Incluye pasos para reproducir
- Adjunta logs si es posible
- Especifica tu entorno (OS, Python version, etc.)

### Sugerir Features

- Abre un issue con el tag `enhancement`
- Describe el caso de uso
- Explica por qué sería útil
- Propón una implementación si es posible

### Contribuir Código

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 🛠️ Configuración de Desarrollo

### 1. Fork y Clone

```bash
# Fork en GitHub, luego:
git clone https://github.com/TU_USUARIO/whisper--claude-.git
cd whisper--claude-/transcriptor-pro
```

### 2. Configurar Entorno

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependencias (incluye dev)
pip install -r requirements.txt

# Instalar herramientas de desarrollo
pip install black ruff mypy pytest pytest-cov pre-commit
```

### 3. Configurar Pre-commit

```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

### 4. Configurar Variables de Entorno

```bash
cp .env.example .env
# Edita .env con tus API keys
```

---

## 🔄 Proceso de Pull Request

### 1. Antes de Crear el PR

- [ ] Ejecuta todos los tests: `pytest`
- [ ] Verifica formateo: `black --check src/ tests/`
- [ ] Ejecuta linter: `ruff check src/ tests/`
- [ ] Type checking: `mypy src/`
- [ ] Actualiza documentación si es necesario
- [ ] Agrega tests para nuevas funcionalidades

### 2. Crear el PR

- Usa un título descriptivo
- Describe los cambios realizados
- Referencia issues relacionados (#123)
- Marca como WIP si no está listo

### 3. Durante la Revisión

- Responde a comentarios
- Realiza cambios solicitados
- Mantén la rama actualizada con master
- No hagas force push después de review

### 4. Después del Merge

- Elimina tu rama feature
- Actualiza tu fork
- Celebra 🎉

---

## 🎨 Guías de Estilo

### Python

Seguimos PEP 8 con algunas excepciones:

```python
# Formato con Black (line length 100)
black --line-length 100 src/ tests/

# Imports ordenados
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config import AppConfig
from src.core import transcribe_audio
```

### Docstrings

Usamos estilo Google:

```python
def transcribe_audio(audio_path: Path, model: str = "groq-whisper-large-v3") -> TranscriptionResult:
    """
    Transcribe un archivo de audio usando el modelo especificado.

    Args:
        audio_path: Ruta absoluta al archivo de audio
        model: Identificador del modelo a usar

    Returns:
        TranscriptionResult con texto, segmentos y metadatos

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el formato no es soportado

    Example:
        >>> result = transcribe_audio(Path("audio.mp3"))
        >>> print(result.text)
    """
    pass
```

### Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Formato
<type>(<scope>): <subject>

# Tipos
feat: Nueva funcionalidad
fix: Corrección de bug
docs: Cambios en documentación
style: Formateo, punto y coma faltante, etc.
refactor: Refactorización de código
test: Agregar tests
chore: Mantenimiento

# Ejemplos
feat(core): add support for Whisper v4
fix(budget): correct daily reset calculation
docs(readme): update installation instructions
test(config): add validation tests
```

### Ramas

```bash
# Formato
<type>/<short-description>

# Ejemplos
feature/add-batch-processing
fix/audio-validation-bug
docs/update-api-docs
refactor/improve-error-handling
```

---

## 🧪 Tests

### Escribir Tests

```python
import pytest
from src.core import calculate_cost

class TestCostCalculation:
    """Tests para cálculo de costes"""

    def test_calculate_cost_groq(self):
        """Test cálculo con Groq"""
        cost = calculate_cost(60, "groq-whisper-large-v3")
        assert cost > 0

    @pytest.mark.slow
    def test_long_transcription(self):
        """Test de transcripción larga"""
        # Test que tarda mucho
        pass
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/test_core.py::TestCostCalculation::test_calculate_cost_groq

# Excluir lentos
pytest -m "not slow"
```

---

## 📝 Documentación

### Actualizar Docs

- Actualiza README.md si cambias funcionalidades principales
- Actualiza SETUP.md si cambias configuración
- Agrega docstrings a nuevas funciones/clases
- Actualiza CHANGELOG.md

### Generar Docs (Futuro)

```bash
# Sphinx (cuando se implemente)
cd docs
make html
```

---

## 🐛 Reportar Bugs

### Template de Bug Report

```markdown
**Descripción**
Descripción clara del bug

**Para Reproducir**
1. Ve a '...'
2. Haz click en '...'
3. Observa el error

**Comportamiento Esperado**
Qué esperabas que pasara

**Screenshots**
Si aplica, adjunta capturas

**Entorno:**
 - OS: [e.g. Windows 11]
 - Python: [e.g. 3.11]
 - Version: [e.g. 1.0.0]

**Logs**
```
Pega logs aquí
```

**Contexto Adicional**
Cualquier otra información relevante
```

---

## 💡 Sugerir Mejoras

### Template de Feature Request

```markdown
**¿El feature resuelve un problema? Descríbelo.**
Descripción clara del problema

**Describe la solución que te gustaría**
Descripción clara de lo que quieres que pase

**Describe alternativas que consideraste**
Otras soluciones o features que consideraste

**Contexto Adicional**
Screenshots, mockups, etc.
```

---

## 🏆 Reconocimientos

Los contribuidores serán listados en:
- README.md (sección Contributors)
- CHANGELOG.md (releases)
- Commits del proyecto

---

## ❓ Preguntas

Si tienes preguntas:

1. Revisa la [documentación](README.md)
2. Busca en [issues existentes](https://github.com/alvandalus/whisper--claude-/issues)
3. Abre un nuevo issue con tag `question`

---

## 📞 Contacto

- **Issues**: [GitHub Issues](https://github.com/alvandalus/whisper--claude-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alvandalus/whisper--claude-/discussions)

---

**¡Gracias por contribuir! 🙌**
