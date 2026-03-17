# Usar una imagen oficial de Python ligera
FROM python:3.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación y plantillas
COPY src/ src/
COPY templates/ templates/
COPY static/ static/

# Crear directorio para la base de datos y persistencia
RUN mkdir -p data

# Exponer el puerto donde corre Flask
EXPOSE 5000

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src/web_app.py
ENV PYTHONPATH=/app

# Comando para ejecutar la aplicación
CMD ["python", "src/web_app.py"]
