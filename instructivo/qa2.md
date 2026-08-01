# QA2 — Revisión del flujo conversacional post-Fases 1-9

## Lista de issues detectados

### Issue 1: Lentitud en resultados de búsqueda
**Síntoma:** Los resultados tardan mucho en aparecer después de enviar texto.
**Pregunta:** ¿Cada cuánto se hace web scraping o solo se hace una vez?
**Diagnóstico:**
- `buscar_por_termino()` en `engine.py` hace scraping en vivo contra todas las tiendas activas en cada búsqueda.
- No hay cache para búsquedas por término (el cache existente `ScrapingCache` es por `producto_id`, no por término libre).
- Cada tienda se scrapea secuencialmente (no en paralelo), multiplicando el tiempo.
- Si una tienda no responde o tarda, bloquea todas las demás.

**Buenas prácticas:**
- Cache por término con TTL (igual que tiendas pero key = término, no producto_id).
- Scraping paralelo con `asyncio.gather` para consultar todas las tiendas simultáneamente.
- Timeout por tienda (si una no responde en 10s, continuar con las demás).
- Mostrar resultados parciales (streaming) — las tiendas que responden rápido aparecen primero.

---

### Issue 2: Selección limitada a un resultado por componente
**Síntoma:** Solo se puede escoger una opción por componente. Si hay varios resultados útiles, hay que elegir uno solo.
**Síntoma adicional:** Los productos "agotados" se muestran pero no se ofrece alternativa de otras tiendas.

**Diagnóstico:**
- `TarjetaProducto` permite seleccionar una sola opción por término.
- El botón "Agregar al carrito" agrega una única opción.
- Los productos agotados (`disponible: false`) aparecen deshabilitados sin sugerir alternativas.

**Buenas prácticas:**
- Permitir seleccionar múltiples opciones del mismo componente (ej: 2 LEDs de AV + 3 de Megatronica).
- Para productos agotados: mostrar badge "Agotado en {tienda}" + destacar que está disponible en {otra tienda}.
- Si un producto está agotado en todas las tiendas, mostrar mensaje "No disponible — consultar disponibilidad".

---

### Issue 3: Preguntas innecesarias cuando ya hay resultados
**Síntoma:** El flujo de preguntas aparece aunque la búsqueda ya encontró resultados y el carrito está listo.
**Diagnóstico:**
- El flujo actual pasa por `/preguntas` después de upload, sin importar si la búsqueda ya resolvió todo.
- Las preguntas deberían ser excepcionales, no el flujo principal.

**Buenas prácticas:**
- **Eliminar el flujo de preguntas obligatorio** cuando la búsqueda conversacional ya encontró resultados.
- Las preguntas solo aparecen cuando un término **no se encuentra** en ninguna tienda:
  1. Comparar el término no encontrado contra un diccionario de electrónica (sinónimos, nombres alternativos).
  2. Si hay coincidencia: sugerir "¿Buscabas {término alternativo}?" y buscar automáticamente.
  3. Si no hay coincidencia: una sola pregunta "¿Para qué sirve este componente o tiene otro nombre?".
- Máximo 1 pregunta por término no encontrado (no 2 como ahora).

---

### Issue 4: Carrito no permite agregar más cosas después
**Síntoma:** Una vez que hay items en el carrito, no se puede seguir buscando y agregando más.
**Diagnóstico:**
- `CargaPage` mantiene estado del carrito en `useState`, pero no hay un flujo claro de "buscar más → agregar al carrito".
- El carrito actual funciona pero la UX no invita a seguir buscando.

**Buenas prácticas:**
- El carrito debe ser persistente durante toda la sesión de búsqueda.
- Después de agregar al carrito, limpiar la selección pero mantener el campo de búsqueda vacío para una nueva búsqueda.
- Botón "Buscar más" o simplemente dejar el textarea listo para una nueva búsqueda.
- El carrito lateral siempre visible mostrando el total acumulado.

---

### Issue 5: No se puede pedir más de 1 unidad del mismo producto
**Síntoma:** La cantidad viene del texto original (ej: "5 resistencias") pero no se puede ajustar en el carrito.
**Diagnóstico:**
- `ItemCarrito` tiene `cantidad` fija desde la extracción del texto.
- No hay UI para cambiar la cantidad en el carrito.

**Buenas prácticas:**
- Input de cantidad editable en cada item del carrito (+ / - botones o input numérico).
- Recalcular subtotal y total automáticamente al cambiar cantidad.
- Validar cantidad mínima 1.

---

### Issue 6: Transición carrito → cotización
**Síntoma:** El botón "Generar cotización" del carrito genera un archivo de texto y lo sube al endpoint de upload, que pasa por el flujo de preguntas.
**Diagnóstico:**
- `handleFinalizar` crea un `File` con texto y llama a `uploadFile`, que va al endpoint `/upload` → sesión → preguntas.
- Este flujo es innecesario si ya tenemos los items seleccionados con precios.

**Buenas prácticas:**
- Crear un endpoint directo `POST /cotizacion/desde-carrito` que reciba los items seleccionados (término, tienda, cantidad, precio) y cree la cotización directamente.
- Sin pasar por upload/preguntas.
- El carrito → cotización directamente con los datos ya resueltos.

---

## Resumen de cambios a aplicar

| # | Cambio | Archivos | Esfuerzo |
|---|--------|----------|----------|
| 1a | Cache por término en `engine.py` | `engine.py` | Medio |
| 1b | Scraping paralelo con `asyncio.gather` | `engine.py` | Bajo |
| 1c | Timeout por tienda | `engine.py`, `base.py` | Bajo |
| 2a | Multi-selección por componente | `TarjetaProducto.tsx`, `CargaPage.tsx` | Medio |
| 2b | Sugerir alternativas para agotados | `TarjetaProducto.tsx` | Bajo |
| 3 | Preguntas solo si no se encuentra | `CargaPage.tsx`, `busqueda.py` | Medio |
| 4 | Carrito persistente + buscar más | `CargaPage.tsx` | Bajo |
| 5 | Editar cantidad en carrito | `CarritoPreview.tsx` | Bajo |
| 6 | Endpoint directo carrito → cotización | `cotizacion.py` (endpoint), `CargaPage.tsx` | Medio |
