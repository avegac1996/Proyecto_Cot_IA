# Resumen de Cambios Realizados — CotIA

---

## 1. Datos del Cliente en Cotizaciones

### Backend
- **Modelo `Cotizacion`**: agregados campos `cliente_correo` y `cliente_celular` (ya existía `cliente_nombre`)
- **Schema `CotizacionResponse`**: incluye `cliente_nombre`, `cliente_correo`, `cliente_celular`
- **Schema `CotizacionListItem`**: incluye `cliente_nombre` y `usuario_nombre`
- **Endpoint `crear_desde_carrito`**: acepta datos del cliente al crear; los preserva al editar (no sobrescribe)
- **PDF (`exporter.py`)**: caja de datos del cliente entre la barra de color y la tabla de items

### Frontend
- **`ClienteModal.tsx`**: modal con campos nombre, correo, celular
- **`CargaPage.tsx`**: al clic en "Generar cotización" abre el modal; si edita cotización existente, lo omite
- **`HistorialPage.tsx`**: columna Cliente en tabla; datos del cliente en modal de detalle

---

## 2. Columna Usuario en Historial

### Backend
- **Endpoint `listar_cotizaciones`**: JOIN con tabla `usuarios` para obtener `username`
- **Schema `CotizacionListItem`**: agregado `usuario_nombre: str | None`

### Frontend
- **Tipo `CotizacionListItem`**: agregado `usuario_nombre`
- **`HistorialPage.tsx`**: columna "Usuario" entre Cliente y Fecha en la tabla

---

## 3. IVA Configurable

### Backend
- **`configuracion.py` (service)**: nuevas funciones `obtener_iva(db)` y `actualizar_iva(db, valor)`
  - Fallback a 15% si no existe registro
  - Almacena en tabla `configuracion_negocio` con clave `"iva"`
- **Endpoint `configuracion.py`**:
  - `GET /configuracion` retorna `iva` además de margen y tienda
  - `PUT /configuracion/iva` — admin puede actualizar IVA (0-100)
  - `PUT /configuracion/margen` — ahora también retorna `iva`
- **PDF (`exporter.py`)**: `generate_pdf` recibe `iva_pct` y muestra 3 filas:
  - **Subtotal:** (suma de items, sin IVA)
  - **IVA (X%):** (subtotal × porcentaje)
  - **TOTAL:** (subtotal + IVA)
- **Endpoint PDF**: lee IVA de BD y lo pasa al exporter

### Frontend
- **Tipo `ConfiguracionNegocio`**: agregado `iva: number`
- **`busquedaService.ts`**: nueva función `actualizarIva(iva)`
- **`ConfiguracionPage.tsx`**: campo IVA (%) con label y descripción; guarda margen e IVA juntos

---

## 4. Asistente IA (Gemini Chat)

### Backend
- **`gemini/chat.py`**: servicio conversacional con Gemini
  - System prompt restrictivo: solo responde sobre componentes buscados
  - Si no hay resultados, ayuda a reformular búsqueda o sugerir términos
  - Construye contexto con resultados (incluye términos sin resultados)
  - Mantiene historial (últimos 6 mensajes)
- **Endpoint `POST /buscar/preguntar`**: recibe pregunta, resultados, historial

### Frontend
- **`AgenteChat.tsx`**: componente de chat con:
  - Header con icono Sparkles
  - Lista de mensajes (burbujas usuario/asistente)
  - Indicador de carga
  - Input con Enter para enviar
  - Subtitle dinámico: muestra término buscado si no hay resultados
- **`CargaPage.tsx`**:
  - Botón IA (icono Sparkles) al lado derecho de "Buscar componentes" en los 4 tabs
  - Clic despliega/oculta el AgenteChat
  - Funciona con y sin resultados de búsqueda
  - Mensaje "No se encontraron resultados" cuando aplica
- **`busquedaService.ts`**: función `preguntarAgente(pregunta, resultados, historial)`

---

## 5. Menú Responsive

### Frontend
- **`Header.tsx`**: rediseñado completamente
  - Desktop: sidebar fijo a la izquierda (igual que antes)
  - Mobile: top bar fijo con botón hamburger → drawer overlay
  - Toggle con estado `isOpen`
