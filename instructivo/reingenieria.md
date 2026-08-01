# Reingeniería del Flujo de Cotización — AV Electronics

## Documento de diseño funcional y técnico

---

## 1. Visión general

El sistema actual sigue un flujo rígido: **carga de archivo → parseo → preguntas → cotización**.
La reingeniería propone un flujo conversacional flexible inspirado en cómo el cliente realmente compra por WhatsApp.

### Flujo actual vs. propuesto

| Aspecto | Actual | Propuesto |
|---|---|---|
| Entrada | Archivo de texto/audio/imagen | Mensaje de texto libre (estilo WhatsApp) |
| Detección | Parseo línea por línea | Extracción de palabras clave + filtrado de relleno |
| Búsqueda | Busca en todas las tiendas a la vez | **Primero AV Electronics**, luego las otras 2 |
| Margen | Fijo 5% para tiendas externas | **Configurable desde admin**, guardado en BD |
| Selección | Automática (más barato) | **El cliente escoge** qué producto cotizar |
| Interacción | Formulario web | **Conversacional** — muestra opciones y espera selección |

---

## 2. Flujo detallado paso a paso

### Paso 1: Recepción del mensaje

**Entrada del cliente (ejemplo real):**
```
"Buenas tardes quisiera saber el precio de un arduino y un sensor de temperatura"
```

**Proceso:**
1. Limpiar el mensaje (quitar saludos, puntuación, stopwords)
2. Extraer palabras clave relevantes
3. Identificar componentes mencionados

**Filtrado de relleno:**

| Palabra | Clasificación |
|---|---|
| "Buenas" | Saludo — descartar |
| "tardes" | Saludo — descartar |
| "quisiera" | Verbo de cortesía — descartar |
| "saber" | Verbo — descartar |
| "el" | Artículo — descartar |
| "precio" | Contexto (indica intención de cotizar) — descartar |
| "de" | Preposición — descartar |
| "un" | Artículo — descartar |
| **"arduino"** | **Palabra clave — componente 1** |
| "y" | Conjunción — descartar |
| **"sensor"** | **Palabra clave — componente 2** |
| **"de"** | Preposición — mantener (une "sensor" + "temperatura") |
| **"temperatura"** | **Palabra clave — especifica tipo de sensor** |

**Resultado del filtrado:**
```
Componente 1: "arduino"
Componente 2: "sensor de temperatura"
```

### Paso 2: Búsqueda en AV Electronics (tienda propia)

Por cada componente detectado, buscar **primero en AV Electronics**:

```
Componente: "arduino"
  → Buscar en https://avelectronics.cc/?s=arduino
  → Resultados:
    - Arduino UNO R3 — $25.00 — Disponible ✅
    - Arduino Nano — $18.00 — Disponible ✅
    - Arduino Mega 2560 — $35.00 — Agotado ❌
```

**Regla:** Si AV Electronics tiene el producto → mostrar opciones, sin margen extra (precio directo).

### Paso 3: Búsqueda en otras tiendas (solo si AV no tiene)

Si AV Electronics **no tiene** el producto o está agotado, buscar en las otras 2 tiendas:

```
Componente: "sensor de temperatura"
  → AV Electronics: No encontrado ❌
  → Buscar en Megatronica: https://megatronica.cc/?s=sensor+temperatura
    - Sensor DHT22 — $12.00 — Disponible ✅
  → Buscar en ElectroStore: https://electrostoree.com/search?q=sensor+temperatura
    - (ElectroStore no vende componentes electrónicos — probablemente 0 resultados)
```

**Regla:** A estos resultados se les agrega el **% extra configurable** desde el panel de admin.

> **Nota sobre ElectroStore:** Es una tienda Shopify de Uruguay con 1 solo producto (Game Stick M15). No vende componentes electrónicos. Se agrega al sistema por si en el futuro expande su catálogo, pero la búsqueda de componentes casi siempre retornará 0 resultados. Sus precios están en UYU (pesos uruguayos).

### Paso 4: Presentación de opciones al cliente

Por cada componente, mostrar una tarjeta con las opciones encontradas:

```
📦 ARDUINO — Encontrado en AV Electronics (precio directo)

  [✓] Arduino UNO R3     $25.00    Disponible
  [ ] Arduino Nano        $18.00    Disponible
  [ ] Arduino Mega 2560   $35.00    Agotado

  → Selecciona cuál llevar a cotización

---

📦 SENSOR DE TEMPERATURA — No encontrado en AV Electronics
   Buscado en tiendas externas (precio + 15% margen)

  [✓] Sensor LM35 (Megatronica)     $9.78    Disponible
      Precio base: $8.50 + $1.28 (15%)
  [ ] Sensor DHT22 (Megatronica)    $13.80   Disponible
      Precio base: $12.00 + $1.80 (15%)

  → Selecciona cuál llevar a cotización
  → El margen es editable por el admin
```

### Paso 5: Selección del cliente

El cliente marca qué productos quiere cotizar:

- Si hay 1 sola opción disponible → se auto-selecciona
- Si hay múltiples → el cliente escoge
- Si no hay opciones → se marca como "no disponible"

### Paso 6: Carrito y cotización final

Los productos seleccionados se agregan al carrito. El cliente puede:
- Agregar más productos (escribir otro mensaje)
- Quitar productos del carrito
- Finalizar la cotización

---

## 3. Configuración del % extra (margen)

### Panel de admin

El admin debe poder:
1. **Ver** el % de margen actual
2. **Modificar** el % de margen
3. **Guardar** el cambio en la base de datos

**Ubicación:** Nueva sección en el panel de admin → "Configuración de Negocio"

**Campos:**

| Campo | Tipo | Descripción |
|---|---|---|
| `margen_competencia` | Decimal (0-100) | % extra aplicado a productos de tiendas externas |
| `tienda_propia` | String | Nombre de la tienda propia (AV Electronics) |

**Comportamiento:**
- El cambio aplica **inmediatamente** a nuevas cotizaciones
- Las cotizaciones ya generadas mantienen el margen con el que se crearon
- Solo el rol `admin` puede modificar este valor

