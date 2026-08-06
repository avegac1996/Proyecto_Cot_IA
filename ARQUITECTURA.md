# Arquitectura y Funcionamiento — CotIA

Sistema de cotización automatizada de componentes electrónicos con scraping multi-tienda, reconocimiento de imágenes con IA, asistente conversacional y generación de cotizaciones en PDF/Excel.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI (Python 3.13), SQLAlchemy async, Pydantic |
| Frontend | React 18 + TypeScript, Vite, Tailwind CSS, Zustand |
| Base de Datos | PostgreSQL 16 |
| IA | Google Gemini Vision (`gemini-flash-lite-latest`) |
| PDF/Excel | ReportLab, openpyxl |
| Scraping | httpx + BeautifulSoup4 (estático), Playwright (dinámico), Wayback Machine |
| Contenedores | Docker Compose |
| Auth | JWT (python-jose); migración a bcrypt pendiente |

---

## Infraestructura Docker

```
docker-compose.yml
├── postgres       (BD principal, puerto 5432)
├── pgadmin        (Admin BD, puerto 5050)
├── backend        (FastAPI, puerto 8000, hot-reload)
└── frontend       (Vite dev server, puerto 5173, HMR)
```

---

## Estado operativo y límites actuales

- El despliegue activo usa PostgreSQL, pgAdmin, backend y frontend. **No usa Redis, Celery ni colas de tareas** porque no hay workers ni tareas Celery implementados en el código.
- El scraping se ejecuta bajo demanda. PostgreSQL conserva resultados por término y tienda con un TTL configurable; al vencer, la siguiente búsqueda refresca únicamente esa tienda.
- Redis/Celery quedan como una ampliación futura para refrescos programados, no como requisito de ejecución actual.
- Alembic es la única vía de evolución del esquema; el backend aplica `alembic upgrade head` al iniciar.

## Backend — Estructura

```
BACKEND/app/
├── main.py                  # App FastAPI, CORS, routers, lifespan
├── core/
│   ├── config.py            # Settings (Pydantic BaseSettings): DB URL, JWT, Gemini API key, márgenes
│   ├── database.py          # Engine async, sessionmaker, get_db dependency
│   └── security.py          # JWT create/verify; bcrypt pendiente
├── models/                  # Modelos SQLAlchemy ORM
│   ├── usuario.py           # Usuario (id, username, email, password_hash, rol, activo)
│   ├── sesion.py            # Sesion de búsqueda (id UUID, usuario_id, componentes_json)
│   ├── cotizacion.py        # Cotizacion + CotizacionItem (con cliente_nombre/correo/celular)
│   ├── tienda.py            # Tienda (nombre, base_url, selectors JSON, usa_javascript, use_wayback)
│   ├── producto.py          # Producto catalogado
│   ├── configuracion.py     # ConfiguracionNegocio (clave/valor: margen, tienda_propia, iva)
│   ├── banco_preguntas.py   # Preguntas de desambiguación
│   ├── equivalencia.py      # Equivalencias de componentes
│   └── scraping_cache.py    # Cache de resultados de scraping por tienda
├── schemas/                 # Pydantic schemas (request/response)
│   ├── cotizacion.py        # CotizacionResponse, CotizacionListItem (con usuario_nombre, cliente_*)
│   └── ...
├── api/v1/endpoints/        # Endpoints REST
│   ├── auth.py              # POST /auth/login, POST /auth/register
│   ├── busqueda.py          # POST /buscar, POST /buscar/imagen, POST /buscar/preguntar
│   ├── cotizacion.py        # CRUD cotizaciones, PDF, Excel, desde-carrito
│   ├── configuracion.py     # GET/PUT /configuracion (margen, tienda_propia, iva)
│   ├── tiendas.py           # CRUD tiendas (admin)
│   ├── usuarios.py          # CRUD usuarios (admin)
│   ├── productos.py         # CRUD productos
│   ├── preguntas.py         # Preguntas de desambiguación
│   ├── upload.py            # Upload de archivos (PDF, DOCX, XLSX)
│   └── health.py            # Health check
└── services/                # Lógica de negocio
    ├── configuracion.py     # Leer/actualizar margen, tienda_propia, iva
    ├── cotizacion/
    │   ├── generator.py     # Generar cotización desde sesión, agregar items, recalcular
    │   └── exporter.py      # PDF (con subtotal, IVA, total) y Excel
    ├── gemini/
    │   ├── vision.py        # Identificar componentes desde imagen (Gemini Vision)
    │   └── chat.py          # Asistente conversacional (Gemini, contexto de resultados)
    ├── scraping/
    │   ├── engine.py        # Orquestador: buscar_precios, buscar_por_termino (paralelizado)
    │   ├── busqueda.py      # Búsqueda priorizada (AV Electronics primero, externas con margen)
    │   ├── sugerencias.py   # Sugerencias cuando no hay resultados
    │   └── scrapers/
    │       ├── base.py      # Clase base: _build_search_url, _parse_price, _parse_availability
    │       ├── static_scraper.py   # httpx + BS4 para sitios estáticos
    │       ├── dynamic_scraper.py  # Playwright para sitios con JS
    │       └── wayback_scraper.py  # Wayback Machine para sitios con anti-bot
    ├── matching/            # Matching de componentes con catálogo
    ├── preguntas/           # Selector de preguntas de desambiguación
    └── ingesta/             # Ingesta de catálogos
```

