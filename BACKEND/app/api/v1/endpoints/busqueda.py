from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services.ingesta.filtro import extraer_componentes
from app.services.scraping.busqueda import buscar_por_termino_priorizado

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


class ResultadoComponente(BaseModel):
    termino: str
    cantidad: int
    encontrado_propia: bool
    opciones: list[OpcionProducto]


class BusquedaResponse(BaseModel):
    resultados: list[ResultadoComponente]


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
