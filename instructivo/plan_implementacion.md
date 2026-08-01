# Plan de Implementación — Reingeniería CotIA

## Inventario completo del sistema actual (verificado)

### Backend (Python + FastAPI)

#### Modelos existentes (BD)

| Modelo | Tabla | Campos clave | Estado |
|---|---|---|---|
| `Usuario` | `usuarios` | id, username, email, password_hash, rol (admin/user), activo | ✅ Completo |
| `Sesion` | `sesiones` | id (UUID), usuario_id, componentes_json (JSONB), ambiguedades_resueltas, estado | ✅ Completo |
| `Producto` | `productos` | id, nombre, categoria, especificaciones (JSONB), terminos_coloquiales (ARRAY), activo | ✅ Completo |
| `Tienda` | `tiendas` | id, nombre, url_base, selectores (JSONB), activa, usa_javascript, ttl_horas | ✅ Completo |
| `ScrapingCache` | `scraping_cache` | id, producto_id (FK NOT NULL), tienda, precio, disponible, url_producto, fecha_consulta, ttl_horas | ⚠️ producto_id obligatorio — bloquea búsqueda por término |
| `Cotizacion` | `cotizaciones` | id, session_id, usuario_id, cliente_nombre, estado, total, items (relationship) | ✅ Completo |
| `CotizacionItem` | `cotizacion_items` | id, cotizacion_id, producto_id, producto_nombre, cantidad, precio_unitario, proveedor, margen_aplicado, subtotal, disponible, es_propio, seleccionado, opciones_proveedores (JSONB) | ✅ Completo |
| `BancoPregunta` | `banco_preguntas` | id, categoria, pregunta, campo_a_desambiguar, prioridad, activa | ✅ Completo |
| `Equivalencia` | `equivalencias` | id, producto_id, termino_equivalente, tipo_match, confianza | ✅ Completo |

#### Servicios existentes

| Archivo | Funciones | Estado |
|---|---|---|
| `normalizer.py` | `detectar_tipo`, `normalizar_valor`, `normalizar_unidad`, `aplicar_defaults`, `detectar_ambiguedades`, `aplicar_respuestas` | ✅ Con defaults (16 tipos) y máx. 2 preguntas |
| `texto.py` | `parsear_linea`, `parsear_texto` | ✅ Aplica defaults antes de ambigüedad |
| `audio.py` | `transcribir_audio` (Whisper local) | ✅ Funciona (requiere GPU para velocidad) |
| `imagen.py` | `extraer_texto_imagen` (Tesseract) | ✅ Funciona (texto impreso, no manuscrito) |
| `selector.py` | `seleccionar_preguntas` | ✅ Respeta MAX_PREGUNTAS_SESION=2 |
| `generator.py` | `generar_cotizacion`, `agregar_item_cotizacion`, `recalcular_total`, `_generar_sugerencias`, `_buscar_producto`, `_construir_opcion` | ✅ Con AV-first, margen, auto-sugerencias |
| `engine.py` | `buscar_precios(db, producto)` | ⚠️ Solo por Producto, retorna 1 resultado por tienda |
| `exporter.py` | `generate_pdf`, `generate_excel` | ✅ Funciona |
| `static_scraper.py` | `StaticScraper.scrape(query)` | ⚠️ Retorna 1 solo resultado (return en primer match) |
| `dynamic_scraper.py` | `DynamicScraper.scrape(query)` | ⚠️ Retorna 1 solo resultado (return en primer match) |
| `base.py` | `BaseScraper._build_search_url`, `_parse_price`, `_parse_availability` | ✅ URL de búsqueda ya funciona |

#### Endpoints existentes

