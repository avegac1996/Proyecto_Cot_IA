from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services.gemini.vision import identificar_componentes_imagen
from app.services.gemini.chat import preguntar_agente
from app.services.ingesta.filtro import extraer_componentes
from app.services.scraping.busqueda import buscar_por_termino_priorizado
from app.services.scraping.engine import buscar_por_termino, limpiar_cache_termino
from app.services.configuracion import obtener_margen, obtener_tienda_propia

router = APIRouter(prefix="/buscar", tags=["busqueda"])


class BusquedaRequest(BaseModel):
    texto: str


class OpcionProducto(BaseModel):
    tienda: str
    nombre_producto: str
    precio_base: float | None
    precio_con_margen: float | None
    margen_aplicado: float
    disponible: bool
    url: str | None
    es_propio: bool
    variantes: list[str] = []


class SugerenciaResponse(BaseModel):
    sugerencia: str
    razon: str


class ResultadoComponente(BaseModel):
    termino: str
    cantidad: int
    encontrado_propia: bool
    opciones: list[OpcionProducto]
    sugerencia: SugerenciaResponse | None = None


class BusquedaResponse(BaseModel):
    resultados: list[ResultadoComponente]


class AlternativaRequest(BaseModel):
    nombre_producto: str
    tienda_excluir: str


class AlternativaResponse(BaseModel):
    alternativas: list[OpcionProducto]


