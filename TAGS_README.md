# Sistema de Etiquetas (Tags) - Hackernews Report

El sistema de etiquetas categoriza automáticamente los posts de Hacker News por temas tecnológicos, facilitando el descubrimiento de contenido relacionado.

## 🏷️ Categorías de Tags Disponibles

### Inteligencia Artificial & Machine Learning
- **AI**: Inteligencia artificial, machine learning, deep learning, GPT, LLM, ChatGPT, Claude, Gemini, transformers, etc.

### Lenguajes de Programación
- **Python**: Python, Django, Flask, FastAPI, PyTorch, TensorFlow
- **JavaScript**: JavaScript, TypeScript, Node.js, React, Vue, Angular, Next.js, Svelte
- **Rust**: Rust, Cargo
- **Go**: Golang
- **C/C++**: C, C++, Clang, GCC
- **Java**: Java, JVM, Kotlin, Spring

### Desarrollo Web & Frontend
- **Web Dev**: Desarrollo web, frontend, backend, fullstack, HTML, CSS, navegadores

### Cloud & Infraestructura
- **Cloud**: AWS, Azure, GCP, Google Cloud, Kubernetes, Docker, containers
- **DevOps**: CI/CD, Jenkins, GitHub Actions, GitLab

### Bases de Datos
- **Database**: SQL, PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch

### Ciencia & Investigación
- **Science**: Investigación científica, papers, arXiv, Nature, física, química, biología
- **Space**: NASA, SpaceX, cohetes, satélites, Marte, Luna, astronomía
- **Climate**: Cambio climático, energías renovables, solar, eólica

### Seguridad & Privacidad
- **Security**: Vulnerabilidades, exploits, hacking, encriptación, passwords
- **Privacy**: GDPR, tracking, vigilancia, recolección de datos

### Blockchain & Crypto
- **Blockchain**: Bitcoin, Ethereum, criptomonedas, Web3, NFT, DeFi

### Hardware
- **Hardware**: Chips, procesadores, CPU, GPU, NVIDIA, AMD, Intel, ARM, RISC-V

### Móvil
- **Mobile**: iOS, Android, iPhone, App Store, Play Store, Swift

### Startups & Negocios
- **Startup**: Fundadores, VC, venture capital, funding, Series A, IPO
- **Business**: Empresas, CEO, revenue, profit, mercado

### Open Source
- **Open Source**: GitHub, GitLab, licencias MIT, Apache, GPL

### Sistemas Operativos
- **Linux**: Ubuntu, Debian, Arch, Fedora, kernel
- **macOS**: Mac OS, Apple, M1, M2, M3
- **Windows**: Microsoft, Windows 11

### Herramientas & Productividad
- **Tools**: CLI, terminal, Vim, Emacs, VSCode, IDEs

### Gaming
- **Gaming**: Juegos, Unity, Unreal, Steam, Nintendo, PlayStation, Xbox

### Otros Temas Técnicos
- **API**: REST, GraphQL, gRPC
- **Performance**: Optimización, velocidad, benchmarks, latencia
- **Testing**: Pruebas, QA, unit tests, integration tests

## 🚀 Uso

### En la Interfaz Web

1. **Filtrar por Tag**:
   - Haz clic en cualquier tag en el sidebar o en un post
   - URL: `http://localhost:5000/?tag=AI`

2. **Ver Tags Populares**:
   - El sidebar muestra los 15 tags más populares con sus conteos
   - Los tags están coloreados por categoría

3. **Combinar Filtros**:
   - Puedes combinar categoría y tag: `/?category=story&tag=Python`

### API REST

```bash
# Obtener posts con un tag específico
curl http://localhost:5000/api/posts?tag=AI

# Obtener estadísticas de tags
curl http://localhost:5000/api/tags

# Combinar filtros
curl http://localhost:5000/api/posts?category=story&tag=Python&limit=10
```

### Programáticamente

```python
from src.tags import TagSystem

# Extraer tags de un título
title = "New GPT-4 model shows improved Python code generation"
tags = TagSystem.extract_tags(title)
# Resultado: ['AI', 'Python']

# Obtener todos los tags disponibles
all_tags = TagSystem.get_all_tags()

# Obtener keywords de un tag específico
keywords = TagSystem.get_tag_keywords("AI")
```

