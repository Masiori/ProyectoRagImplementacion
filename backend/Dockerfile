# ============================================================
# Backend Dockerfile
# Imagen: Python 3.11 slim
# ============================================================
FROM python:3.11-slim

# Variables de entorno básicas de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema (mínimas; las ampliaremos en milestones posteriores
# cuando agreguemos parsing de PDFs, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python primero (mejor cacheo en builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Puerto que expone FastAPI
EXPOSE 8000

# Comando de arranque
# --reload activo en desarrollo (lo desactivaremos en producción vía override)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