### Flujo Principal del Backend

1. **Búsqueda** (`POST /buscar`):
   - Recibe texto con lista de componentes
   - Extrae componentes individuales
   - Para cada componente, busca en paralelo en todas las tiendas activas
   - AV Electronics (tienda propia) se busca sin margen; tiendas externas con margen configurable
   - Resultados se ordenan por precio y disponibilidad
   - Si no hay resultados exactos, Gemini propone un sinónimo que debe ser confirmado antes de una nueva búsqueda

2. **Cotización** (`POST /cotizacion/desde-carrito`):
   - Recibe items del carrito con tienda y precio seleccionados
   - Crea cotización con datos del cliente (nombre, correo, celular)
   - Si se envía `cotizacion_id`, agrega items a cotización existente (preserva datos del cliente)
   - Calcula total con subtotales por item

3. **PDF** (`GET /cotizacion/{id}/pdf`):
   - Lee IVA configurado de la BD
   - Genera PDF con: logo, datos del cliente, tabla de items, **Subtotal sin IVA**, **IVA (%)**, **Total con IVA**
   - Footer con datos de contacto de AV Electronics

4. **Asistente IA** (`POST /buscar/preguntar`):
   - Recibe pregunta + resultados de búsqueda + historial de mensajes
   - Construye contexto con los componentes encontrados (o términos sin resultados)
   - Envía a Gemini con system prompt restrictivo (solo responde sobre lo buscado)
   - Mantiene historial conversacional (últimos 6 mensajes)

5. **Reconocimiento de Imagen** (`POST /buscar/imagen`):
   - Recibe una imagen mediante `multipart/form-data`
   - Gemini Vision identifica componentes electrónicos
   - Retorna texto extraído y lista de componentes

---

## Frontend — Estructura

```
FRONTEND/src/
├── main.tsx                 # Entry point
├── app/
│   └── AppShell.tsx         # Layout: sidebar (desktop) / topbar+drawer (mobile), routing
├── modules/
│   ├── carga/               # Página principal de búsqueda y cotización
│   │   ├── CargaPage.tsx    # Página con tabs: texto, voz, imagen, archivo
│   │   ├── components/
│   │   │   ├── TarjetaProducto.tsx     # Card de resultado con opciones por tienda
│   │   │   ├── CarritoPreview.tsx      # Carrito lateral con items seleccionados
│   │   │   ├── ClienteModal.tsx        # Modal de datos del cliente (nombre, correo, celular)
│   │   │   ├── AgenteChat.tsx          # Chat IA desplegable (con/sin resultados)
│   │   │   ├── FileInput.tsx           # Upload PDF/DOCX/XLSX/TXT con extracción de texto
│   │   │   ├── ImageInput.tsx          # Upload imagen → Gemini Vision
│   │   │   ├── VoiceInput.tsx          # Input por voz (Web Speech API)
│   │   │   └── ...
│   │   └── services/
│   │       └── busquedaService.ts      # buscarComponentes, preguntarAgente, crearCotizacion, config
│   ├── historial/
│   │   ├── HistorialPage.tsx           # Tabla de cotizaciones (con columna Usuario)
│   │   └── services/historialService.ts
│   ├── admin/
│   │   └── ConfiguracionPage.tsx       # Configurar margen, IVA, tienda propia
│   ├── header/
│   │   ├── Header.tsx                  # Sidebar responsive con drawer móvil
│   │   ├── ThemeToggle.tsx             # Toggle dark/light
│   │   └── UserMenu.tsx                # Info usuario + logout
│   ├── footer/Footer.tsx
│   ├── login/LoginPage.tsx
│   ├── cotizacion/                     # Vista de cotización individual
│   ├── preguntas/                      # Preguntas de desambiguación
│   └── usuarios/                       # CRUD usuarios (admin)
├── shared/
│   ├── types/index.ts                  # Interfaces TypeScript (Cotizacion, ResultadoComponente, etc.)
│   ├── lib/api.ts                      # Instancia Axios con interceptor JWT
│   └── store/
│       ├── authStore.ts                # Zustand: auth state, token, user
│       └── uiStore.ts                  # Zustand: theme (light/dark)
└── styles/globals.css                  # Tailwind + variables CSS (--color-primary, etc.)
```

