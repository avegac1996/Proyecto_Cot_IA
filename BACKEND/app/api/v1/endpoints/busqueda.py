from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services.ingesta.filtro import extraer_componentes
from app.services.scraping.busqueda import buscar_por_termino_priorizado
from app.services.scraping.engine import buscar_por_termino
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
    resultados = []
    for comp in componentes:
        resultado = await buscar_por_termino_priorizado(
            db, comp["termino"], comp["cantidad"]
        )
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

    for termino in terminos_busqueda:
        if len(alternativas) >= 10:
            break
        resultado = await buscar_por_termino(db, termino)
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