### Estructura en BD

```sql
-- Tabla: configuracion_negocio
CREATE TABLE configuracion_negocio (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(50) UNIQUE NOT NULL,
    valor VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_actualizacion TIMESTAMP DEFAULT NOW()
);

-- Valores iniciales:
INSERT INTO configuracion_negocio (clave, valor, descripcion) VALUES
('margen_competencia', '5.0', 'Margen % aplicado a productos de tiendas externas'),
('tienda_propia', 'AV Electronics', 'Nombre de la tienda propia (sin margen)');
```

---

## 4. Arquitectura técnica propuesta

### 4.1 Backend — Nuevos componentes

#### A. Filtro de palabras clave

**Archivo:** `app/services/ingesta/filtro.py`

```python
# Pseudocódigo del diseño

STOPWORDS = {
    # Saludos
    "buenas", "buenos", "tardes", "dias", "noches", "hola", "saludos",
    # Verbos de cortesía
    "quisiera", "quiero", "necesito", "me", "gustaria", "podria",
    # Artículos y preposiciones
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "y", "o", "en", "con", "para",
    # Verbos genéricos
    "saber", "conocer", "ver", "tener", "hacer",
    # Contexto de cotización
    "precio", "cotizar", "cotizacion", "costo", "valor", "cuanto",
}

def extraer_componentes(mensaje: str) -> list[str]:
    """
    1. Normalizar texto (lowercase, sin tildes)
    2. Tokenizar por espacios
    3. Filtrar stopwords
    4. Agrupar tokens adyacentes que formen un componente
    5. Validar contra diccionario de tipos conocidos
    6. Retornar lista de componentes detectados
    """
    pass
```

**Ejemplo de funcionamiento:**
```
Entrada: "Buenas tardes quisiera saber el precio de un arduino y un sensor de temperatura"
Salida: ["arduino", "sensor de temperatura"]
```

#### B. Búsqueda priorizada

**Archivo:** `app/services/scraping/busqueda.py`

```python
# Pseudocódigo del diseño

async def buscar_producto_priorizado(
    db: AsyncSession,
    termino: str,
    margen: float
) -> dict:
    """
    1. Buscar en AV Electronics primero
    2. Si encuentra resultados → retornar con precio directo
    3. Si no encuentra → buscar en otras tiendas
    4. Aplicar margen % a resultados externos
    5. Retornar estructura con todas las opciones
    """
    pass

# Estructura de retorno:
{
    "termino": "arduino",
    "encontrado_propia": True,
    "opciones_propia": [
        {
            "tienda": "AV Electronics",
            "producto": "Arduino UNO R3",
            "precio_base": 25.00,
            "margen": 0,          # Sin margen
            "precio_final": 25.00,
            "disponible": True,
            "url": "https://avelectronics.cc/producto/arduino-uno-r3"
        },
        ...
    ],
    "opciones_externas": [],  # Vacío porque AV Electronics sí tiene
}
```

#### C. Endpoint de configuración de margen

**Archivo:** `app/api/v1/endpoints/configuracion.py`

```python
# Endpoints propuestos:

# GET /api/v1/configuracion
# → Retorna la configuración actual (margen, tienda_propia)
# → Accesible para cualquier usuario autenticado

# PUT /api/v1/configuracion/margen
# → Body: { "margen": 15.0 }
# → Solo admin
# → Actualiza el margen en BD
# → Retorna la configuración actualizada
```

### 4.2 Frontend — Nuevos componentes

#### A. Vista de resultados de búsqueda

Reemplaza la tabla actual por **tarjetas de producto** con opciones seleccionables:

```
┌─────────────────────────────────────────────────┐
│ 📦 Arduino                                        │
│ Encontrado en AV Electronics · Precio directo    │
│                                                   │
│ ○ Arduino UNO R3      $25.00    ✅ Disponible    │
│ ○ Arduino Nano         $18.00    ✅ Disponible    │
│ ○ Arduino Mega 2560    $35.00    ❌ Agotado      │
│                                                   │
│ [Seleccionar y agregar al carrito]               │
└─────────────────────────────────────────────────┘
```

#### B. Vista de resultados externos

```
┌─────────────────────────────────────────────────┐
│ 📦 Sensor de temperatura                         │
│ No encontrado en AV Electronics                  │
│ Buscado en tiendas externas · +15% margen        │
│                                                   │
│ ○ Sensor LM35 (Megatronica)                       │
│   Precio base: $8.50                              │
│   Margen +15%: +$1.28                             │
│   Total: $9.78         ✅ Disponible              │
│                                                   │
│ ○ Sensor DHT22 (Megatronica)                      │
│   Precio base: $12.00                             │
│   Margen +15%: +$1.80                             │
│   Total: $13.80        ✅ Disponible              │
│                                                   │
│ [Seleccionar y agregar al carrito]               │
└─────────────────────────────────────────────────┘
```

#### C. Panel de admin — Configuración de margen

```
┌─────────────────────────────────────────────────┐
│ ⚙️ Configuración de Negocio                       │
│                                                   │
│ Margen para tiendas externas:                    │
│ ┌─────────┐                                        │
│ │  15.0   │  %                                    │
│ └─────────┘                                        │
│                                                   │
│ Este porcentaje se aplica a productos que no      │
│ están disponibles en AV Electronics y se buscan  │
│ en tiendas externas.                              │
│                                                   │
│ [Guardar]                                         │
└─────────────────────────────────────────────────┘
```

#### D. Carrito de cotización

```
┌─────────────────────────────────────────────────┐
│ 🛒 Carrito de Cotización                         │
│                                                   │
│ 1. Arduino UNO R3                                  │
│    AV Electronics · $25.00 · 1 unidad             │
│    [Quitar]                                       │
│                                                   │
│ 2. Sensor LM35                                     │
│    Megatronica · $9.78 (+15%) · 1 unidad          │
│    [Quitar]                                       │
│                                                   │
│ Total: $34.78                                     │
│                                                   │
│ [+ Agregar más productos]                         │
│ [Finalizar cotización]                           │
└─────────────────────────────────────────────────┘
```