| Endpoint | Método | Función | Estado |
|---|---|---|---|
| `/api/v1/upload` | POST | Subir archivo (texto/audio/imagen) → crear sesión | ✅ Funciona |
| `/api/v1/cotizacion/{session_id}` | POST | Crear cotización desde sesión | ✅ Funciona |
| `/api/v1/cotizacion/{session_id}` | GET | Obtener cotización | ✅ Funciona |
| `/api/v1/cotizaciones` | GET | Listar cotizaciones (paginado) | ✅ Funciona |
| `/api/v1/cotizacion/{id}/pdf` | GET | Descargar PDF | ✅ Funciona |
| `/api/v1/cotizacion/{id}/excel` | GET | Descargar Excel | ✅ Funciona |
| `/api/v1/cotizacion/item/{id}/seleccionar` | PUT | Seleccionar proveedor de un item | ✅ Funciona |
| `/api/v1/cotizacion/{id}/agregar` | POST | Agregar item al carrito | ✅ Funciona |
| `/api/v1/cotizacion/{id}/finalizar` | POST | Finalizar cotización (bloquea ediciones) | ✅ Funciona |
| `/api/v1/preguntas/{session_id}` | GET | Obtener preguntas pendientes | ✅ Funciona |
| `/api/v1/preguntas/{session_id}/responder` | POST | Responder preguntas | ✅ Funciona |
| `/api/v1/auth/login` | POST | Login (JWT) | ✅ Funciona |
| `/api/v1/usuarios` | GET/POST | CRUD usuarios (admin) | ✅ Funciona |
| `/api/v1/productos` | GET | Listar productos | ✅ Funciona |
| `/api/v1/health` | GET | Health check | ✅ Funciona |

#### Configuración actual

| Setting | Valor | Ubicación |
|---|---|---|
| `MARGEN_COMPETENCIA` | 5.0 | `config.py` (estático, no en BD) |
| `TIENDA_PROPIA` | "AV Electronics" | `config.py` (estático) |
| `MAX_PREGUNTAS_SESION` | 2 | `config.py` (estático) |
| `MAX_FILE_SIZE_MB` | 25 | `config.py` (estático) |

#### Tiendas sembradas

| Tienda | URL | JS | Selectores |
|---|---|---|---|
| AV Electronics | https://avelectronics.cc/ | No | WooCommerce (product_card, search_url, stock_in_classes) |
| Megatronica | https://megatronica.cc/ | Sí | WooCommerce (similar) |

**Tienda 3: ElectroStore** — Existe pero con limitaciones importantes (ver abajo).

#### Tiendas sembradas (3)

| Tienda | URL | Plataforma | JS | Productos electrónicos | Selectores |
|---|---|---|---|---|---|
| AV Electronics | https://avelectronics.cc/ | WooCommerce | No | ✅ Sí (componentes) | WooCommerce (product_card, search_url, stock_in_classes) |
| Megatronica | https://megatronica.cc/ | WooCommerce | Sí | ✅ Sí (componentes) | WooCommerce (similar) |
| ElectroStore | https://electrostoree.com/ | Shopify | No | ❌ No (solo 1 producto: Game Stick) | Shopify (diferentes selectores) |

#### ⚠️ Hallazgo crítico sobre ElectroStore

**ElectroStore NO vende componentes electrónicos.** Es una tienda de Uruguay que:
- Usa **Shopify** (no WooCommerce) — selectores diferentes
- Tiene **1 solo producto**: Game Stick M15 Plus ($2.390 UYU)
- Precios en **UYU** (pesos uruguayos), no USD
- No tiene Arduino, sensores, resistencias, ni nada del catálogo de AV Electronics

**URL de búsqueda de ElectroStore:** `https://electrostoree.com/search?q={query}`
**Selectores Shopify:** `div.product-card`, `.product-title a`, `.price`, etc.

**Recomendación:** Agregar ElectroStore al seed con selectores de Shopify, pero la búsqueda de componentes electrónicos casi siempre retornará 0 resultados. Sirve como respaldo para productos que AV y Megatronica no tengan, pero no es una tienda de electrónica.

**Decisión:** Agregar ElectroStore al seed con `activa=False`. El admin puede activarla desde el panel si en el futuro vende electrónica. Hay que crear selectores de Shopify (diferentes a WooCommerce).

**Seed de ElectroStore (Shopify):**
```python
{
    "nombre": "ElectroStore",
    "url_base": "https://electrostoree.com/",
    "selectores": {
        "search_url": "https://electrostoree.com/search?q={query}",
        "product_card": "div.product-card, .card--product",
        "product_url": "a.product-title, .card__title a",
        "price": ".price, .price__regular",
        "availability": ".product-form__inventory",
        "stock_in_classes": False,
        "product_page_price": ".price__regular .price-item",
        "product_page_availability": ".product-form__inventory, .stock-status",
    },
    "usa_javascript": False,
    "ttl_horas": 48,
    "activa": False,  # ← Desactivada por defecto
}
```

### Frontend (React + TypeScript + Vite)

#### Páginas existentes