### Flujo Principal del Frontend

1. **CargaPage** — Página principal:
   - 4 métodos de input: texto, voz, imagen, archivo
   - Botón "Buscar componentes" + botón IA (icono Sparkles) al lado derecho
   - Al buscar, muestra resultados en `TarjetaProducto` con opciones por tienda
   - Usuario selecciona productos → van al `CarritoPreview`
   - Al generar cotización: abre `ClienteModal` para datos del cliente (si es nueva)
   - Si edita cotización existente: skip modal, preserva datos
   - `AgenteChat` se despliega al clic en botón IA (con o sin resultados)

2. **HistorialPage** — Historial de cotizaciones:
   - Tabla con columnas: #, Cliente, **Usuario**, Fecha, Ítems, Total, Estado, Acciones
   - Modal de detalle con datos del cliente
   - Acciones: ver detalle, descargar PDF, descargar Excel, agregar más productos, finalizar

3. **ConfiguracionPage** (admin) — Configuración:
   - Margen de competencia (%)
   - **IVA (%)** — se aplica en el PDF
   - Tienda propia (informativo)

4. **Header** — Navegación responsive:
   - Desktop: sidebar fijo a la izquierda
   - Mobile: top bar con hamburger → drawer overlay

---

## Modelos de Datos

### Usuario
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int PK | Auto-increment |
| username | str unique | Nombre de usuario |
| email | str unique | Email |
| password_hash | str | Actualmente texto plano; migración a bcrypt pendiente |
| rol | str | "admin" o "user" |
| activo | bool | Estado activo/inactivo |

### Cotizacion
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int PK | Auto-increment |
| session_id | UUID FK | Referencia a Sesion |
| usuario_id | int FK | Usuario que creó la cotización |
| cliente_nombre | str? | Nombre del cliente |
| cliente_correo | str? | Correo del cliente |
| cliente_celular | str? | Celular del cliente |
| estado | str | "borrador", "pendiente" o "finalizada" |
| total | Decimal | Subtotal sin IVA |
| fecha_creacion | datetime | Timestamp |

Una cotización comienza como `borrador` mientras se agregan búsquedas y productos. Solo cambia a `pendiente` al generar la cotización con nombre, correo y celular del cliente. Los borradores y cotizaciones incompletas no se muestran en el historial.

### CotizacionItem
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int PK | |
| cotizacion_id | int FK | |
| producto_nombre | str | |
| cantidad | int | |
| precio_unitario | Decimal | |
| proveedor | str | Tienda seleccionada |
| margen_aplicado | Decimal | |
| subtotal | Decimal | precio × cantidad |
| disponible | bool | |
| es_propio | bool | Es de AV Electronics |
| opciones_proveedores | JSON | Todas las opciones encontradas |

### Tienda
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int PK | |
| nombre | str | |
| base_url | str | |
| selectors | JSON | Selectores CSS/JS para scraping |
| activa | bool | |
| es_favorita | bool | Una sola tienda prioritaria; aparece primero en los resultados |
| usa_javascript | bool | Requiere Playwright |
| ttl_horas | int | Frecuencia máxima de refresco de su caché |

### ConfiguracionNegocio
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int PK | |
| clave | str unique | "margen_competencia", "tienda_propia", "iva" |
| valor | str | Valor almacenado |
| descripcion | str? | |