---

## 5. Flujo completo del sistema

```
Cliente escribe mensaje
        │
        ▼
┌───────────────────┐
│ Filtro de palabras │
│ clave              │
└───────┬───────────┘
        │
        ▼
   ["arduino", "sensor de temperatura"]
        │
        ▼
┌───────────────────┐
│ Por cada término:  │
│ Buscar en AV       │
│ Electronics primero │
└───────┬───────────┘
        │
        ├──→ AV Electronics TIENE el producto
        │         │
        │         ▼
        │    Mostrar opciones (precio directo)
        │    Cliente selecciona
        │         │
        │         ▼
        │    Agregar al carrito
        │
        └──→ AV Electronics NO tiene el producto
                  │
                  ▼
             Buscar en otras 2 tiendas
             Aplicar margen % (configurable)
                  │
                  ▼
             Mostrar opciones (precio + margen)
             Cliente selecciona
                  │
                  ▼
             Agregar al carrito
                  │
                  ▼
┌───────────────────┐
│ Carrito de         │
│ cotización         │
└───────┬───────────┘
        │
        ├──→ [+ Agregar más] → Volver a recibir mensaje
        │
        └──→ [Finalizar] → Generar cotización (PDF/Excel)
```

---

## 6. Cambios necesarios en el código existente

### Backend

| Archivo | Cambio |
|---|---|
| `app/services/ingesta/filtro.py` | **NUEVO** — Extracción de palabras clave desde texto libre |
| `app/services/scraping/busqueda.py` | **NUEVO** — Búsqueda priorizada (AV primero, luego otras) |
| `app/api/v1/endpoints/configuracion.py` | **NUEVO** — Endpoints GET/PUT para margen configurable |
| `app/models/configuracion.py` | **NUEVO** — Modelo `ConfiguracionNegocio` |
| `app/services/scraping/engine.py` | Modificar `buscar_precios` para soportar búsqueda por término (no solo por producto) |
| `app/services/cotizacion/generator.py` | Adaptar para recibir selecciones del cliente en vez de procesar toda la sesión |
| `app/core/config.py` | `MARGEN_COMPETENCIA` pasa a ser leído de BD en vez de settings estático |
| `app/main.py` | Agregar seed de `configuracion_negocio` y router de configuración |

### Frontend

| Archivo | Cambio |
|---|---|
| `FRONTEND/src/modules/carga/CargaPage.tsx` | Reemplazar por vista de mensaje libre + resultados |
| `FRONTEND/src/modules/carga/components/TarjetaProducto.tsx` | **NUEVO** — Tarjeta con opciones seleccionables |
| `FRONTEND/src/modules/carga/components/Carrito.tsx` | **NUEVO** — Carrito lateral con items seleccionados |
| `FRONTEND/src/modules/admin/ConfiguracionPage.tsx` | **NUEVO** — Panel de admin para margen |
| `FRONTEND/src/modules/admin/AdminRouter.tsx` | **NUEVO** — Router para secciones de admin |
| `FRONTEND/src/shared/types/index.ts` | Nuevos tipos: `OpcionProducto`, `ResultadoBusqueda`, `ConfiguracionNegocio` |
| `FRONTEND/src/modules/carga/services/busquedaService.ts` | **NUEVO** — Servicio para buscar productos por término |

---

## 7. Consideraciones de diseño

### 7.1 Búsqueda por término vs. por producto

El sistema actual busca por **producto** (registro en BD con ID). El nuevo sistema debe buscar por **término de texto libre** directamente en las tiendas vía web scraping.

**Cambio clave:** `buscar_precios(db, producto: Producto)` → `buscar_por_termino(db, termino: str)`

El scraping debe:
1. Construir la URL de búsqueda de la tienda: `https://avelectronics.cc/?s=arduino`
2. Scrapear los resultados de búsqueda (no solo una página de producto)
3. Extraer: nombre, precio, disponibilidad, URL por cada resultado
4. Retornar múltiples opciones por término

### 7.2 Caché de búsquedas

Cada búsqueda por término debe cachearse con un TTL:
- Mismo término + misma tienda → usar caché
- TTL configurable (default 24h)
- Si el admin cambia el margen → no invalida el caché (el margen se aplica al mostrar, no al cachear)

### 7.3 Margen aplicado al mostrar, no al buscar

El precio base se obtiene del scraping y se guarda sin margen.
El margen se aplica **al presentar al cliente**, no al buscar.

```
precio_base (scraping) → caché → mostrar con margen → cliente ve precio_final
```

Esto permite cambiar el margen sin re-scrapear.

### 7.4 Persistencia del margen en la cotización

Cuando el cliente finaliza la cotización, el margen aplicado **se congela** en el `CotizacionItem`:
- `precio_unitario` = precio con margen al momento de cotizar
- `margen_aplicado` = % que se aplicó
- Si el admin cambia el margen después, no afecta cotizaciones pasadas

---

## 8. Casos de prueba del flujo

### Caso 1: Producto encontrado en AV Electronics
```
Mensaje: "quisiera el precio de un arduino"
→ Detecta: "arduino"
→ Busca en AV Electronics → encuentra 3 opciones
→ Cliente selecciona "Arduino UNO R3"
→ Se agrega al carrito a $25.00 (sin margen)
```

### Caso 2: Producto no encontrado en AV Electronics
```
Mensaje: "necesito un sensor de temperatura"
→ Detecta: "sensor de temperatura"
→ Busca en AV Electronics → no encuentra
→ Busca en Megatronica → encuentra DHT22 $12.00
→ Busca en ElectroStore → no encuentra (no vende electrónica)
→ Aplica margen 15%: DHT22 $13.80
→ Cliente selecciona "Sensor DHT22"
→ Se agrega al carrito a $13.80
```