| Ruta | Componente | Función | Estado |
|---|---|---|---|
| `/login` | `LoginPage` | Login con JWT | ✅ Funciona |
| `/carga` | `CargaPage` | Subir archivo + texto libre → crear sesión | ✅ Con info de auto-completado |
| `/preguntas` | `PreguntasPage` | Responder preguntas de ambigüedad | ✅ Funciona |
| `/cotizacion` | `CotizacionPage` | Ver cotización, seleccionar proveedores, carrito, finalizar | ✅ Funciona |
| `/historial` | `HistorialPage` | Listar cotizaciones pasadas | ✅ Funciona |
| `/usuarios` | `UsuariosPage` | CRUD usuarios (solo admin) | ✅ Funciona |

#### Componentes clave existentes

| Componente | Función | Estado |
|---|---|---|
| `CotizacionTable` | Tabla con items, selección de proveedor, agregar al carrito, finalizar | ✅ Completo |
| `Header` | Navegación, brand "CotIA" | ✅ Funciona |
| `Footer` | Footer con copyright | ✅ Funciona |

#### Dependencias npm actuales

```
react, react-dom, react-router-dom, axios, zustand, lucide-react, clsx, tailwind-merge
```

**No hay:** tesseract.js, mammoth, pdfjs-dist, xlsx (SheetJS)

---

## Lo que NO existe y necesitamos crear

### Backend — Nuevos archivos

| # | Archivo | Función | Prioridad |
|---|---|---|---|
| B1 | `app/models/configuracion.py` | Modelo `ConfiguracionNegocio` (clave/valor) | Alta |
| B2 | `app/services/configuracion.py` | `obtener_margen(db)`, `actualizar_margen(db, valor)` | Alta |
| B3 | `app/api/v1/endpoints/configuracion.py` | GET/PUT margen (solo admin para PUT) | Alta |
| B4 | `app/services/ingesta/filtro.py` | `extraer_componentes(mensaje)` con n-grams | Alta |
| B5 | `app/services/scraping/busqueda.py` | `buscar_por_termino(db, termino, margen)` — AV primero, luego otras | Alta |
| B6 | `app/api/v1/endpoints/busqueda.py` | POST `/buscar` — recibe texto, retorna opciones | Alta |
| B7 | `app/models/scraping_cache_termino.py` | Caché por término (no por producto_id) | Media |

### Backend — Archivos a modificar

| # | Archivo | Cambio | Prioridad |
|---|---|---|---|
| B8 | `scrapers/base.py` | `scrape()` retorna `list[dict]` en vez de `dict` | Alta |
| B9 | `scrapers/static_scraper.py` | Cambiar `return result` por `results.append()`, seguir iterando | Alta |
| B10 | `scrapers/dynamic_scraper.py` | Igual que static_scraper | Alta |
| B11 | `engine.py` | Agregar `buscar_por_termino()` que no dependa de `Producto` | Alta |
| B12 | `generator.py` | Leer margen desde BD (vía `configuracion.py`) en vez de `settings` | Media |
| B13 | `main.py` | Agregar seed de `configuracion_negocio` + router de configuración + router de búsqueda | Media |
| B14 | `router.py` | Incluir `configuracion.router` y `busqueda.router` | Media |
| B15 | `requirements.txt` | Agregar `pdfplumber`, `python-docx` (si procesamos archivos en backend) | Baja |

### Frontend — Nuevos archivos

| # | Archivo | Función | Prioridad |
|---|---|---|---|
| F1 | `modules/carga/components/TarjetaProducto.tsx` | Tarjeta con opciones seleccionables por componente | Alta |
| F2 | `modules/carga/components/CarritoPreview.tsx` | Carrito lateral con items seleccionados | Alta |
| F3 | `modules/carga/components/MicButton.tsx` | Botón de micrófono (Web Speech API) | Media |
| F4 | `modules/carga/components/ImageUpload.tsx` | Upload de imagen con Tesseract.js OCR | Media |
| F5 | `modules/carga/components/FileUpload.tsx` | Upload de PDF/Word/Excel con parseo en navegador | Media |
| F6 | `modules/admin/ConfiguracionPage.tsx` | Panel de admin para margen configurable | Alta |
| F7 | `modules/carga/services/busquedaService.ts` | Servicio POST `/buscar` al backend | Alta |
| F8 | `shared/types/speech.d.ts` | Tipos TypeScript para `SpeechRecognition` | Media |

