from pydantic import BaseModel


class ProductoResponse(BaseModel):
    id: int
    nombre: str
    categoria: str
    especificaciones: dict
    terminos_coloquiales: list[str] | None = None

    model_config = {"from_attributes": True}


class ProductoSearchResponse(BaseModel):
    resultados: list[ProductoResponse]
    total: int