### Caso 3: Múltiples productos en un mensaje
```
Mensaje: "buenas quiero cotizar un arduino y un sensor de temperatura"
→ Detecta: ["arduino", "sensor de temperatura"]
→ Busca "arduino" en AV → encuentra, precio directo
→ Busca "sensor de temperatura" en AV → no encuentra
→ Busca en externas → encuentra con margen
→ Cliente selecciona una opción de cada uno
→ Ambos se agregan al carrito
```

### Caso 4: Producto no encontrado en ninguna tienda
```
Mensaje: "necesito un flux capacitor"
→ Detecta: "flux capacitor"
→ Busca en AV → no encuentra
→ Busca en Megatronica → no encuentra
→ Busca en ElectroStore → no encuentra
→ Se muestra: "Producto no encontrado en ninguna tienda"
→ No se agrega al carrito
```

### Caso 5: Admin cambia el margen
```
Admin entra a Configuración → cambia margen de 5% a 15%
→ Guarda en BD
→ Próximas búsquedas mostrarán precios con 15%
→ Cotizaciones pasadas mantienen su margen original
```

---

## 9. Pendientes de decisión

- [ ] ¿La entrada de texto libre viene por WhatsApp, por el formulario web, o ambos?
- [ ] ¿Se necesita integración con WhatsApp Business API o es solo el formulario web?
- [ ] ¿El cliente puede escribir la cantidad de unidades en el mensaje (ej: "3 arduinos")?
- [ ] ¿Se debe mostrar el desglose (precio base + margen) o solo el precio final?
- [ ] ¿Qué pasa si el cliente escribe un término muy genérico (ej: "luces")?
- [ ] ¿Se necesita autocompletado/sugerencias mientras el cliente escribe?

---

## 10. Próximos pasos

1. **Revisar y validar este documento** con el cliente
2. Decidir los pendientes de la sección 9
3. Diseñar los selectores de scraping para páginas de búsqueda (no solo producto)
4. Implementar backend: filtro → búsqueda priorizada → configuración
5. Implementar frontend: mensaje libre → tarjetas → carrito → admin
6. Pruebas end-to-end con casos de la sección 8

---

## 11. Entrada multimodal: Voz, Imagen y Archivo

El cliente puede ingresar su lista de componentes de 4 formas distintas.
Todas convergen al mismo punto: **texto plano** que se filtra y procesa.

```
  🎤 Voz          📷 Imagen        📄 Archivo        ⌨️ Texto
     │               │                │               │
     ▼               ▼                ▼               │
  Speech-to-Text   OCR / Vision    Parser de PDF     │
     │               │                │               │
     └───────────────┴────────────────┘               │
                     │                                 │
                     ▼                                 │
              TEXTO PLANO ◄────────────────────────────┘
                     │
                     ▼
            Filtro de palabras clave
                     │
                     ▼
            Búsqueda en tiendas
```

### 11.1 Entrada por voz (Speech-to-Text)

El cliente habla: *"Buscame si existen focos LED color azul"* y el sistema lo convierte a texto.

#### Opción A: Web Speech API (Navegador) — Recomendado

**Tecnología:** JavaScript nativo del navegador (Chrome, Edge, Safari)
**Costo:** Gratuito, sin API key, sin backend
**Latencia:** Tiempo real (streaming)
**Precisión:** Alta en español (Google dictation engine integrado en Chrome)

```typescript
// Frontend — sin necesidad de backend
const recognition = new webkitSpeechRecognition()
recognition.lang = 'es-ES'
recognition.continuous = false
recognition.interimResults = true

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript
  // transcript = "buscame si existen focos led color azul"
}
recognition.start()
```

**Ventajas:**
- Cero costo
- Sin dependencias externas
- Funciona offline (Chrome usa motor local)
- Resultado inmediato

**Desventajas:**
- Solo funciona en Chrome/Edge/Safari (no Firefox)
- Requiere permiso de micrófono del navegador
- No funciona en móviles viejos

#### Opción B: OpenAI Whisper API (Cloud)

**Tecnología:** API de OpenAI (`whisper-1`)
**Costo:** $0.006/minuto de audio
**Precisión:** Muy alta, excelente en español

```python
# Backend
import openai

audio_file = open("cliente.wav", "rb")
transcript = openai.Audio.transcribe("whisper-1", audio_file)
texto = transcript.text
# texto = "buscame si existen focos led color azul"
```

**Ventajas:**
- Funciona en cualquier navegador (el audio se graba y se envía)
- Precisión superior
- Maneja ruido de fondo bien

**Desventajas:**
- Requiere API key (costo bajo pero existe)
- Latencia: 2-5 segundos por grabación
- Requiere conexión a internet

#### Opción C: Whisper local (Python)

**Tecnología:** `openai-whisper` corriendo localmente
**Costo:** Gratuito (open source)
**Precisión:** Alta

```python
# Backend
import whisper

model = whisper.load_model("base")
result = model.transcribe("cliente.wav", language="es")
texto = result["text"]
```

**Ventajas:**
- Sin costo de API
- Funciona offline

**Desventajas:**
- Requiere GPU para velocidad aceptable (sin GPU: 10-30s por audio corto)
- Modelo de 1.5GB que se descarga al contenedor
- Mayor uso de RAM

#### Recomendación

| Escenario | Recomendación |
|---|---|
| Web app en Chrome/Edge | **Opción A** (Web Speech API) — gratuito, inmediato |
| Si se necesita máxima compatibilidad | **Opción B** (Whisper API) — $0.006/min, muy preciso |
| Si no se quiere pagar API | **Opción C** (Whisper local) — requiere GPU en el server |

### 11.2 Entrada por imagen (OCR)

El cliente sube una foto de su lista de componentes (ej: foto de un cuaderno, screenshot de WhatsApp).

#### Opción A: Tesseract OCR (Python) — Recomendado

**Tecnología:** `pytesseract` + `Pillow`
**Costo:** Gratuito (open source)
**Idiomas:** Español soportado

