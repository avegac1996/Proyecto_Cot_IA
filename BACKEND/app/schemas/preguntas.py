from uuid import UUID

from pydantic import BaseModel


class PreguntaItem(BaseModel):
    id: int
    categoria: str
    pregunta: str
    campo_a_desambiguar: str | None = None
    componentes_afectados: list[int]


class PreguntasResponse(BaseModel):
    session_id: UUID
    preguntas: list[PreguntaItem]
    total_preguntas: int


class RespuestaItem(BaseModel):
    pregunta_id: int
    respuesta: str


class RespuestasRequest(BaseModel):
    respuestas: list[RespuestaItem]


class RespuestasResponse(BaseModel):
    session_id: UUID
    componentes_actualizados: bool
    ambiguedades_restantes: int
