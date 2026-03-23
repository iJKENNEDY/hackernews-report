# Documentación de Despliegue

Hacker News Report se puede desplegar tanto localmente como utilizando Docker.

## Despliegue con Docker (Recomendado)

Asegúrate de tener instalados Docker y Docker Compose.

1.  **Construir e iniciar los servicios**:
    ```bash
    docker-compose up --build
    ```
2.  La aplicación estará disponible en `http://localhost:5000`.
3.  Los datos se persistirán en el directorio local `./data`.

## Instalación Local

### Requisitos
- Python 3.12 o superior
- Pip o UV (gestor de paquetes)

### Pasos

1.  **Crear y activar entorno virtual**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/MacOS
    source .venv/bin/activate
    ```
2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Ejecutar la aplicación Web**:
    ```bash
    python src/web_app.py
    ```
4.  **Usar la CLI**:
    ```bash
    python -m src.cli --help
    ```

## Variables de Entorno
- `FLASK_APP`: `src/web_app.py`
- `PORT`: Puerto de escucha (default 5000)
- `PYTHONPATH`: Debe incluir el directorio raíz para importar `src`.
