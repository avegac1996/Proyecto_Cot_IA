FROM python:3.13-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando por defecto (override en docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