### Frontend — Archivos a modificar

| # | Archivo | Cambio | Prioridad |
|---|---|---|---|
| F9 | `CargaPage.tsx` | Reescribir: input conversacional + tarjetas + carrito en vez de upload | Alta |
| F10 | `shared/types/index.ts` | Agregar `ResultadoBusqueda`, `OpcionProducto`, `ConfiguracionNegocio` | Alta |
| F11 | `AppRouter.tsx` | Agregar ruta `/admin/configuracion` (solo admin) | Alta |
| F12 | `Header.tsx` | Agregar link "Configuración" si es admin | Media |
| F13 | `package.json` | Agregar deps: `tesseract.js`, `mammoth`, `pdfjs-dist`, `xlsx` | Media |
| F14 | `vite.config.ts` | Configurar workers para Tesseract.js y pdf.js | Baja |

---

## Plan de ejecución por fases

### FASE 1: Backend — Configuración de margen en BD (2 días)

**Objetivo:** El margen se puede cambiar desde el admin y se guarda en BD.

**Tareas:**

1. **B1** — Crear `app/models/configuracion.py`:
   ```python
   class ConfiguracionNegocio(Base):
       __tablename__ = "configuracion_negocio"
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       clave: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
       valor: Mapped[str] = mapped_column(String(255), nullable=False)
       descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
       fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
   ```

2. **B2** — Crear `app/services/configuracion.py`:
   ```python
   async def obtener_margen(db: AsyncSession) -> float:
       """Lee el margen desde BD. Fallback a settings.MARGEN_COMPETENCIA si no existe."""
       result = await db.execute(
           select(ConfiguracionNegocio).where(ConfiguracionNegocio.clave == "margen_competencia")
       )
       config = result.scalar_one_or_none()
       if config:
           return float(config.valor)
       return settings.MARGEN_COMPETENCIA  # fallback

   async def actualizar_margen(db: AsyncSession, valor: float) -> None:
       """Actualiza o crea el margen en BD."""
       ...upsert...
   ```

3. **B3** — Crear `app/api/v1/endpoints/configuracion.py`:
   - `GET /api/v1/configuracion` → retorna `{ margen_competencia, tienda_propia }`
   - `PUT /api/v1/configuracion/margen` → body `{ "margen": 15.0 }` → solo admin

4. **B12** — Modificar `generator.py`:
   - Reemplazar `margen = Decimal(str(settings.MARGEN_COMPETIA)) / Decimal(100)` por `margen = Decimal(str(await obtener_margen(db))) / Decimal(100)`
   - Mismo cambio en `agregar_item_cotizacion`
   - Mismo cambio en `_construir_opcion` (pasar margen como parámetro)

5. **B13/B14** — Modificar `main.py` y `router.py`:
   - Agregar seed: `ConfiguracionNegocio(clave="margen_competencia", valor="5.0")`
   - Incluir `configuracion.router`

**Verificación:**
- `GET /api/v1/configuracion` retorna margen actual
- `PUT /api/v1/configuracion/margen` con `{"margen": 15.0}` actualiza BD
- Nueva cotización usa margen 15%
- Cotización anterior mantiene margen 5%

---

### FASE 2: Backend — Scrapers múltiples resultados (3 días)

**Objetivo:** Los scrapers retornan todos los productos encontrados, no solo el primero.

**Tareas:**

1. **B8** — Modificar `scrapers/base.py`:
   ```python
   @abstractmethod
   async def scrape(self, query: str) -> list[dict]:
       """Ejecuta el scraping y devuelve una LISTA de resultados.
       Returns:
           list[dict] con keys: precio, disponible, url, nombre_producto (opcional)
       """
       ...
   ```

2. **B9** — Modificar `static_scraper.py`:
   - Cambiar `result = {"precio": ...}` por `results: list[dict] = []`
   - Cambiar cada `return result` por `results.append({...})`
   - Agregar `nombre_producto` extrayendo el texto del título del producto
   - Al final del loop, `return results`
   - Limitar a máximo 10 resultados por tienda (evitar páginas enormes)

3. **B10** — Modificar `dynamic_scraper.py`:
   - Mismos cambios que static_scraper
   - Cerrar browser al final del loop, no en cada return