```python
# Backend
import pytesseract
from PIL import Image

imagen = Image.open("lista_cliente.png")
texto = pytesseract.image_to_string(imagen, lang='spa')
# texto = "5 resistencias de 220\n10 leds rojos\n1 arduino"
```

**Ventajas:**
- Gratuito
- Funciona offline
- Soporta español

**Desventajas:**
- Precisión media en fotos con mala iluminación o ángulo
- No lee texto manuscrito bien (solo texto impreso/digital)
- Requiere preprocesamiento de imagen (escalar, binarizar)

#### Opción B: Tesseract.js (Navegador)

**Tecnología:** JavaScript, corre en el navegador
**Costo:** Gratuito

```typescript
// Frontend — sin backend
import Tesseract from 'tesseract.js'

const { data: { text } } = await Tesseract.recognize(
  imagenFile,
  'spa'
)
// text = "5 resistencias de 220\n10 leds rojos"
```

**Ventajas:**
- Cero carga en el backend
- Gratuito
- El cliente no necesita enviar la imagen al server

**Desventajas:**
- Más lento que el backend (5-15s por imagen)
- Precisión similar a Opción A

#### Opción C: Google Cloud Vision API

**Tecnología:** Google Cloud Vision — `document_text_detection`
**Costo:** $1.50 por 1000 imágenes
**Precisión:** Muy alta, lee manuscrito

```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()
image = vision.Image(content=imagen_bytes)
response = client.document_text_detection(image=image)
texto = response.full_text_annotation.text
```

**Ventajas:**
- Lee texto manuscrito (fotos de cuadernos)
- Maneja fotos con mala calidad
- Detecta automáticamente el idioma

**Desventajas:**
- Requiere cuenta de Google Cloud + API key
- Costo por uso

#### Opción D: EasyOCR / PaddleOCR (Python)

**Tecnología:** Deep learning OCR
**Costo:** Gratuito (open source)
**Precisión:** Alta, mejor que Tesseract

```python
import easyocr
reader = easyocr.Reader(['es'])
result = reader.readtext('lista_cliente.png')
texto = ' '.join([d[1] for d in result])
```

**Ventajas:**
- Mejor precisión que Tesseract
- Lee texto en ángulo
- Soporta español

**Desventajas:**
- Requiere GPU para velocidad (sin GPU: 10-20s por imagen)
- Modelo de 500MB+

#### Recomendación

| Escenario | Recomendación |
|---|---|
| Fotos de pantalla / listas impresas | **Opción A** (Tesseract) o **Opción B** (Tesseract.js) |
| Fotos de cuaderno manuscrito | **Opción C** (Google Vision) — lee manuscrito |
| Sin GPU y sin API | **Opción B** (Tesseract.js en navegador) |

### 11.3 Entrada por archivo (PDF, Word, Excel, TXT)

El cliente sube un archivo con su lista de componentes.

#### Formatos soportados y librerías

| Formato | Librería Python | Alternativa JS |
|---|---|---|
| `.txt` | Ya implementado (lectura directa) | — |
| `.pdf` | `pdfplumber` (mejor que PyPDF2) | `pdf.js` (navegador) |
| `.docx` | `python-docx` | `mammoth.js` (navegador) |
| `.xlsx` | `openpyxl` (ya instalado) | `sheetjs` (navegador) |
| `.csv` | `csv` (stdlib) | PapaParse (navegador) |
| `.png/.jpg` | OCR (ver sección 11.2) | Tesseract.js |

#### Implementación Python (backend)

```python
import pdfplumber
from docx import Document
import openpyxl

def extraer_texto_pdf(archivo_bytes: bytes) -> str:
    """Extrae texto de un PDF."""
    import io
    with pdfplumber.open(io.BytesIO(archivo_bytes)) as pdf:
        return '\n'.join(page.extract_text() or '' for page in pdf.pages)

def extraer_texto_docx(archivo_bytes: bytes) -> str:
    """Extrae texto de un Word."""
    import io
    doc = Document(io.BytesIO(archivo_bytes))
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())

def extraer_texto_xlsx(archivo_bytes: bytes) -> str:
    """Extrae texto de un Excel (cada celda como línea)."""
    import io
    wb = openpyxl.load_workbook(io.BytesIO(archivo_bytes), read_only=True)
    lineas = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if cell is not None:
                    lineas.append(str(cell))
    return '\n'.join(lineas)
```

**Ventajas:**
- Todo en Python, sin APIs externas
- `pdfplumber` y `python-docx` son ligeros
- Ya tenemos `openpyxl` instalado

**Desventajas:**
- PDFs escaneados (imágenes) necesitan OCR adicional
- PDFs con tablas complejas pueden requerir preprocesamiento

#### Alternativa: Todo en el navegador (JavaScript)

| Formato | Librería JS | Ventaja |
|---|---|---|
| `.pdf` | `pdf.js` (Mozilla) | Sin backend, rápido |
| `.docx` | `mammoth.js` | Convierte a HTML/texto |
| `.xlsx` | `SheetJS` | Extrae celdas |
| `.csv` | PapaParse | Ultra rápido |
| `.txt` | FileReader API | Nativo del navegador |

**Ventaja clave:** Si hacemos todo en el navegador, el backend solo recibe texto plano, sin importar el formato original. Simplifica el backend enormemente.

### 11.4 Matriz de decisión: Python vs Alternativas

| Funcionalidad | ¿Python puede? | Alternativa | ¿Cuándo usar la alternativa? |
|---|---|---|---|
| **Voz → Texto** | ✅ Whisper local | Web Speech API (JS) | Siempre que sea web app en Chrome/Edge — gratuito e inmediato |
| **Voz → Texto (cloud)** | ✅ OpenAI API | Google Speech API | Si se quiere máxima precisión y compatibilidad |
| **Imagen → Texto (OCR)** | ✅ Tesseract/EasyOCR | Tesseract.js (navegador) | Si no hay GPU en el server |
| **Imagen → Texto (manuscrito)** | ⚠️ Difícil | Google Vision API | Si el cliente manda fotos de cuaderno |
| **PDF → Texto** | ✅ pdfplumber | pdf.js (navegador) | Ambos funcionan bien |
| **Word → Texto** | ✅ python-docx | mammoth.js (navegador) | Ambos funcionan bien |
| **Excel → Texto** | ✅ openpyxl | SheetJS (navegador) | Ambos funcionan bien |

