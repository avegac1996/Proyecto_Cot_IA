from uuid import UUID

from pydantic import BaseModel


class ComponenteExtraido(BaseModel):
    texto_original: str
    tipo: str
    valor: str | None = None
    unidad: str | None = None
    cantidad: int = 1
    ambiguo: bool = False
    ambiguedades: list[str] = []


class UploadResponse(BaseModel):
    session_id: UUID
    componentes: list[ComponenteExtraido]
    ambiguedades_detectadas: bool
    total_componentes: int