4. **B11** — Modificar `engine.py`:
   - Mantener `buscar_precios(db, producto)` para compatibilidad con flujo actual
   - Agregar `buscar_por_termino(db, termino: str) -> dict`:
     ```python
     async def buscar_por_termino(db: AsyncSession, termino: str) -> dict:
         """Busca un término en todas las tiendas activas. Retorna opciones por tienda."""
         tiendas = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
         resultados = {"termino": termino, "opciones": []}
         for tienda in tiendas.scalars():
             scraper = await get_scraper(...)
             items = await scraper.scrape(termino)  # ahora retorna list
             for item in items:
                 resultados["opciones"].append({
                     "tienda": tienda.nombre,
                     "nombre_producto": item.get("nombre_producto", termino),
                     "precio_base": item["precio"],
                     "disponible": item["disponible"],
                     "url": item["url"],
                 })
         return resultados
     ```

**Verificación:**
- `scrape("arduino")` en AV Electronics retorna 3+ resultados
- `buscar_por_termino(db, "arduino")` retorna opciones de todas las tiendas
- El flujo existente (`buscar_precios`) sigue funcionando

---

### FASE 3: Backend — Filtro de palabras clave (2 días)

**Objetivo:** Extraer componentes de un mensaje conversacional estilo WhatsApp.

**Tareas:**

1. **B4** — Crear `app/services/ingesta/filtro.py`:
   ```python
   def extraer_componentes(mensaje: str) -> list[str]:
       """
       Estrategia: n-grams contra TIPOS_PALABRAS (no stopwords simples).
       
       1. Normalizar texto (lowercase, sin tildes, sin puntuación)
       2. Generar trigramas, bigramas y unigramas del texto
       3. Comparar contra todas las entradas de TIPOS_PALABRAS
       4. Para cada match, extraer el contexto (cantidad, color, especificación)
       5. Retornar lista de términos de búsqueda
       """
   ```

   **Lógica clave (no usar stopwords a ciegas):**
   - Recorrer el texto con ventana deslizante de 3 → 2 → 1 palabras
   - Para cada ventana, comparar contra `TIPOS_PALABRAS` (que ya tiene "sensor", "motor dc", "paso a paso", "sensor de temperatura" como entradas)
   - Si hay match, marcar esa posición como consumida
   - Extraer cantidad si hay un número antes ("5 resistencias" → cantidad=5)
   - Extraer color si hay una palabra de `COLORES` cerca
   - Lo que no matchea ningún tipo → ignorar (es relleno)

   **Ejemplo:**
   ```
   Entrada: "Buenas tardes quisiera saber el precio de un arduino y un sensor de temperatura"
   
   Ventana 3: "buenas tardes quisiera" → no match
   Ventana 3: "tardes quisiera saber" → no match
   ...
   Ventana 2: "sensor de" → no match directo, pero...
   Ventana 3: "sensor de temperatura" → match con TIPOS_SENSOR["temperatura"] → componente: "sensor de temperatura"
   Ventana 1: "arduino" → match con TIPOS_PALABRAS["arduino"] → componente: "arduino"
   
   Salida: [
       {"termino": "arduino", "cantidad": 1},
       {"termino": "sensor de temperatura", "cantidad": 1}
   ]
   ```

2. **B6** — Crear `app/api/v1/endpoints/busqueda.py`:
   ```python
   @router.post("/buscar")
   async def buscar_componentes(
       body: BusquedaRequest,  # { "texto": "..." }
       db: AsyncSession = Depends(get_db),
       user: Usuario = Depends(get_current_user),
   ) -> BusquedaResponse:
       """Recibe texto libre, extrae componentes, busca en tiendas, retorna opciones."""
       componentes = extraer_componentes(body.texto)
       margen = await obtener_margen(db)
       resultados = []
       for comp in componentes:
           resultado = await buscar_por_termino_priorizado(db, comp["termino"], margen)
           resultados.append(resultado)
       return BusquedaResponse(resultados=resultados)
   ```

3. **B5** — Crear `app/services/scraping/busqueda.py`:
   ```python
   async def buscar_por_termino_priorizado(
       db: AsyncSession, termino: str, margen: float
   ) -> dict:
       """
       1. Buscar en AV Electronics primero
       2. Si encuentra → retornar opciones_propia (sin margen)
       3. Si no encuentra → buscar en otras tiendas
       4. Aplicar margen a resultados externos
       5. Retornar estructura completa
       """
   ```