### 11.5 Arquitectura propuesta para multimodalidad

```
┌─────────────────────────────────────────────────────────┐
│ FRONTEND (Navegador)                                    │
│                                                          │
│  🎤 Botón micrófono                                      │
│     └→ Web Speech API (Chrome) → texto                   │
│     └→ [Fallback] Grabar audio → enviar a backend        │
│                                                          │
│  📷 Botón imagen                                         │
│     └→ Tesseract.js (OCR en navegador) → texto           │
│     └→ [Fallback] Enviar imagen a backend                │
│                                                          │
│  📄 Botón archivo                                        │
│     └→ FileReader / pdf.js / mammoth.js → texto          │
│     └→ [Fallback] Enviar archivo a backend               │
│                                                          │
│  ⌨️ Caja de texto                                       │
│     └→ Texto directo                                     │
│                                                          │
│  Todo converge a: TEXTO PLANO                            │
│  → Se envía al backend como texto                        │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ BACKEND (Python)                                         │
│                                                          │
│  Recibe texto plano                                      │
│  → Filtro de palabras clave                              │
│  → Búsqueda en tiendas                                   │
│  → Retorna opciones al frontend                          │
│                                                          │
│  [Solo si el navegador no pudo procesar:]                │
│  → Whisper API (audio)                                   │
│  → Tesseract / EasyOCR (imagen)                          │
│  → pdfplumber / python-docx (archivo)                    │
└─────────────────────────────────────────────────────────┘
```

### 11.6 Estrategia recomendada: Frontend-first

**Principio:** Procesar en el navegador primero, backend como fallback.

| Modalidad | Primera opción (frontend) | Fallback (backend) |
|---|---|---|
| Voz | Web Speech API (JS) | OpenAI Whisper API |
| Imagen | Tesseract.js | Tesseract Python o Google Vision |
| Archivo | pdf.js / mammoth.js / SheetJS | pdfplumber / python-docx / openpyxl |
| Texto | Input directo | — |

**Beneficios:**
- Backend más simple (solo recibe texto)
- Menor carga del servidor
- Respuesta más rápida (sin upload/download)
- Funciona offline en el navegador

**Cuando usar backend:**
- Navegador no soporta Web Speech API (Firefox)
- Imagen manuscrita (necesita Google Vision)
- Archivo muy grande (>25MB)

### 11.7 Dependencias necesarias

#### Frontend (npm)

```json
{
  "tesseract.js": "^5.0.0",
  "mammoth": "^1.6.0",
  "pdfjs-dist": "^4.0.0",
  "xlsx": "^0.18.5"
}
```

#### Backend (requirements.txt) — solo para fallback

```
openai-whisper==20231117    # Voz (si se usa Whisper local)
pytesseract==0.3.10         # OCR (si se usa Tesseract backend)
Pillow==10.2.0              # Procesamiento de imagen
pdfplumber==0.11.0          # PDF
python-docx==1.1.0          # Word
easyocr==1.7.1              # OCR avanzado (opcional)
```

#### Sistema (Dockerfile)

```dockerfile
# Para Tesseract OCR (si se usa backend)
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-spa

# Para Whisper local (si se usa)
# Requiere GPU o mucho CPU
```

---

## 12. Pendientes de decisión (actualizado)

- [ ] ¿La entrada de texto libre viene por WhatsApp, por el formulario web, o ambos?
- [ ] ¿Se necesita integración con WhatsApp Business API o es solo el formulario web?
- [ ] ¿El cliente puede escribir la cantidad de unidades en el mensaje (ej: "3 arduinos")?
- [ ] ¿Se debe mostrar el desglose (precio base + margen) o solo el precio final?
- [ ] ¿Qué pasa si el cliente escribe un término muy genérico (ej: "luces")?
- [ ] ¿Se necesita autocompletado/sugerencias mientras el cliente escribe?
- [ ] **Voz: ¿Web Speech API (gratuito, Chrome) o Whisper API ($0.006/min, universal)?**
- [ ] **Imagen: ¿Tesseract (gratuito, impreso) o Google Vision ($1.50/1000 imgs, lee manuscrito)?**
- [ ] **Archivo: ¿Procesar en navegador (JS) o en backend (Python)?**
- [ ] **¿El cliente puede usar voz e imagen al mismo tiempo (ej: grabar voz mientras ve resultados)?**

---

## 13. Análisis QA: Viabilidad técnica del documento

### Veredicto general: ⚠️ Viable con ajustes críticos

El documento es funcionalmente sólido pero tiene **5 problemas técnicos críticos** que deben corregirse antes de implementar.

---

### 🔴 Problemas críticos (bloquean implementación)

#### CRÍTICO 1: Los scrapers solo retornan 1 resultado, no múltiples

**Lo que dice el documento:** Mostrar múltiples opciones por componente (ej: Arduino UNO, Nano, Mega).

**Lo que hace el código actual:** Tanto `StaticScraper.scrape()` como `DynamicScraper.scrape()` hacen `return` en el **primer** producto encontrado:

```python
# static_scraper.py:98-103
if precio is not None:
    result = {
        "precio": precio,
        "disponible": disponible,
        "url": url_producto,
    }
    return result  # ← RETORNA EL PRIMERO Y SALE
```

**Impacto:** El documento propone mostrar 3 Arduinos al cliente, pero el scraper actual solo retornaría 1.

**Solución:** Modificar `scrape()` para retornar `list[dict]` en vez de `dict`. Cambiar el `return result` por `results.append(...)` y seguir iterando.

**Esfuerzo:** Medio — cambiar interfaz de `scrape()`, actualizar `engine.py`, actualizar caché.

---

#### CRÍTICO 2: ScrapingCache está indexada por `producto_id`, no por término

