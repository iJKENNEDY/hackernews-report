---
name: etiquetar
description: etiquetar o resaltar posts que contengan empresas ai o similares.
---

```markdown
### 🎯 Criterios de Etiquetado Prioritario

Identificar y resaltar posts que mencionen:

#### 🏢 Ecosistema AI
- 🟢 **<span style="color: #74aa9c;">OpenAI</span>** (Free)
- 🟠 **<span style="color: #d97757;">Claude / Anthropic</span>** (Free)
- 🔵 **<span style="color: #4285f4;">Gemini / DeepMind</span>** (Free)
- ⚫ **<span style="color: #000000;">Grok / xAI</span>** 🤖
- 🔴 **<span style="color: #ff5a1f;">Mistral</span>** (Free)
- 🟣 **<span style="color: #a855f7;">DeepSeek</span>** 🤖
- 🔵 **<span style="color: #0668E1;">Meta / Llama</span>** (Free)
- 🟡 **<span style="color: #fbbf24;">Hugging Face</span>** (Free)

#### 🏷️ Conceptos Clave
- 🧠 **LLMs / SLMs**
- 🎨 **GenAI**
- 🤖 **Agents / Multi-Agent Systems**
- 📚 **RAG (Retrieval-Augmented Generation)**
- 🗣️ **NLP / Computer Vision**
- 🏗️ **Foundation Models**
- ⚙️ **Fine-tuning / LoRA**

### ⚙️ Configuración de Filtros por Defecto
- ⌨️ **CLI:** Filtrado automático habilitado por defecto (desactivable mediante flags).
- 🖥️ **UI:** Switch de **"Filtros AI"** en la interfaz, activo por defecto.

### 🛠️ Instrucciones de Procesamiento
1. **Detección:** Escaneo de contenido (insensible a mayúsculas).
2. **Etiquetado:** Generación de tags automáticos (ej. `#OpenAI`, `#DeepSeek`, `#Agents`).
3. **Resaltado:** Envolver términos en negritas (`**término**`) en la visualización del post.
4. **Orden de Prioridad:** El proceso de filtrado y etiquetado debe priorizar los elementos en el orden en que aparecen en las listas superiores.
```