4. **B7** — Crear `app/models/scraping_cache_termino.py`:
   ```python
   class ScrapingCacheTermino(Base):
       __tablename__ = "scraping_cache_termino"
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       termino: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
       tienda: Mapped[str] = mapped_column(String(100), nullable=False)
       resultados: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
       fecha_consulta: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       ttl_horas: Mapped[int] = mapped_column(Integer, default=24)
       # Unique constraint: (termino, tienda)
   ```

**Verificación:**
- POST `/api/v1/buscar` con `{"texto": "buenas quiero un arduino y un sensor de temperatura"}`
- Response incluye 2 componentes, cada uno con opciones de tiendas
- AV Electronics aparece primero, sin margen
- Megatronica aparece con margen aplicado
- Segunda búsqueda del mismo término usa caché

---

### FASE 4: Frontend — UI conversacional + tarjetas (3 días)

**Objetivo:** Reemplazar la página de carga por un chat conversacional con tarjetas de producto.

**Tareas:**

1. **F10** — Actualizar `shared/types/index.ts`:
   ```typescript
   interface OpcionProducto {
     tienda: string
     nombre_producto: string
     precio_base: number
     precio_con_margen: number
     margen_aplicado: number
     disponible: boolean
     url: string | null
     es_propio: boolean
   }
   
   interface ResultadoComponente {
     termino: string
     cantidad: number
     encontrado_propia: boolean
     opciones: OpcionProducto[]
   }
   
   interface BusquedaResponse {
     resultados: ResultadoComponente[]
   }
   
   interface ConfiguracionNegocio {
     margen_competencia: number
     tienda_propia: string
   }
   ```

2. **F7** — Crear `modules/carga/services/busquedaService.ts`:
   ```typescript
   export async function buscarComponentes(texto: string): Promise<BusquedaResponse> {
     const { data } = await api.post<BusquedaResponse>('/buscar', { texto })
     return data
   }
   
   export async function getConfiguracion(): Promise<ConfiguracionNegocio> {
     const { data } = await api.get<ConfiguracionNegocio>('/configuracion')
     return data
   }
   
   export async function actualizarMargen(margen: number): Promise<void> {
     await api.put('/configuracion/margen', { margen })
   }
   ```

3. **F1** — Crear `modules/carga/components/TarjetaProducto.tsx`:
   - Recibe `ResultadoComponente`
   - Muestra el término buscado como título
   - Lista las opciones con radio buttons
   - Badge "Tienda propia" o "+X% margen"
   - Botón "Agregar al carrito"
   - Si no hay opciones → "No encontrado en ninguna tienda"

4. **F2** — Crear `modules/carga/components/CarritoPreview.tsx`:
   - Lista items seleccionados
   - Muestra tienda, precio, cantidad
   - Botón "Quitar" por item
   - Total acumulado
   - Botón "Finalizar cotización" → navega a `/cotizacion`

5. **F9** — Reescribir `CargaPage.tsx`:
   - Input de texto libre (estilo chat) en la parte inferior
   - Botón "Buscar" (o Enter)
   - Resultados aparecen como tarjetas arriba
   - Carrito lateral derecho (o inferior en móvil)
   - Info: "Máximo 2 preguntas, auto-completado inteligente"
   - Mantiene el botón de upload de archivo como alternativa

**Verificación:**
- Escribir "buenas quiero un arduino" → aparece tarjeta con opciones
- Seleccionar una opción → se agrega al carrito
- Escribir otro mensaje → nueva tarjeta, carrito acumula
- Finalizar → navega a cotización con los items seleccionados

---

### FASE 5: Frontend — Panel de admin para margen (0.5 días)

**Objetivo:** El admin puede cambiar el margen desde la web.

**Tareas:**

1. **F6** — Crear `modules/admin/ConfiguracionPage.tsx`:
   - Input numérico para margen
   - Botón "Guardar"
   - Muestra valor actual
   - Solo accesible si `user.rol === 'admin'`

2. **F11** — Modificar `AppRouter.tsx`:
   ```typescript
   <Route path="/admin/configuracion" element={
     <AdminRoute><Suspense fallback={<PageFallback />}><ConfiguracionPage /></Suspense></AdminRoute>
   } />
   ```

3. **F12** — Modificar `Header.tsx`:
   - Si `user.rol === 'admin'`, mostrar link "Configuración"