La clave `gemini_api_key` se guarda cifrada con Fernet y prefijo `enc:v1:`. La clave maestra `GEMINI_KEY_ENCRYPTION_KEY` permanece únicamente en el entorno. La clave efectiva es la de BD cifrada y, si no existe, `GEMINI_API_KEY` del entorno.

---

## API Endpoints

### Autenticación
- `POST /api/v1/auth/login` — Login, retorna JWT
- `POST /api/v1/auth/register` — Registro (admin)

### Búsqueda
- `POST /api/v1/buscar` — Buscar componentes por texto
- `POST /api/v1/buscar/imagen` — Identificar componentes desde imagen (Gemini Vision)
- `POST /api/v1/buscar/preguntar` — Asistente IA conversacional (Gemini)

### Cotización
- `POST /api/v1/cotizacion/desde-carrito` — Crear/actualizar desde carrito
- `POST /api/v1/cotizacion/borrador` — Crear el contexto persistente de una cotización en curso
- `POST /api/v1/cotizacion/{id}/contexto` — Agregar componentes reconocidos al borrador o cotización autorizada
- `GET /api/v1/cotizaciones` — Listar (con usuario_nombre)
- `GET /api/v1/cotizacion/by-id/{id}` — Obtener por ID
- `GET /api/v1/cotizacion/{id}/pdf` — Descargar PDF (con subtotal, IVA, total)
- `GET /api/v1/cotizacion/{id}/excel` — Descargar Excel
- `POST /api/v1/cotizacion/{id}/finalizar` — Finalizar cotización
- `DELETE /api/v1/cotizacion/{id}` — Eliminar cotización
- `PUT /api/v1/cotizacion/{id}/envio` — Actualizar envío
- `POST /api/v1/cotizacion/{id}/agregar` — Añadir un ítem manual
- `PUT /api/v1/cotizacion/item/{item_id}/seleccionar` — Seleccionar proveedor autorizado

### Configuración
- `GET /api/v1/configuracion` — Obtener (margen, tienda_propia, iva)
- `PUT /api/v1/configuracion/margen` — Actualizar margen (admin)
- `PUT /api/v1/configuracion/iva` — Actualizar IVA (admin)
- `GET/PUT /api/v1/configuracion/envio` — Consultar o actualizar opciones de envío
- `GET/PUT /api/v1/configuracion/gemini-key` — Consultar estado o guardar la clave Gemini cifrada
- `POST /api/v1/configuracion/gemini-key/revelar` — Revelar la clave solo tras validar contraseña de administrador

### Tiendas, Usuarios, Productos
- CRUD completo para admin

---

## Scraping — Flujo Detallado

1. `buscar_por_termino_priorizado(termino, db)`:
   - Busca en AV Electronics (tienda propia) **sin margen**
   - Busca en tiendas externas **con margen** aplicado
   - Ambas búsquedas en paralelo con `asyncio.gather`

2. `buscar_por_termino(db, termino)` consulta la caché por término y, cuando corresponde, delega el scraping a cada tienda activa. `buscar_precios(db, producto)` aplica el mismo patrón para productos catalogados:
   - Selecciona scraper según configuración de tienda:
     - `usa_javascript=False, use_wayback=False` → `StaticScraper` (httpx + BS4)
     - `usa_javascript=True` → `DynamicScraper` (Playwright)
     - `use_wayback=True` → `WaybackScraper` (Wayback Machine)
   - Todas las tiendas se scrapean en paralelo

3. Timeouts optimizados:
   - Static: 8s HTTP, máx 3 páginas de productos
   - Dynamic: 10s carga, 5s selector, domcontentloaded, máx 3 páginas
   - Wayback: 15s HTTP

4. Cache persistente en PostgreSQL (`scraping_cache`) por término, tienda y TTL. Se consulta antes de scrapear; una tienda favorita se ordena primero.

---

## Seguridad

- JWT con expiración configurable
- Las contraseñas aún requieren la migración pendiente a bcrypt; no debe considerarse el despliegue apto para producción hasta completarla.
- Roles: `admin` (acceso total) y `user` (solo sus cotizaciones)
- CORS restringido a orígenes configurados
- Endpoints de admin protegidos con `require_admin` dependency