**Lo que dice el documento:** Buscar por término libre ("arduino", "sensor de temperatura") y cachear resultados.

**Lo que hace el código actual:** `ScrapingCache` requiere `producto_id` (FK a `productos.id`):

```python
# scraping_cache.py:17
producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), nullable=False)
```

**Impacto:** Si el cliente busca "sensor de temperatura" y ese término no corresponde a un producto en la BD, no hay `producto_id` para el caché. La búsqueda por término no se puede cachear con la estructura actual.

**Solución:** Opción A: Crear `ScrapingCacheTermino` con `(termino, tienda)` como clave. Opción B: Hacer `producto_id` nullable y agregar columna `termino_busqueda`.

**Esfuerzo:** Medio — nueva tabla o migración + cambios en `engine.py`.

---

#### CRÍTICO 3: `buscar_precios` depende de `Producto` en BD, no de texto libre

**Lo que dice el documento:** `buscar_por_termino(db, termino: str)` — buscar directamente por texto.

**Lo que hace el código actual:** `buscar_precios(db, producto: Producto)` requiere un objeto `Producto` de la BD con ID:

```python
# engine.py:15
async def buscar_precios(db: AsyncSession, producto: Producto) -> list[dict]:
```

El `generator.py` primero hace `_buscar_producto(db, comp)` para encontrar un producto en BD, y solo si existe busca precios.

**Impacto:** Si el cliente busca algo que no está en la tabla `productos` (ej: "motor dc"), el sistema actual no busca precios. El documento asume que se busca directamente en las tiendas sin pasar por la BD local.

**Solución:** Crear función `buscar_por_termino(db, termino: str)` que:
1. Construya la URL de búsqueda de la tienda
2. Scrapee los resultados
3. No dependa de `producto_id` ni de la tabla `productos`

**Esfuerzo:** Alto — nueva función, nuevo modelo de caché, nueva lógica de scraping.

---

#### CRÍTICO 4: El filtro de stopwords tiene una contradicción lógica

**Lo que dice el documento:** Filtrar "de" como stopword, pero también mantener "de" para unir "sensor" + "temperatura".

**El problema en la tabla del documento (líneas 54-55):**
```
| "de"  | Preposición — descartar |  ← línea 48 (descartar)
| "de"  | Preposición — mantener   |  ← línea 54 (mantener, une sensor+temperatura)
```

La misma palabra "de" aparece como descartar Y mantener. Un filtro de stopwords simple no puede hacer esto.

**Solución:** El filtro necesita lógica de **ventana deslizante** (n-grams):
1. No filtrar stopwords a ciegas
2. Buscar bigramas/trigramas que coincidan con tipos conocidos ("sensor de temperatura", "motor de paso")
3. Luego filtrar el resto

Alternativa: Usar el diccionario `TIPOS_PALABRAS` existente en `normalizer.py` que ya tiene "sensor", "motor dc", "paso a paso" como tipos reconocidos. En vez de filtrar stopwords, buscar matches contra este diccionario.

**Esfuerzo:** Medio — reescribir `extraer_componentes` con lógica de n-grams.

---

#### CRÍTICO 5: ElectroStore no vende componentes electrónicos

**Lo que dice el documento:** "Buscar en Tienda 3" como tercera opción de electrónica.

