# CotIA — Sistema Inteligente de Cotización de Componentes Electrónicos

Sistema web que automatiza la cotización de componentes electrónicos a partir de listas recibidas en texto, audio o imagen. Procesa la información, identifica ambigüedades, consulta precios en tiendas online mediante web scraping, y genera cotizaciones formales descargables en PDF y Excel.

## Características

- **Ingesta multimodal**: texto (.txt, .csv), audio (.mp3, .wav, .m4a) con Whisper, imagen (.jpg, .png) con Tesseract OCR
- **Normalización inteligente**: traduce términos coloquiales a productos estandarizados
- **Resolución de ambigüedades**: hace preguntas al usuario para completar datos faltantes
- **Web scraping multi-tienda**: BeautifulSoup (estático) y Playwright (dinámico) con cache en PostgreSQL
- **Comparación de precios**: muestra precios por proveedor con margen configurable (5% por defecto)
- **Descarga de cotización**: PDF (ReportLab) y Excel (openpyxl)
- **Histórico de cotizaciones**: guarda cotizaciones previas para evitar scraping repetido
- **Autenticación JWT**: dos roles (admin, user) con usuarios por defecto
- **Gestión de usuarios**: admin crea y desactiva usuarios

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL |
| Frontend | React + Vite + TailwindCSS + Zustand |
| Scraping | httpx + BeautifulSoup4 (estático), Playwright (dinámico) |
| Ingesta | Whisper (audio), Tesseract OCR (imagen) |
| Export | ReportLab (PDF), openpyxl (Excel) |
| Migraciones | Alembic |
| Deploy | Docker + Docker Compose + Nginx |

## Tiendas Soportadas

| Tienda | URL | Tipo | Scraping |
|---|---|---|---|
| AV Electronics | https://avelectronics.cc/ | WooCommerce | Estático (httpx) |
| Megatronica | https://megatronica.cc/ | WooCommerce + JS | Dinámico (Playwright) |

## Inicio Rápido (Desarrollo)

### Prerrequisitos

- Docker + Docker Compose
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/avegac1996/Proyecto_Cot_IA.git
cd Proyecto_Cot_IA

# 2. Configurar variables de entorno
cp BACKEND/.env.example BACKEND/.env
cp FRONTEND/.env.example FRONTEND/.env

# 3. Levantar servicios
docker compose up -d --build

# 4. Verificar
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:5173
# pgAdmin: http://localhost:5050
```

### Usuarios por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123!` | admin |
| `user` | `User123!` | user |

## Despliegue en Producción

```bash
# 1. Configurar .env con variables de producción
# 2. Levantar con el compose de producción
docker compose -f docker-compose.prod.yml up -d --build

# 3. Ejecutar migraciones (se ejecutan automáticamente en el comando del backend)
# 4. Configurar certificados SSL en nginx/certs/ y descomentar HTTPS en nginx/nginx.conf
```

## Estructura del Proyecto

```
Proyecto_Cot_IA/
├── BACKEND/
│   ├── alembic/                    # Migraciones de BD
│   ├── app/
│   │   ├── api/v1/endpoints/       # Endpoints REST
│   │   ├── core/                   # Config, database, security
│   │   ├── models/                 # Modelos SQLAlchemy
│   │   ├── schemas/                # Schemas Pydantic
│   │   └── services/
│   │       ├── cotizacion/         # Generador + Exportador
│   │       ├── ingesta/            # Texto, Audio (Whisper), Imagen (OCR)
│   │       ├── matching/           # Normalizador
│   │       ├── preguntas/          # Selector de preguntas
│   │       └── scraping/           # Engine + Scrapers
│   ├── tests/                      # Tests con pytest
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
├── FRONTEND/
│   ├── src/
│   │   ├── modules/                # Carga, Preguntas, Cotización, Historial, Usuarios
│   │   └── shared/                 # Components, lib, store, types
│   ├── Dockerfile                  # Desarrollo
│   ├── Dockerfile.prod             # Producción (build estático + Nginx)
│   └── package.json
├── nginx/
│   └── nginx.conf                  # Configuración Nginx para producción
├── .github/workflows/ci.yml        # CI/CD con GitHub Actions
├── docker-compose.yml              # Desarrollo
├── docker-compose.prod.yml         # Producción
└── instructivo/
    └── arquitectura.md             # Documento de arquitectura completo
```

## Testing

```bash
# Backend
cd BACKEND
pip install -r requirements.txt pytest pytest-asyncio
pytest -v

# Frontend
cd FRONTEND
npm ci
npx tsc --noEmit
npm run build
```

## API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/auth/login` | Iniciar sesión |
| GET | `/api/v1/auth/me` | Usuario actual |
| POST | `/api/v1/upload` | Cargar archivo (texto/audio/imagen) |
| GET | `/api/v1/preguntas/{session_id}` | Obtener preguntas |
| POST | `/api/v1/preguntas/{session_id}/responder` | Responder preguntas |
| POST | `/api/v1/cotizacion/{session_id}` | Generar cotización |
| GET | `/api/v1/cotizacion/{session_id}` | Obtener cotización |
| GET | `/api/v1/cotizacion/{id}/pdf` | Descargar PDF |
| GET | `/api/v1/cotizacion/{id}/excel` | Descargar Excel |
| GET | `/api/v1/cotizaciones` | Listar cotizaciones |
| GET/POST | `/api/v1/usuarios` | Gestión de usuarios (admin) |

## Licencia

Proyecto privado — Uso interno.