@router.post("", response_model=BusquedaResponse)
async def buscar_componentes(
    body: BusquedaRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Recibe texto libre, extrae componentes y busca en tiendas activas.

    Flujo:
    1. extraer_componentes(texto) → lista de términos con n-grams
    2. Por cada término, buscar_por_termino_priorizado(db, termino, cantidad)
    3. Retorna opciones por componente, AV Electronics primero (sin margen)
    """
    componentes = extraer_componentes(body.texto)

    # Limpiar cache en memoria para que cada búsqueda traiga resultados frescos
    limpiar_cache_termino()

    # Deduplicación global: un producto solo aparece una vez en toda la lista
    # Procesamos secuencialmente para que el primer término que encuentre un producto se quede con él
    productos_vistos = set()  # nombre_producto en lowercase
    from app.services.scraping.sugerencias import sugerir_termino

    resultados = []
    for comp in componentes:
        resultado = await buscar_por_termino_priorizado(db, comp["termino"], comp["cantidad"])
        opciones_filtradas = []
        for op in resultado.get("opciones", []):
            nombre_key = op["nombre_producto"].strip().lower()
            if nombre_key in productos_vistos:
                continue
            productos_vistos.add(nombre_key)
            opciones_filtradas.append(op)
        resultado["opciones"] = opciones_filtradas
        if not opciones_filtradas and not resultado.get("sugerencia"):
            resultado["sugerencia"] = sugerir_termino(comp["termino"])
        resultados.append(resultado)

    return BusquedaResponse(resultados=resultados)


@router.post("/alternativas", response_model=AlternativaResponse)
async def buscar_alternativas(
    body: AlternativaRequest,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Busca productos similares en tiendas externas cuando un producto está agotado.

    Estrategia fuzzy:
    1. Buscar con el nombre completo del producto
    2. Si hay pocos resultados, buscar con palabras clave individuales
    3. Filtrar la tienda donde está agotado
    4. Aplicar margen a tiendas externas
    """
    margen_pct = await obtener_margen(db)
    tienda_propia = await obtener_tienda_propia(db)
    margen_factor = 1 + margen_pct / 100

    nombre = body.nombre_producto.strip()
    if not nombre:
        return AlternativaResponse(alternativas=[])

    # Stopwords comunes en español para productos electrónicos
    stopwords = {"de", "del", "para", "con", "sin", "el", "la", "los", "las",
                 "un", "una", "unos", "unas", "y", "o", "u", "en", "por", "the",
                 "for", "with", "and", "or", "kit", "modulo", "módulo"}

    palabras = [p for p in nombre.lower().split() if p not in stopwords and len(p) > 2]

    # Generar términos de búsqueda: nombre completo + combinaciones de palabras clave
    terminos_busqueda = [nombre]
    if len(palabras) >= 2:
        # Buscar con las 2-3 palabras más significativas
        terminos_busqueda.append(" ".join(palabras[:3]))
        terminos_busqueda.append(" ".join(palabras[:2]))
        # Buscar con cada palabra individual (solo las más largas)
        for p in sorted(palabras, key=len, reverse=True)[:3]:
            terminos_busqueda.append(p)

    # Sinónimos: buscar términos equivalentes
    from app.services.matching.normalizer import TIPOS_PALABRAS
    for p in palabras:
        for tipo, sinonimos in TIPOS_PALABRAS.items():
            if p in sinonimos:
                # Agregar sinónimos que no sean la palabra original
                for sin in sinonimos:
                    if sin != p and sin not in terminos_busqueda:
                        terminos_busqueda.append(sin.replace(p, sin) if p in nombre else sin)
                break

    # Buscar y recolectar resultados únicos
    vistos = set()
    alternativas = []

    resultados_busqueda = await asyncio.gather(*[
        buscar_por_termino(db, termino) for termino in terminos_busqueda
    ])

    for resultado in resultados_busqueda:
        if len(alternativas) >= 10:
            break
        for op in resultado.get("opciones", []):
            if op["tienda"] == body.tienda_excluir:
                continue
            if op["precio_base"] is None:
                continue
            # Deduplicar por tienda + nombre
            key = f"{op['tienda']}::{op.get('nombre_producto', '')}"
            if key in vistos:
                continue
            vistos.add(key)

            if op["tienda"] == tienda_propia:
                alternativas.append(OpcionProducto(
                    tienda=op["tienda"],
                    nombre_producto=op.get("nombre_producto") or termino,
                    precio_base=op["precio_base"],
                    precio_con_margen=round(op["precio_base"], 2),
                    margen_aplicado=0.0,
                    disponible=op["disponible"],
                    url=op["url"],
                    es_propio=True,
                ))
            else:
                alternativas.append(OpcionProducto(
                    tienda=op["tienda"],
                    nombre_producto=op.get("nombre_producto") or termino,
                    precio_base=op["precio_base"],
                    precio_con_margen=round(op["precio_base"] * margen_factor, 2),
                    margen_aplicado=margen_pct,
                    disponible=op["disponible"],
                    url=op["url"],
                    es_propio=False,
                ))

    return AlternativaResponse(alternativas=alternativas)


class ImagenResponse(BaseModel):
    texto: str
    componentes: list[str]


@router.post("/imagen", response_model=ImagenResponse)
async def identificar_imagen(
    file: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
):
    """Recibe una imagen, la envía a Google Gemini Vision y devuelve los
    componentes electrónicos identificados en formato de lista."""

    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "GEMINI_NOT_CONFIGURED", "message": "Gemini API no configurada"},
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE", "message": "El archivo debe ser una imagen"},
        )

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "FILE_TOO_LARGE", "message": "La imagen no puede pesar más de 10MB"},
        )

    try:
        texto = await identificar_componentes_imagen(image_bytes, file.content_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "GEMINI_ERROR", "message": str(exc)},
        )

    componentes = [line.strip() for line in texto.split("\n") if line.strip()]

    return ImagenResponse(texto=texto, componentes=componentes)


class PreguntaRequest(BaseModel):
    pregunta: str
    resultados: list[dict]
    historial: list[dict] | None = None


class PreguntaResponse(BaseModel):
    respuesta: str


@router.post("/preguntar", response_model=PreguntaResponse)
async def preguntar(
    body: PreguntaRequest,
    user: Usuario = Depends(get_current_user),
):
    """Permite al usuario hacer preguntas sobre los resultados de búsqueda
    usando Google Gemini como asistente experto en electrónica."""

    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "GEMINI_NOT_CONFIGURED", "message": "Gemini API no configurada"},
        )

    if not body.pregunta.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_QUESTION", "message": "La pregunta no puede estar vacía"},
        )

    try:
        respuesta = await preguntar_agente(
            pregunta=body.pregunta,
            resultados=body.resultados,
            historial=body.historial,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "GEMINI_ERROR", "message": str(exc)},
        )

    return PreguntaResponse(respuesta=respuesta)