- **`AppShell.tsx`**: layout con `flex-col` en mobile y `flex-row` en desktop; padding-top en mobile

---

## 6. Optimizaciones de Scraping

### Backend
- **`busqueda.py` (endpoint)**: componentes buscados en paralelo con `asyncio.gather`
- **`engine.py`**: tiendas scrapeadas en paralelo con `asyncio.gather` (no secuencial)
- **`static_scraper.py`**: timeout HTTP reducido a 8s, máx 3 páginas
- **`dynamic_scraper.py`**: timeout 10s, `domcontentloaded` en lugar de `networkidle`, máx 3 páginas
- **`wayback_scraper.py`**: timeout reducido a 15s
- **Nueva tienda**: Electroshop agregada a la BD

---

## 7. Reconocimiento de Imagen (Gemini Vision)

### Backend
- **`gemini/vision.py`**: envía imagen base64 a Gemini Vision
  - Prompt especializado en componentes electrónicos
  - Extrae texto y lista de componentes identificados
- **Endpoint `POST /buscar/imagen`**: recibe imagen, retorna texto + componentes

### Frontend
- **`ImageInput.tsx`**: upload de imagen, preview, envío al backend

---

## 8. Exportación PDF/Excel Mejorada

### PDF
- Logo de AV Electronics en header (1.4 inch)
- Barra de color primario
- Caja de datos del cliente (nombre, correo, celular)
- Tabla de items: Producto, Cant., P. Unit., Subtotal
- Columna "Proveedor" y "Estado" removidas (más limpio)
- Sección de resumen: **Subtotal**, **IVA (X%)**, **TOTAL**
- Footer con datos de contacto de AV Electronics

### Excel
- Exportación con openpyxl
- Mismo formato de datos

---

## 9. Entradas Multi-Modal

### Frontend (`CargaPage.tsx`)
- **Tab Texto**: textarea para escribir lista de componentes
- **Tab Voz**: Web Speech API para transcripción
- **Tab Imagen**: upload de imagen → Gemini Vision
- **Tab Archivo**: upload PDF/DOCX/XLSX/TXT con extracción de texto en navegador
  - pdfjs-dist para PDF
  - mammoth para DOCX
  - xlsx para Excel

---

## Archivos Modificados/Creados

### Backend
| Archivo | Cambio |
|---------|--------|
| `models/cotizacion.py` | +cliente_correo, +cliente_celular |
| `schemas/cotizacion.py` | +cliente fields, +usuario_nombre |
| `api/v1/endpoints/cotizacion.py` | JOIN usuario, acepta cliente, IVA en PDF |
| `api/v1/endpoints/configuracion.py` | +IVA endpoint |
| `api/v1/endpoints/busqueda.py` | Paralelización, +endpoint preguntar |
| `services/configuracion.py` | +obtener_iva, +actualizar_iva |
| `services/cotizacion/exporter.py` | Cliente box, subtotal/IVA/total, logo ajustes |
| `services/gemini/chat.py` | **NUEVO** — Asistente conversacional |
| `services/gemini/vision.py` | Sin cambios (existente) |
| `services/scraping/engine.py` | Paralelización, timeouts |
| `services/scraping/scrapers/*.py` | Timeouts reducidos |
| `services/scraping/busqueda.py` | Sin cambios (existente) |

### Frontend
| Archivo | Cambio |
|---------|--------|
| `shared/types/index.ts` | +cliente fields, +usuario_nombre, +iva |
| `modules/carga/CargaPage.tsx` | Modal cliente, AgenteChat, botón IA, tabs |
| `modules/carga/components/ClienteModal.tsx` | **NUEVO** |
| `modules/carga/components/AgenteChat.tsx` | **NUEVO** |
| `modules/carga/services/busquedaService.ts` | +preguntarAgente, +actualizarIva, +cliente params |
| `modules/historial/HistorialPage.tsx` | +columna Usuario, +cliente en detalle |
| `modules/admin/ConfiguracionPage.tsx` | +campo IVA |
| `modules/header/Header.tsx` | Responsive con drawer |
| `modules/app/AppShell.tsx` | Layout responsive |

### Documentación
| Archivo | Descripción |
|---------|-------------|
| `ARQUITECTURA.md` | Arquitectura completa del sistema |
| `RESUMEN_CAMBIOS.md` | Este archivo |
