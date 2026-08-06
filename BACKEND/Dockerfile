FROM python:3.13-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libpq-dev \
    # Playwright/Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libdbus-1-3 \
    libatspi2.0-0 \
    libexpat1 \
    libgio-2.0-0 \
    libglib2.0-0 \
    libgobject-2.0-0 \
    # OCR (Tesseract)
    tesseract-ocr \
    # Audio processing (Whisper)
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python
COPY requirements.txt requirements-dev.txt .
RUN pip install --no-cache-dir setuptools==69.5.1 wheel
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt
# Instalar Whisper por separado (setup.py incompatible con build isolation en Python 3.13)
RUN pip install --no-cache-dir --no-build-isolation openai-whisper==20240930 || \
    pip install --no-cache-dir --no-build-isolation openai-whisper

# Instalar Chromium para Playwright
RUN playwright install chromium

# Código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando por defecto (override en docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