**Verificación:**
- Admin entra a `/admin/configuracion`
- Cambia margen a 15%, guarda
- Busca un producto externo → ve precio con 15%
- User normal no ve el link de configuración

---

### FASE 6: Frontend — Entrada por voz (0.5 días)

**Objetivo:** Botón de micrófono que transcribe voz a texto.

**Tareas:**

1. **F8** — Crear `shared/types/speech.d.ts`:
   ```typescript
   interface SpeechRecognitionEvent extends Event {
     results: SpeechRecognitionResultList
   }
   interface SpeechRecognition extends EventTarget {
     lang: string
     continuous: boolean
     interimResults: boolean
     start(): void
     stop(): void
     onresult: ((event: SpeechRecognitionEvent) => void) | null
     onerror: ((event: Event) => void) | null
     onend: (() => void) | null
   }
   declare global {
     interface Window {
       SpeechRecognition: { new (): SpeechRecognition }
       webkitSpeechRecognition: { new (): SpeechRecognition }
     }
   }
   ```

2. **F3** — Crear `modules/carga/components/MicButton.tsx`:
   - Botón con icono de micrófono
   - Al clicar, inicia `webkitSpeechRecognition`
   - Muestra "Escuchando..." mientras graba
   - Al terminar, pone el texto en el input
   - Fallback: si no soporta Web Speech API, ocultar botón
   - `navigator.mediaDevices.getUserMedia` como alternativa

**Verificación:**
- En Chrome/Edge, clicar micrófono, hablar "busca un arduino"
- El texto aparece en el input
- Clicar "Buscar" → resultados aparecen

---

### FASE 7: Frontend — Entrada por imagen (1 día)

**Objetivo:** Subir foto, extraer texto con OCR en el navegador.

**Tareas:**

1. **F13** — Instalar `tesseract.js`:
   ```bash
   npm install tesseract.js
   ```

2. **F14** — Configurar `vite.config.ts`:
   ```typescript
   optimizeDeps: {
     exclude: ['tesseract.js']
   }
   ```

3. **F4** — Crear `modules/carga/components/ImageUpload.tsx`:
   - Input type="file" accept="image/*"
   - Al seleccionar imagen, mostrar preview
   - Ejecutar Tesseract.js con `lang: 'spa'`
   - Mostrar progreso "Procesando imagen... X%"
   - Al terminar, poner texto extraído en el input
   - Botón "Buscar" habilitado

**Verificación:**
- Subir foto de una lista impresa
- Tesseract extrae el texto
- El texto aparece en el input
- Clicar "Buscar" → resultados

---

### FASE 8: Frontend — Entrada por archivo (1.5 días)

**Objetivo:** Subir PDF/Word/Excel, extraer texto en el navegador.

**Tareas:**

1. **F13** — Instalar dependencias:
   ```bash
   npm install mammoth pdfjs-dist xlsx
   ```

2. **F5** — Crear `modules/carga/components/FileUpload.tsx`:
   - Input type="file" accept=".txt,.csv,.pdf,.docx,.xlsx"
   - Detectar formato por extensión
   - `.txt/.csv` → `FileReader.readAsText()`
   - `.pdf` → `pdfjs.getDocument()` → extraer texto de cada página
   - `.docx` → `mammoth.extractRawText()`
   - `.xlsx` → `XLSX.read()` → extraer celdas
   - Mostrar texto extraído en el input (editable)
   - Botón "Buscar"

**Verificación:**
- Subir PDF con lista de componentes → texto extraído en input
- Subir Word → texto extraído
- Subir Excel → celdas extraídas como líneas
- Editar texto extraído antes de buscar

---

### FASE 9: Integración y pruebas (2 días)

**Tareas:**

1. **Prueba end-to-end del flujo conversacional:**
   - Escribir mensaje → buscar → seleccionar → carrito → finalizar → cotización
   - Verificar que el margen se aplica correctamente
   - Verificar que AV Electronics aparece primero

2. **Prueba de voz:**
   - Hablar → texto → buscar → seleccionar

3. **Prueba de imagen:**
   - Subir foto → OCR → texto → buscar

4. **Prueba de archivo:**
   - Subir PDF/Word/Excel → extraer → buscar

5. **Prueba de admin:**
   - Cambiar margen → verificar en nuevas búsquedas
   - Verificar cotizaciones pasadas no cambian

