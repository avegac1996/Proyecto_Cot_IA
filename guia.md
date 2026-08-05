# GUIA DEL PROYECTO - COTIA (Sistema de Cotizaciones de Componentes Electronicos)

## INDICE
1. [Descripcion General](#descripcion-general)
2. [Lista Completa de Cambios](#lista-completa-de-cambios)
3. [Preguntas que hizo el Ingeniero](#preguntas-que-hizo-el-ingeniero)
4. [Posibles Preguntas que puede hacer el Ingeniero](#posibles-preguntas)
5. [Estructura del Proyecto](#estructura-del-proyecto)
6. [Web Scraping - Donde esta y como funciona](#web-scraping)
7. [Subida de Audios - Donde esta y como funciona](#subida-de-audios)
8. [Conexion Frontend-Backend](#conexion-frontend-backend)
9. [Lectura de Imagenes - Como funciona](#lectura-de-imagenes)
10. [Inteligencia Artificial - Donde esta](#inteligencia-artificial)
11. [Endpoints del Backend](#endpoints-del-backend)
12. [Que hace cada linea de codigo - Resumen por archivo](#que-hace-cada-linea)

---

## DESCRIPCION GENERAL

COTIA es un sistema web que permite a una tienda de electronica (AV Electronics) generar cotizaciones automaticas. El cliente envia una lista de componentes (por texto, voz, imagen o archivo), el sistema identifica cada componente, busca precios en la tienda propia y en tiendas competidoras mediante web scraping, aplica margen de ganancia, y genera una cotizacion con PDF y Excel.

**Stack tecnologico:**
- **Backend:** Python, FastAPI, SQLAlchemy (async), PostgreSQL, Docker
- **Frontend:** React, TypeScript, Vite, TailwindCSS
- **IA:** Google Gemini (Vision para imagenes, Chat para asistente)
- **Scraping:** BeautifulSoup (estatico), Playwright (dinamico), Wayback Machine (historico)
- **Audio:** OpenAI Whisper (transcripcion)

---

## LISTA COMPLETA DE CAMBIOS

### Cambios solicitados por el ingeniero y resueltos:

1. **Boton de recargar productos** - Se agrego un boton junto a la barra de busqueda para recargar productos scrapeados sin tener que recargar la pagina.
   - Archivo: `FRONTEND/src/modules/carga/CargaPage.tsx`
   - Endpoint: `POST /buscar` (limpia cache con `limpiar_cache_termino()`)

2. **Deduplicacion global de productos** - Evita que el mismo producto aparezca multiples veces en diferentes terminos de busqueda.
   - Archivo: `BACKEND/app/services/scraping/busqueda.py` (filtrado por relevancia)

3. **Prioridad AV Electronics** - Los productos de la tienda propia (AV Electronics) aparecen primero en los resultados, sin margen aplicado. Las tiendas externas tienen margen.
   - Archivo: `BACKEND/app/services/scraping/busqueda.py:161-202`

4. **Auto-agregar al carrito** - Al buscar, automaticamente se agrega al carrito la mejor opcion de cada componente con su cantidad.
   - Archivo: `FRONTEND/src/modules/carga/CargaPage.tsx`

5. **Extraer variantes (colores) de productos** - El scraper extrae variantes de productos WooCommerce (ej: LED en rojo, verde, amarillo).
   - Archivo: `BACKEND/app/services/scraping/scrapers/static_scraper.py:224-284`

6. **Aumentar limite de productos scrapeados a 10** - Se aumento de 5 a 10 el numero maximo de productos visitados por tienda.
   - Archivo: `BACKEND/app/services/scraping/scrapers/static_scraper.py:25`

7. **Mover boton recargar al header** - Se movio el boton de recargar al header de "Cotizar Componentes" para mejor UX.
   - Archivo: `FRONTEND/src/modules/carga/CargaPage.tsx`

8. **Opciones de envio configurables** - Se agrego la capacidad de configurar opciones de envio (recogida, Servientrega por zonas) desde el panel de administracion.
   - Backend: `BACKEND/app/api/v1/endpoints/configuracion.py` (endpoints GET/PUT `/configuracion/envio`)
   - Frontend: `FRONTEND/src/modules/admin/ConfiguracionPage.tsx`

9. **API Key de Gemini configurable** - La API key de Google Gemini se puede configurar desde el panel de administracion, con enmascarado y revelacion por contraseña.
   - Backend: `BACKEND/app/api/v1/endpoints/configuracion.py` (endpoints `/configuracion/gemini-key`)
   - Frontend: `FRONTEND/src/modules/admin/ConfiguracionPage.tsx`

10. **IVA en cotizaciones** - El IVA (configurable, actualmente 15%) se muestra en la tabla de cotizacion y se incluye en el total.
    - Frontend: `FRONTEND/src/modules/cotizacion/components/CotizacionTable.tsx`
    - Backend: `BACKEND/app/services/cotizacion/exporter.py` (PDF y Excel)

11. **Editar envio desde historial** - Desde el modal "Ver detalle" en el historial, se puede cambiar el tipo de envio de una cotizacion no finalizada.
    - Backend: `BACKEND/app/api/v1/endpoints/cotizacion.py:416-438` (PUT `/cotizacion/{id}/envio`)
    - Frontend: `FRONTEND/src/modules/historial/HistorialPage.tsx`

12. **No volver a pedir datos del cliente al editar** - Al usar "Agregar mas productos" en una cotizacion existente, no se vuelve a pedir los datos del cliente, solo el envio.
    - Frontend: `FRONTEND/src/modules/carga/CargaPage.tsx:510-517`

13. **Filtro y orden de seleccion en la busqueda** - Al buscar "2 led rojo", el sistema filtra por relevancia (color, tamaño, especificaciones) y ordena para que el producto mas relevante aparezca primero.
    - Archivo: `BACKEND/app/services/scraping/busqueda.py:35-123` (`_score_relevancia` y `_filtrar_y_ordenar_por_relevancia`)

14. **Sincronizacion con el carrito** - El producto pre-seleccionado coincide con la intencion de busqueda del usuario (ej: LED rojo, no amarillo).
    - Archivo: `FRONTEND/src/modules/carga/CargaPage.tsx` (auto-agregar mejor opcion)

15. **Limpiar cache en cada busqueda** - Cada nueva busqueda trae resultados frescos, no cacheados.
    - Archivo: `BACKEND/app/api/v1/endpoints/busqueda.py:77-78` (`limpiar_cache_termino()`)

16. **Todos los usuarios pueden ver todas las cotizaciones** - Cualquier usuario logueado puede ver el historial completo de cotizaciones.
    - Archivo: `BACKEND/app/api/v1/endpoints/cotizacion.py`

17. **Modo offline en historial** - El historial puede funcionar sin conexion mostrando datos cacheados.
    - Archivo: `FRONTEND/src/modules/historial/HistorialPage.tsx`

---

## PREGUNTAS QUE HIZO EL INGENIERO

1. **¿En donde esta el web scraping?**
   - Respuesta: En `BACKEND/app/services/scraping/`. La carpeta contiene:
     - `engine.py` - Motor principal que coordina el scraping
     - `busqueda.py` - Busqueda priorizada (AV Electronics primero)
     - `sugerencias.py` - Sugerencias cuando no hay resultados
     - `scrapers/` - Subcarpeta con los scrapers:
       - `base.py` - Clase base abstracta
       - `static_scraper.py` - Scraper con httpx + BeautifulSoup
       - `dynamic_scraper.py` - Scraper con Playwright para sitios con JS
       - `wayback_scraper.py` - Scraper con Wayback Machine

2. **¿En Donde esta el que se encarga de subir audios y como funciona?**
   - Respuesta: El endpoint de subida esta en `BACKEND/app/api/v1/endpoints/upload.py`. El servicio de transcripcion esta en `BACKEND/app/services/ingesta/audio.py`. Funciona asi:
     1. El usuario sube un archivo de audio (.mp3, .wav, .m4a, .ogg) desde el frontend
     2. El backend lo recibe en el endpoint `POST /upload` con tipo "audio"
     3. Se guarda temporalmente y se transcribe con OpenAI Whisper (modelo "base", idioma español)
     4. El texto transcrito se parsea con `parsear_texto()` para extraer componentes
     5. Se crea una sesion en la base de datos con los componentes detectados
   - En el frontend, la entrada de voz esta en `FRONTEND/src/modules/carga/components/` (componente de input de voz)

3. **¿Como lee las imagenes que subimos?**
   - Respuesta: Usa Google Gemini Vision. El flujo es:
     1. El usuario sube una imagen desde el frontend (tab "Imagen")
     2. El frontend la envia al endpoint `POST /buscar/imagen`
     3. El backend en `BACKEND/app/services/gemini/vision.py` codifica la imagen en base64
     4. Se envia a la API de Gemini (`gemini-flash-lite-latest`) con un prompt que le dice que identifique componentes electronicos
     5. Gemini devuelve una lista de componentes (uno por linea, formato "cantidad nombre")
     6. El texto se muestra en el frontend y el usuario puede buscar esos componentes
   - Nota: Tambien hay un endpoint legacy `POST /upload` con tipo "imagen" que usa Tesseract OCR, pero el flujo principal usa Gemini Vision.

4. **¿Donde esta la parte que conecta el frontend con el backend?**
   - Respuesta: La conexion esta en `FRONTEND/src/shared/lib/api.ts`. Usa Axios con:
     - `baseURL`: `http://localhost:8000/api/v1` (configurable via `VITE_API_URL`)
     - Interceptor de request: agrega el token JWT del `localStorage` en el header `Authorization`
     - Interceptor de response: si recibe 401, limpia el token y redirige a `/login`
   - Los servicios que usan esta conexion estan en:
     - `FRONTEND/src/modules/carga/services/busquedaService.ts` (busqueda, cotizacion, configuracion)
     - `FRONTEND/src/modules/historial/services/historialService.ts` (historial, detalle, envio)

5. **¿Que endpoints se utiliza?**
   - Ver seccion [Endpoints del Backend](#endpoints-del-backend) mas abajo.

6. **¿Que hace cada linea de codigo?**
   - Ver seccion [Que hace cada linea](#que-hace-cada-linea) mas abajo.

7. **¿La parte de la inteligencia artificial, donde esta?**
   - Respuesta: En `BACKEND/app/services/gemini/`. Contiene:
     - `vision.py` - Identifica componentes en imagenes usando Gemini Vision
     - `chat.py` - Asistente conversacional que responde preguntas sobre los resultados de busqueda usando Gemini Chat
   - El API key se configura desde el panel de admin en el frontend (`/admin/configuracion`)

---

## POSIBLES PREGUNTAS

### Arquitectura y estructura

1. **¿Cual es la arquitectura del proyecto?**
   - Backend: FastAPI (Python) con SQLAlchemy async, PostgreSQL en Docker
   - Frontend: React + TypeScript + Vite, con TailwindCSS
   - Comunicacion: REST API con JWT para autenticacion

2. **¿Por que usaron SQLAlchemy async?**
   - Porque FastAPI es async por naturaleza, y el scraping hace llamadas HTTP que son I/O-bound. Async permite hacer scraping paralelo a multiples tiendas sin bloquear.

3. **¿Como manejan la base de datos?**
   - PostgreSQL en Docker. Migraciones con Alembic. Modelos en `BACKEND/app/models/`.

4. **¿Que patrones de diseño usan?**
   - Repository pattern (servicios separados de endpoints)
   - Factory pattern (`get_scraper()` devuelve el scraper adecuado)
   - Strategy pattern (StaticScraper, DynamicScraper, WaybackScraper)

### Web Scraping

5. **¿Como funciona el web scraping?**
   - Ver seccion [Web Scraping](#web-scraping) abajo.

6. **¿Que pasa si una tienda no responde?**
   - Hay un timeout de 45 segundos (`SCRAPE_TIMEOUT_SECONDS`). Si expira, se loguea una advertencia y se devuelve vacio para esa tienda.

7. **¿Como evitan que el scraping sea lento?**
   - Scraping paralelo con `asyncio.gather()` - todas las tiendas se scrapean al mismo tiempo
   - Cache en memoria (TTL 2 min) y cache en BD (`ScrapingCache` con TTL configurable por tienda)

8. **¿Como manejan sitios que usan JavaScript?**
   - Si la tienda tiene `usa_javascript=True`, se usa `DynamicScraper` con Playwright

9. **¿Que es el Wayback Scraper?**
   - Un scraper que usa el Wayback Machine de Internet Archive para acceder a versiones archivadas de paginas que ya no existen o han cambiado.

10. **¿Como aplican el margen de ganancia?**
    - La tienda propia (AV Electronics) no tiene margen. Las tiendas externas se les aplica el margen configurable (ej: 30%) multiplicando `precio_base * (1 + margen/100)`.

### Busqueda y filtrado

11. **¿Como identifica los componentes del texto del cliente?**
    - Usa n-grams (ventanas de 3, 2, 1 palabras) contra un diccionario de tipos de componentes. Archivo: `BACKEND/app/services/ingesta/filtro.py`.

12. **¿Como filtra para que "LED rojo" no muestre "LED amarillo"?**
    - Usa un sistema de scoring de relevancia (`_score_relevancia`) que puntua cada producto segun cuantos descriptores (color, tamaño, especificacion) coinciden. Los que mas coinciden aparecen primero. Archivo: `BACKEND/app/services/scraping/busqueda.py:35-66`.

13. **¿Que pasa si no encuentra un componente?**
    - Genera una sugerencia usando `sugerir_termino()` que busca terminos similares.

### Cotizacion

14. **¿Como se calcula el total de la cotizacion?**
    - Total = Suma(subtotal de cada item) + Envio. El IVA se calcula sobre (Subtotal + Envio) y se muestra por separado.
    - `Total a pagar = Subtotal + Envio + IVA`

15. **¿Como se genera el PDF?**
    - En `BACKEND/app/services/cotizacion/exporter.py` usando `reportlab`. Incluye tabla de items, subtotal, envio, IVA y total.

16. **¿Se puede editar una cotizacion despues de creada?**
    - Si, mientras este "pendiente". Se puede: agregar mas productos, cambiar el envio. Una vez "finalizada" no se puede modificar (bloqueo con HTTP 409).

### Inteligencia Artificial

17. **¿Que modelo de Gemini usan?**
    - `gemini-flash-lite-latest` (rapido y economico).

18. **¿Como protegen la API key de Gemini?**
    - Se almacena en la base de datos (tabla configuracion). En el frontend se muestra enmascarada. Para revelarla hay que ingresar la contraseña de admin.

19. **¿Que hace el asistente IA (chat)?**
    - Responde preguntas sobre los componentes encontrados en la busqueda. No responde preguntas fuera del contexto de los resultados. Tiene historial de conversacion (ultimos 6 mensajes).

### Seguridad

20. **¿Como funciona la autenticacion?**
    - JWT (JSON Web Token). Login en `POST /auth/login` devuelve un token. El token se guarda en `localStorage` y se envia en cada request en el header `Authorization: Bearer <token>`.

21. **¿Quien puede ver las cotizaciones?**
    - Cualquier usuario autenticado. No hay filtro por usuario.

22. **¿Quien puede administrar?**
    - Solo usuarios con rol "admin" (rutas protegidas con `AdminRoute` en el frontend y `require_admin` en el backend).

---

## ESTRUCTURA DEL PROYECTO

```
repost/
├── BACKEND/
│   ├── app/
│   │   ├── api/v1/endpoints/     # Endpoints de la API
│   │   │   ├── auth.py           # Login, refresh, me
│   │   │   ├── busqueda.py       # Buscar componentes, imagen, preguntar IA
│   │   │   ├── configuracion.py  # Margen, IVA, envio, Gemini key
│   │   │   ├── cotizacion.py     # CRUD cotizaciones, PDF, Excel
│   │   │   ├── tiendas.py        # CRUD tiendas
│   │   │   ├── upload.py         # Subida de archivos (audio, imagen, texto)
│   │   │   └── usuarios.py       # CRUD usuarios
│   │   ├── core/                 # Configuracion, seguridad, database
│   │   ├── models/               # Modelos SQLAlchemy
│   │   ├── schemas/              # Schemas Pydantic
│   │   └── services/             # Logica de negocio
│   │       ├── configuracion.py  # Margen, IVA, envio, Gemini key
│   │       ├── cotizacion/       # Generador, exporter (PDF/Excel)
│   │       ├── gemini/           # IA - Vision y Chat
│   │       ├── ingesta/          # Audio, imagen, texto, filtro
│   │       ├── matching/         # Normalizador de componentes
│   │       └── scraping/         # Web scraping
│   │           ├── engine.py     # Motor de scraping
│   │           ├── busqueda.py   # Busqueda priorizada
│   │           ├── sugerencias.py
│   │           └── scrapers/     # Scrapers especificos
│   ├── tests/                    # Pruebas
│   ├── Dockerfile
│   └── requirements.txt
├── FRONTEND/
│   ├── src/
│   │   ├── app/                  # Router y shell
│   │   │   ├── AppRouter.tsx     # Rutas principales
│   │   │   └── AppShell.tsx      # Layout con sidebar
│   │   ├── modules/
│   │   │   ├── carga/            # Pagina principal de busqueda
│   │   │   │   ├── CargaPage.tsx
│   │   │   │   ├── components/   # CarritoPreview, EnvioModal, etc
│   │   │   │   └── services/     # busquedaService.ts
│   │   │   ├── cotizacion/       # Pagina de cotizacion
│   │   │   │   ├── CotizacionPage.tsx
│   │   │   │   └── components/   # CotizacionTable
│   │   │   ├── historial/        # Historial de cotizaciones
│   │   │   │   ├── HistorialPage.tsx
│   │   │   │   └── services/     # historialService.ts
│   │   │   ├── admin/            # Panel de administracion
│   │   │   ├── login/            # Login
│   │   │   └── usuarios/         # Gestion de usuarios
│   │   └── shared/
│   │       ├── lib/api.ts        # Cliente Axios (conexion backend)
│   │       ├── types/index.ts    # Tipos TypeScript
│   │       └── store/            # Zustand (auth)
│   └── package.json
└── test/                         # Imagenes de prueba
```

---

## WEB SCRAPING

**Ubicacion:** `BACKEND/app/services/scraping/`

### Como funciona paso a paso:

1. **El usuario busca componentes** (texto, voz, imagen o archivo)
2. **Se extraen los componentes** del texto con `extraer_componentes()` en `ingesta/filtro.py`
3. **Por cada componente**, se llama a `buscar_por_termino_priorizado()` en `scraping/busqueda.py`
4. **Se busca en todas las tiendas activas** en paralelo con `asyncio.gather()`:
   - Cada tienda usa el scraper adecuado (`get_scraper()` en `scrapers/__init__.py`):
     - `StaticScraper` - httpx + BeautifulSoup para sitios estaticos
     - `DynamicScraper` - Playwright para sitios con JavaScript
     - `WaybackScraper` - Wayback Machine para sitios archivados
5. **El scraper construye la URL de busqueda** con `_build_search_url()` y hace HTTP GET
6. **Parsea el HTML** con BeautifulSoup buscando:
   - `product_card` - selector CSS de cada tarjeta de producto
   - `price` - selector del precio
   - `product_url` - selector del link al producto
   - `availability` - selector de disponibilidad
7. **Si el precio no esta en la pagina de busqueda**, visita la pagina de cada producto (hasta 10)
8. **Detecta productos variables** (WooCommerce) y extrae cada variante con su precio
9. **Los resultados se filtran por relevancia** (`_filtrar_y_ordenar_por_relevancia`) segun descriptores (color, tamaño)
10. **Se aplica margen** a tiendas externas, AV Electronics sin margen
11. **Se ordenan**: AV Electronics primero, luego por relevancia o precio

### Cache:
- **Cache en memoria** (`_cache_termino`): TTL 2 minutos. Se limpia en cada busqueda nueva.
- **Cache en BD** (`ScrapingCache`): TTL configurable por tienda (ej: 24 horas).

### Selectores de tiendas:
Se configuran en la tabla `tiendas` de la BD. Cada tienda tiene:
- `url_base`: URL del sitio
- `selectores`: JSON con selectores CSS (`product_card`, `price`, `product_url`, `availability`, `search_url`)
- `usa_javascript`: booleano para usar Playwright
- `ttl_horas`: TTL del cache en BD

---

## SUBIDA DE AUDIOS

**Ubicacion:** 
- Endpoint: `BACKEND/app/api/v1/endpoints/upload.py`
- Servicio: `BACKEND/app/services/ingesta/audio.py`

### Como funciona:

1. El usuario selecciona la tab "Hablar" en el frontend
2. Graba audio desde el microfono (Web Speech API o grabacion de archivo)
3. El archivo de audio (.mp3, .wav, .m4a, .ogg) se envia al endpoint `POST /upload` con `tipo=audio`
4. El backend valida la extension y el tamaño (maximo configurable)
5. Se guarda el audio en un archivo temporal
6. Se transcribe con **OpenAI Whisper** (modelo "base", idioma español):
   ```python
   model = whisper.load_model("base")
   result = model.transcribe(tmp_path, language="es")
   ```
7. El texto transcrito se parsea con `parsear_texto()` para extraer componentes
8. Se crea una sesion en la BD con los componentes detectados
9. El frontend recibe la lista de componentes y los muestra

**Nota:** Whisper requiere `pip install openai-whisper` y `ffmpeg` instalado en el sistema.

---

## CONEXION FRONTEND-BACKEND

**Ubicacion:** `FRONTEND/src/shared/lib/api.ts`

### Como funciona:

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})
```

1. **Cliente Axios** con baseURL `http://localhost:8000/api/v1`
2. **Interceptor de request**: Agrega el token JWT del `localStorage` en cada peticion:
   ```typescript
   const token = localStorage.getItem('cotia_token')
   if (token) config.headers.Authorization = `Bearer ${token}`
   ```
3. **Interceptor de response**: Si recibe HTTP 401 (no autorizado):
   - Limpia el token del localStorage
   - Redirige a `/login`

### Servicios que usan la conexion:

- **`busquedaService.ts`**: `buscarComponentes()`, `identificarImagen()`, `crearCotizacionDesdeCarrito()`, `getConfiguracion()`, `getOpcionesEnvio()`, `getGeminiApiKey()`, etc.
- **`historialService.ts`**: `getHistorial()`, `getCotizacionById()`, `eliminarCotizacion()`, `descargarPDF()`, `finalizarCotizacion()`, `actualizarEnvio()`, etc.

### Rutas del frontend (AppRouter.tsx):
- `/login` - LoginPage
- `/carga` - CargaPage (busqueda y carrito)
- `/historial` - HistorialPage (historial de cotizaciones)
- `/usuarios` - UsuariosPage (solo admin)
- `/admin/configuracion` - ConfiguracionPage (solo admin)
- `/admin/tiendas` - TiendasPage (solo admin)

---

## LECTURA DE IMAGENES

**Ubicacion:** `BACKEND/app/services/gemini/vision.py`

### Como funciona:

1. El usuario sube una imagen desde la tab "Imagen" en el frontend
2. El componente `ImageInput` envia la imagen al endpoint `POST /buscar/imagen`
3. El backend recibe la imagen, valida que sea tipo imagen y menos de 10MB
4. Se llama a `identificar_componentes_imagen()` en `gemini/vision.py`:
   - Se codifica la imagen en base64
   - Se construye un payload con:
     - Un prompt: "Eres un experto en electronica. Analiza esta imagen e identifica TODOS los componentes electronicos..."
     - La imagen en base64 como `inline_data`
   - Se envia a la API de Google Gemini (`gemini-flash-lite-latest`)
   - Temperature: 0.1 (respuestas deterministicas)
   - Max output tokens: 1024
5. Gemini devuelve un texto con un componente por linea (formato: "cantidad nombre")
6. El backend separa las lineas y devuelve `{ texto: "...", componentes: ["3 Arduino Uno", "2 Sensor HC-SR04", ...] }`
7. El frontend muestra el texto y el usuario puede buscar esos componentes

**API Key:** Se obtiene de la BD con `obtener_gemini_api_key()`. Se configura desde el panel de admin.

---

## INTELIGENCIA ARTIFICIAL

**Ubicacion:** `BACKEND/app/services/gemini/`

### Dos funcionalidades de IA:

#### 1. Vision (identificar componentes en imagenes)
- **Archivo:** `gemini/vision.py`
- **Modelo:** `gemini-flash-lite-latest`
- **Funcion:** `identificar_componentes_imagen(image_bytes, mime_type)`
- **Endpoint:** `POST /buscar/imagen`
- **Como funciona:** Envia la imagen en base64 a Gemini con un prompt especializado en electronica. Gemini identifica los componentes y devuelve una lista.

#### 2. Chat (asistente conversacional)
- **Archivo:** `gemini/chat.py`
- **Modelo:** `gemini-flash-lite-latest`
- **Funcion:** `preguntar_agente(pregunta, resultados, historial)`
- **Endpoint:** `POST /buscar/preguntar`
- **Como funciona:**
  1. Construye un contexto con los resultados de busqueda actuales
  2. Usa un system prompt que limita las respuestas a componentes electronicos
  3. Incluye el historial de la conversacion (ultimos 6 mensajes)
  4. Envía la pregunta a Gemini
  5. Devuelve la respuesta
- **Restriccion:** Solo responde sobre los componentes de los resultados de busqueda, no preguntas generales.

### Configuracion de API Key:
- Se almacena en la tabla `configuracion` de la BD
- Se configura desde `/admin/configuracion` en el frontend
- En el frontend se muestra enmascarada (ej: `AIza***...***`)
- Para revelarla hay que ingresar la contraseña de admin
- Endpoints: `GET /configuracion/gemini-key`, `POST /configuracion/gemini-key/revelar`, `PUT /configuracion/gemini-key`

---

## ENDPOINTS DEL BACKEND

### Autenticacion (`/auth`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| POST | `/auth/login` | Login con email y password, devuelve JWT |
| GET | `/auth/me` | Informacion del usuario actual |
| POST | `/auth/refresh` | Renovar token JWT |

### Busqueda (`/buscar`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| POST | `/buscar` | Buscar componentes desde texto libre |
| POST | `/buscar/imagen` | Identificar componentes desde imagen (Gemini Vision) |
| POST | `/buscar/preguntar` | Preguntar al asistente IA (Gemini Chat) |
| POST | `/buscar/alternativas` | Buscar alternativas cuando un producto esta agotado |

### Upload (`/upload`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| POST | `/upload` | Subir archivo (audio, imagen, texto) y extraer componentes |

### Cotizacion (`/cotizacion`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| POST | `/cotizacion/desde-carrito` | Crear/actualizar cotizacion desde el carrito |
| GET | `/cotizaciones` | Listar cotizaciones (paginado, con filtros) |
| GET | `/cotizacion/by-id/{id}` | Obtener cotizacion por ID |
| POST | `/cotizacion/{id}/agregar` | Agregar item a cotizacion existente |
| PUT | `/cotizacion/{id}/envio` | Actualizar envio de cotizacion existente |
| POST | `/cotizacion/{id}/finalizar` | Finalizar cotizacion (bloquea edicion) |
| DELETE | `/cotizacion/{id}` | Eliminar cotizacion |
| GET | `/cotizacion/{id}/pdf` | Descargar PDF de cotizacion |
| GET | `/cotizacion/{id}/excel` | Descargar Excel de cotizacion |

### Configuracion (`/configuracion`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| GET | `/configuracion` | Obtener configuracion (margen, IVA, tienda propia) |
| PUT | `/configuracion/margen` | Actualizar margen de ganancia |
| PUT | `/configuracion/iva` | Actualizar porcentaje de IVA |
| GET | `/configuracion/envio` | Obtener opciones de envio |
| PUT | `/configuracion/envio` | Actualizar opciones de envio (solo admin) |
| GET | `/configuracion/gemini-key` | Obtener API key de Gemini (enmascarada) |
| POST | `/configuracion/gemini-key/revelar` | Revelar API key (requiere password) |
| PUT | `/configuracion/gemini-key` | Actualizar API key de Gemini |

### Tiendas (`/tiendas`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| GET | `/tiendas` | Listar tiendas |
| POST | `/tiendas` | Crear tienda |
| PUT | `/tiendas/{id}` | Actualizar tienda |
| DELETE | `/tiendas/{id}` | Eliminar tienda |

### Usuarios (`/usuarios`)
| Metodo | Path | Descripcion |
|--------|------|-------------|
| GET | `/usuarios` | Listar usuarios |
| POST | `/usuarios` | Crear usuario |
| PUT | `/usuarios/{id}` | Actualizar usuario |
| DELETE | `/usuarios/{id}` | Eliminar usuario |

---

## QUE HACE CADA LINEA

### Resumen por archivo clave:

#### `BACKEND/app/services/scraping/engine.py`
- `buscar_precios()`: Busca precios de un producto en todas las tiendas. Primero revisa cache en BD, luego hace scraping en vivo.
- `buscar_por_termino()`: Busca un termino libre en todas las tiendas activas. Usa cache en memoria (2 min TTL) y scraping paralelo.
- `_scrape_tienda()`: Scrapea una sola tienda con timeout de 45 segundos.
- `limpiar_cache_termino()`: Limpia el cache en memoria.

#### `BACKEND/app/services/scraping/busqueda.py`
- `_normalizar_texto()`: Convierte a minusculas, sin tildes, normaliza unidades (ohm, amarrillo→amarillo).
- `_palabra_en_texto()`: Verifica coincidencia de palabra completa (no substring).
- `_score_relevancia()`: Puntua que tan relevante es un producto segun descriptores. +10 por coincidencia exacta, +3 por palabra, +5 por numero.
- `_filtrar_y_ordenar_por_relevancia()`: Filtra y ordena opciones por score de relevancia. Si hay match con descriptores, muestra solo esos.
- `buscar_por_termino_priorizado()`: Funcion principal. Busca termino, filtra por relevancia, fallback con termino base, aplica margen, prioriza AV Electronics.

#### `BACKEND/app/services/scraping/scrapers/static_scraper.py`
- `scrape()`: Hace HTTP GET a la URL de busqueda, parsea HTML con BeautifulSoup, extrae productos. Si el precio no esta en busqueda, visita la pagina del producto.
- `_scrape_product_page()`: Visita la pagina de un producto simple y extrae precio y disponibilidad.
- `_scrape_variable_product()`: Extrae variantes de un producto WooCommerce desde `data-product_variations` JSON.

#### `BACKEND/app/services/ingesta/filtro.py`
- `_normalizar()`: Lowercase, sin tildes, sin puntuacion.
- `_construir_diccionario_busqueda()`: Construye diccionario de terminos conocidos (componentes, colores, tamaños).
- `_extraer_cantidad()`: Busca un numero antes del componente en el texto.
- `_buscar_descriptores()`: Busca colores, tamaños y especificaciones adyacentes al componente.
- `extraer_componentes()`: Funcion principal. Usa n-grams (3→2→1) para identificar componentes en texto libre.

#### `BACKEND/app/services/gemini/vision.py`
- `identificar_componentes_imagen()`: Codifica imagen en base64, envia a Gemini Vision con prompt especializado, devuelve texto con componentes.

#### `BACKEND/app/services/gemini/chat.py`
- `_build_context()`: Construye texto con los resultados de busqueda para dar contexto a Gemini.
- `preguntar_agente()`: Envia pregunta + contexto + historial a Gemini Chat, devuelve respuesta.

#### `BACKEND/app/api/v1/endpoints/busqueda.py`
- `buscar_componentes()`: Endpoint principal. Recibe texto, extrae componentes, busca en tiendas, devuelve resultados.
- `identificar_imagen()`: Endpoint para imagenes. Recibe imagen, envia a Gemini Vision, devuelve componentes.
- `preguntar()`: Endpoint del asistente IA. Recibe pregunta + resultados, envia a Gemini Chat.
- `buscar_alternativas()`: Busca productos similares cuando uno esta agotado.

#### `BACKEND/app/api/v1/endpoints/cotizacion.py`
- `_to_response()`: Convierte modelo Cotizacion a CotizacionResponse.
- `crear_desde_carrito()`: Crea o actualiza cotizacion desde items del carrito.
- `listar_cotizaciones()`: Lista cotizaciones con paginacion y filtros.
- `obtener_por_id()`: Obtiene una cotizacion por ID.
- `agregar_item()`: Agrega un item a una cotizacion existente.
- `actualizar_envio_cotizacion()`: Actualiza solo el envio de una cotizacion.
- `finalizar_cotizacion()`: Cambia estado a "finalizada" (bloquea edicion).
- `descargar_pdf()`: Genera y devuelve PDF.
- `descargar_excel()`: Genera y devuelve Excel.

#### `FRONTEND/src/shared/lib/api.ts`
- Crea instancia de Axios con baseURL del backend.
- Interceptor de request: agrega token JWT.
- Interceptor de response: maneja 401 redirigiendo a login.

#### `FRONTEND/src/modules/carga/CargaPage.tsx`
- Pagina principal. Maneja: busqueda por texto/voz/imagen/archivo, carrito, modales de cliente y envio, creacion de cotizacion.
- `handleBuscar()`: Llama a `buscarComponentes()` y procesa resultados.
- `handleFinalizar()`: Llama a `crearCotizacionDesdeCarrito()` y navega al historial.
- Al editar cotizacion existente: pre-carga datos del cliente, salta modal de cliente.

#### `FRONTEND/src/modules/historial/HistorialPage.tsx`
- Lista cotizaciones con paginacion, busqueda y filtros de fecha.
- Modal de detalle con tabla de items, subtotal, envio y total.
- Boton "Cambiar envio" para cotizaciones no finalizada.
- Boton "Agregar mas productos" que navega a CargaPage con el ID de la cotizacion.

#### `FRONTEND/src/modules/cotizacion/components/CotizacionTable.tsx`
- Tabla que muestra items de la cotizacion.
- Footer con Subtotal, Envio (nombre y precio), IVA (si > 0) y Total calculado.

---

## NOTAS PARA PRESENTACION

- El proyecto corre con Docker (backend) y Vite (frontend)
- Backend: `docker compose up` en la carpeta BACKEND
- Frontend: `npm run dev` en la carpeta FRONTEND
- Usuario admin: `admin@cotia.com` / `Admin123!`
- Usuario normal: `user@cotia.com` / `User123!`
- Las pruebas de funcionalidad estan en `BACKEND/run_tests.py`, `run_tests_full.py` y `run_tests_frontend.py`
- Las imagenes de prueba estan en `test/` (Test_1 a Test_5)
- Rama de pruebas: `feature/pruebas`