## 🔧 Migración de Base de Datos

Si ya tienes posts en tu base de datos, ejecuta la migración para agregar tags:

```bash
python -m src.migrate_add_tags
```

Este script:
1. Agrega la columna `tags` a la tabla `posts`
2. Analiza todos los posts existentes
3. Extrae y asigna tags automáticamente basándose en los títulos

## 📊 Cómo Funciona

1. **Extracción Automática**: Cuando se obtiene un post de la API de Hacker News, el sistema analiza el título buscando palabras clave.

2. **Matching Inteligente**: Usa expresiones regulares con límites de palabra para evitar falsos positivos (ej: "go" no coincide con "google").

3. **Múltiples Tags**: Un post puede tener hasta 5 tags si su título contiene múltiples temas relevantes.

4. **Almacenamiento**: Los tags se guardan como string separado por comas en la base de datos.

## 🎨 Personalización

### Agregar Nuevos Tags

Edita `src/tags.py` y agrega tu categoría al diccionario `TAG_KEYWORDS`:

```python
TAG_KEYWORDS = {
    # ... tags existentes ...
    
    "Mi Nuevo Tag": [
        "keyword1", "keyword2", "keyword3"
    ],
}
```

### Ajustar Colores de Tags

Edita `static/style.css` para agregar colores personalizados:

```css
.post-tag[href*="Mi Nuevo Tag"],
.tag-item[href*="Mi Nuevo Tag"] {
    background-color: #color-fondo;
    color: #color-texto;
    border-color: #color-borde;
}
```

## 📈 Estadísticas

El sistema proporciona:
- **Conteo por Tag**: Cuántos posts tienen cada tag
- **Tags Populares**: Los 15 tags más frecuentes
- **Distribución**: Visualización de qué temas son más discutidos

## 🔍 Casos de Uso

1. **Desarrolladores de Python**: Filtrar por tag "Python" para ver solo contenido relevante
2. **Investigadores de AI**: Seguir discusiones sobre "AI" y "Machine Learning"
3. **Profesionales de Seguridad**: Monitorear posts con tag "Security"
4. **Entusiastas del Espacio**: Descubrir noticias con tag "Space"
5. **Análisis de Tendencias**: Ver qué tags son más populares en diferentes períodos

## 🚧 Limitaciones Actuales

- Los tags se basan solo en el título (no en el contenido del post)
- Máximo 5 tags por post
- Solo en inglés
- Algunos posts pueden no tener tags si el título no contiene keywords reconocidas

## 🔮 Mejoras Futuras

- [ ] Análisis de contenido del post (no solo título)
- [ ] Machine learning para mejorar la clasificación
- [ ] Tags personalizados por usuario
- [ ] Sugerencias de tags relacionados
- [ ] Trending tags en tiempo real
- [ ] Soporte multiidioma
- [ ] Análisis de sentimiento por tag

## 📝 Ejemplos

### Post con Múltiples Tags

**Título**: "Building a Python API with FastAPI and deploying to AWS"

**Tags Extraídos**: `Python`, `API`, `Cloud`

### Post de AI

**Título**: "GPT-4 achieves human-level performance on coding benchmarks"

**Tags Extraídos**: `AI`, `Performance`, `Testing`

### Post de Ciencia

**Título**: "NASA's James Webb Space Telescope discovers new exoplanet"

**Tags Extraídos**: `Space`, `Science`

## 🤝 Contribuir

Para agregar o mejorar tags:

1. Identifica temas tecnológicos relevantes
2. Agrega keywords al diccionario en `src/tags.py`
3. Prueba con títulos reales de Hacker News
4. Ajusta keywords para evitar falsos positivos/negativos
5. Documenta los cambios

## 📚 Referencias

- [Hacker News API](https://github.com/HackerNews/API)
- [Keyword Extraction Techniques](https://en.wikipedia.org/wiki/Keyword_extraction)
- [Tag Systems in Information Architecture](https://www.nngroup.com/articles/tagging/)