6. **Pruebas de borde:**
   - Término no encontrado en ninguna tienda
   - Múltiples productos en un mensaje
   - Producto solo en AV Electronics (sin margen)
   - Producto solo en Megatronica (con margen)

---

## Resumen de esfuerzo

| Fase | Descripción | Días | Archivos nuevos | Archivos modificados |
|---|---|---|---|---|
| 1 | Margen configurable en BD | 2 | 3 | 3 |
| 2 | Scrapers múltiples resultados | 3 | 0 | 4 |
| 3 | Filtro de palabras clave + búsqueda por término | 2 | 4 | 2 |
| 4 | Frontend conversacional + tarjetas + carrito | 3 | 3 | 2 |
| 5 | Panel de admin margen | 0.5 | 1 | 2 |
| 6 | Voz (Web Speech API) | 0.5 | 2 | 1 |
| 7 | Imagen (Tesseract.js) | 1 | 1 | 2 |
| 8 | Archivo (pdf.js/mammoth/SheetJS) | 1.5 | 1 | 2 |
| 9 | Integración y pruebas | 2 | 0 | 0 |
| **Total** | | **15.5** | **15** | **18** |

---

## Orden de dependencias

```
FASE 1 (margen BD) ──────┐
                         ├──→ FASE 3 (filtro + búsqueda) ──→ FASE 4 (frontend conversacional)
FASE 2 (scrapers multi) ─┘                                        │
                                                                   ├──→ FASE 6 (voz)
                                                                   ├──→ FASE 7 (imagen)
                                                                   ├──→ FASE 8 (archivo)
                                                                   └──→ FASE 9 (pruebas)

FASE 5 (admin margen) ← depende de FASE 1
```

- **FASE 1 y 2 son paralelas** (no dependen entre sí)
- **FASE 3 depende de 1 y 2**
- **FASE 4 depende de 3**
- **FASE 5 depende de 1**
- **FASES 6, 7, 8 son paralelas** entre sí, dependen de 4
- **FASE 9 depende de todo**

---

## Decisiones tomadas (basadas en código verificado)

1. **Voz:** Web Speech API (frontend, gratuito) — el backend ya tiene Whisper para audio subido
2. **Imagen:** Tesseract.js (frontend, gratuito) — el backend ya tiene Tesseract para imágenes subidas
3. **Archivo:** Procesar en navegador (pdf.js/mammoth/SheetJS) — simplifica backend
4. **Margen:** Tabla `configuracion_negocio` en BD, leída en cada cotización
5. **Caché por término:** Nueva tabla `scraping_cache_termino` (no romper la existente)
6. **Scrapers:** Cambiar `scrape()` a retornar `list[dict]` (breaking change, actualizar engine.py)
7. **Filtro:** N-grams contra `TIPOS_PALABRAS` existente (no stopwords simples)
8. **Solo 2 tiendas:** AV Electronics y Megatronica (eliminar referencias a "Tienda 3")
9. **Flujo actual se mantiene:** El upload de archivo existente sigue funcionando como alternativa
10. **Frontend-first para multimodalidad:** Voz e imagen se procesan en navegador, backend recibe texto

---

## Lo que ya funciona y NO se toca

- ✅ Login con JWT (`auth.py`, `deps.py`)
- ✅ CRUD de usuarios (`usuarios.py`)
- ✅ Upload de archivo → sesión (`upload.py`)
- ✅ Preguntas con máx. 2 (`selector.py`, `config.py`)
- ✅ Defaults automáticos por tipo (`normalizer.py`)
- ✅ Auto-sugerencias (`generator.py` — driver para motor)
- ✅ Cotización con AV-first, margen, opciones (`generator.py`)
- ✅ Selección de proveedor (`cotizacion.py` endpoint)
- ✅ Carrito: agregar item (`cotizacion.py` endpoint)
- ✅ Finalizar cotización (`cotizacion.py` endpoint)
- ✅ Export PDF/Excel (`exporter.py`)
- ✅ Scraper base con URL de búsqueda (`base.py`)
- ✅ Selectores de AV Electronics y Megatronica (`main.py`)
- ✅ Whisper local para audio subido (`audio.py`)
- ✅ Tesseract para imagen subida (`imagen.py`)
- ✅ Frontend: login, preguntas, historial, usuarios
- ✅ Frontend: CotizacionTable con selección de proveedor y carrito