**La realidad:** ElectroStore (https://electrostoree.com/) es una tienda Shopify de Uruguay con:
- 1 solo producto: Game Stick M15 Plus ($2.390 UYU)
- No vende Arduino, sensores, resistencias, ni ningún componente electrónico
- Plataforma: Shopify (no WooCommerce) — selectores diferentes
- Precios en UYU (pesos uruguayos), no USD

**Solución:** Agregar ElectroStore al seed con selectores de Shopify. La búsqueda de componentes retornará 0 resultados la mayoría de las veces, pero queda configurada por si expanden catálogo. Hay que agregar selectores de Shopify (diferentes a WooCommerce).

**Esfuerzo:** Bajo — agregar seed + selectores Shopify.

---

### 🟡 Problemas menores (no bloquean pero hay que corregir)

#### MENOR 1: `MARGEN_COMPETENCIA` se lee en múltiples archivos

**Lo que dice el documento:** El margen pasa de `config.py` a BD.

**Lo que hace el código actual:** `settings.MARGEN_COMPETENCIA` se importa en:
- `generator.py` (línea 6)
- `config.py` (definición)

**Impacto:** Cambiar a BD significa que `generator.py` no puede hacer `from app.core.config import settings` y leer `settings.MARGEN_COMPETENCIA`. Necesita una consulta a BD en cada generación de cotización.

**Solución:** Crear `app/services/configuracion.py` con `async obtener_margen(db) -> float` que lea de la tabla `configuracion_negocio`. Todos los lugares que usen el margen deben llamar esta función.

**Esfuerzo:** Bajo — 1 función + 2-3 cambios de import.

---

#### MENOR 2: El scraper ya soporta URL de búsqueda

**Lo que dice el documento (sección 7.1):** "Construir la URL de búsqueda de la tienda".

**Lo que ya hace el código:** `BaseScraper._build_search_url()` ya construye la URL:
```python
# base.py:16-22
def _build_search_url(self, query: str) -> str:
    template = self.selectores.get("search_url", "")
    if template and "{query}" in template:
        return template.replace("{query}", quote_plus(query))
```

Y los selectores de AV Electronics ya incluyen `search_url`:
```python
"search_url": "https://avelectronics.cc/?s={query}"
```

**Conclusión:** ✅ Esto ya funciona. No necesita desarrollo.

---

#### MENOR 3: El carrito y selección ya están parcialmente implementados

**Lo que dice el documento (sección 4.2):** Nuevos componentes para carrito y selección.

**Lo que ya existe:**
- `CotizacionItem` tiene `seleccionado`, `opciones_proveedores`, `es_propio`
- Backend tiene `agregar_item_cotizacion` y `finalizar_cotizacion`
- Frontend tiene `CotizacionTable` con selección de proveedor

**Conclusión:** ✅ Parcialmente implementado. El carrito existe pero hay que adaptar la UI al nuevo flujo conversacional.

---

#### MENOR 4: Web Speech API requiere tipos TypeScript

**Lo que dice el documento:** Usar `webkitSpeechRecognition` en el frontend.

**El problema:** TypeScript no tiene tipos para `SpeechRecognition` por defecto. Generará errores de compilación.

**Solución:** Agregar `@types/webkit-speech-recognition` o declarar los tipos manualmente en un `.d.ts`.

**Esfuerzo:** Bajo — 1 archivo de tipos.

---

#### MENOR 5: Tesseract.js en Vite necesita configuración

**Lo que dice el documento:** Usar Tesseract.js en el navegador.

**El problema:** Tesseract.js usa Web Workers y descarga archivos WASM. Con Vite puede haber problemas de path resolution.

**Solución:** Configurar `vite.config.ts` para excluir Tesseract.js del bundling o usar `import.meta.url` para los paths de workers.

**Esfuerzo:** Bajo — configuración de Vite.

---

### 🟢 Lo que ya funciona y no necesita cambios

| Componente | Estado | Referencia |
|---|---|---|
| URL de búsqueda por tienda | ✅ Funciona | `base.py:16-22` |
| Selectores de AV Electronics | � configurado | `main.py:23-30` |
| Scraper estático (BeautifulSoup) | ✅ Funciona | `static_scraper.py` |
| Scraper dinámico (Playwright) | ✅ Funciona | `dynamic_scraper.py` |
| Modelo `CotizacionItem` con selección | ✅ Implementado | `cotizacion.py` (sesión anterior) |
| Endpoint `agregar_item_cotizacion` | ✅ Implementado | `cotizacion.py` (sesión anterior) |
| Endpoint `finalizar_cotizacion` | ✅ Implementado | `cotizacion.py` (sesión anterior) |
| Defaults automáticos por tipo | ✅ Implementado | `normalizer.py` (sesión anterior) |
| Máx. 2 preguntas | ✅ Implementado | `config.py` (sesión anterior) |

---

### 📋 Matriz de viabilidad corregida

| Propuesta del documento | ¿Es viable? | ¿Qué falta? | Esfuerzo real |
|---|---|---|---|
| Filtro de palabras clave | ⚠️ Sí, pero no con stopwords simples | Reescribir con n-grams + diccionario `TIPOS_PALABRAS` | Medio |
| Búsqueda por término (no por producto) | ⚠️ Sí, pero requiere reescribir scrapers | Cambiar `scrape()` a retornar `list`, nuevo modelo de caché | Alto |
| Búsqueda priorizada (AV primero) | ✅ Sí | Ya existe la lógica de `TIENDA_PROPIA` en `generator.py` | Bajo |
| Margen configurable desde admin | ✅ Sí | Nueva tabla + endpoint + función de lectura | Bajo-Medio |
| Tarjetas de producto seleccionables | ✅ Sí | Nuevo componente React | Medio |
| Carrito de cotización | ✅ Parcialmente existe | Adaptar UI al flujo conversacional | Medio |
| Panel de admin para margen | ✅ Sí | Nueva página React + endpoint | Bajo |
| Voz → Texto (Web Speech API) | ✅ Sí | Tipos TypeScript + componente React | Bajo |
| Imagen → Texto (Tesseract.js) | ✅ Sí | Config Vite + componente React | Bajo-Medio |
| Archivo → Texto (pdf.js/mammoth/SheetJS) | ✅ Sí | Componentes React + npm install | Medio |
| Auto-sugerencias (driver para motor) | ✅ Ya implementado | `generator.py` (sesión anterior) | — |

---

### 🔧 Cambios necesarios en el documento

1. **Sección 2, paso 1:** Reescribir el filtro para usar n-grams + diccionario `TIPOS_PALABRAS` en vez de stopwords simples. Eliminar la contradicción de "de" (descartar vs mantener).

2. **Sección 7.1:** Aclarar que los scrapers YA soportan URL de búsqueda, pero necesitan modificarse para retornar múltiples resultados en vez de solo el primero.

3. **Sección 7.2:** El caché actual es por `producto_id`. Proponer nueva tabla `scraping_cache_termino` con clave `(termino, tienda)` o hacer `producto_id` nullable + agregar `termino`.

4. **Todas las referencias a "Tienda 3":** Reemplazadas por "ElectroStore". Se agrega al seed con `activa=False` y selectores de Shopify (diferentes a WooCommerce). El admin puede activarla desde el panel.

5. **Sección 6 (backend):** Agregar que `scrapers/base.py` y `scrapers/static_scraper.py` y `scrapers/dynamic_scraper.py` necesitan modificación (no solo `engine.py`).

6. **Sección 11.1 (voz):** Agregar nota sobre tipos TypeScript para `SpeechRecognition`.

7. **Sección 11.2 (imagen):** Agregar nota sobre configuración de Vite para Tesseract.js.

---

### 📊 Estimación de esfuerzo total corregida

| Fase | Esfuerzo | Tiempo estimado |
|---|---|---|
| Backend: Scrapers múltiples resultados | Alto | 3-4 días |
| Backend: Caché por término | Medio | 1-2 días |
| Backend: Filtro n-grams | Medio | 1-2 días |
| Backend: Margen desde BD | Bajo-Medio | 1 día |
| Backend: Endpoint búsqueda por término | Medio | 1 día |
| Frontend: UI conversacional + tarjetas | Medio | 2-3 días |
| Frontend: Carrito adaptado | Medio | 1-2 días |
| Frontend: Panel admin margen | Bajo | 0.5 días |
| Frontend: Voz (Web Speech API) | Bajo | 0.5 días |
| Frontend: Imagen (Tesseract.js) | Bajo-Medio | 1 día |
| Frontend: Archivo (pdf.js/mammoth/SheetJS) | Medio | 1-2 días |
| Pruebas e integración | — | 2-3 días |
| **Total** | | **14-20 días** |
