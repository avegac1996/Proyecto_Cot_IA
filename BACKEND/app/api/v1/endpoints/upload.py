from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.sesion import Sesion
from app.models.usuario import Usuario
from app.schemas.upload import UploadResponse
from app.services.ingesta.audio import transcribir_audio
from app.services.ingesta.imagen import extraer_texto_imagen
from app.services.ingesta.texto import parsear_texto

router = APIRouter(prefix="/upload", tags=["upload"])

EXTENSIONES_POR_TIPO = {
    "texto": {".txt", ".csv"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg"},
    "imagen": {".jpg", ".jpeg", ".png", ".webp"},
}


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    tipo: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if tipo not in EXTENSIONES_POR_TIPO:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={"code": "INVALID_FILE_TYPE", "message": f"Tipo '{tipo}' no soportado. Use: audio, imagen, texto"},
        )

    nombre = (file.filename or "").lower()
    extension = "." + nombre.rsplit(".", 1)[-1] if "." in nombre else ""
    if extension not in EXTENSIONES_POR_TIPO[tipo]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": f"Extensión '{extension}' no válida para tipo '{tipo}'. Permitidas: {sorted(EXTENSIONES_POR_TIPO[tipo])}",
            },
        )

    contenido_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(contenido_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"El archivo excede el tamaño máximo de {settings.MAX_FILE_SIZE_MB}MB",
                "details": {"max_size_mb": settings.MAX_FILE_SIZE_MB},
            },
        )

    try:
        if tipo == "texto":
            texto = contenido_bytes.decode("utf-8", errors="ignore")
            componentes = parsear_texto(texto)
        elif tipo == "audio":
            componentes = transcribir_audio(contenido_bytes, extension)
        elif tipo == "imagen":
            componentes = extraer_texto_imagen(contenido_bytes)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={"code": "INVALID_FILE_TYPE", "message": f"Tipo '{tipo}' no soportado"},
            )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "PROCESSING_UNAVAILABLE", "message": str(exc)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROCESSING_ERROR", "message": f"Error al procesar el archivo: {exc}"},
        )

    if not componentes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "No se detectaron componentes en el archivo"},
        )

    sesion = Sesion(
        usuario_id=user.id,
        componentes_json=componentes,
        ambiguedades_resueltas=not any(c["ambiguo"] for c in componentes),
        estado="activa",
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)

    return UploadResponse(
        session_id=sesion.id,
        componentes=componentes,
        ambiguedades_detectadas=any(c["ambiguo"] for c in componentes),
        total_componentes=len(componentes),
    )
