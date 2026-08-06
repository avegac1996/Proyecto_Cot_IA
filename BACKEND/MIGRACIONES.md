# Migraciones de base de datos

El esquema se gestiona exclusivamente con Alembic. El backend ya no ejecuta
`Base.metadata.create_all()` al arrancar.

## Base de datos nueva

Ejecutar `alembic upgrade head`. Docker Compose lo hace automáticamente al
iniciar el backend, tanto en desarrollo como en producción.

## Base de datos existente

Primero haga una copia de seguridad. Después compruebe si la tabla
`alembic_version` existe y cuál es su revisión.

- Si la base está en `0001_initial`, ejecute `alembic upgrade head`.
- Si fue creada anteriormente con `create_all` y ya contiene todas las
  columnas y tablas de los modelos actuales, registre el estado con
  `alembic stamp 0002_align_current_models`; no ejecute la migración sobre
  ese esquema ya actualizado.
- Si contiene el esquema de `0001_initial` pero no tiene historial Alembic,
  ejecute primero `alembic stamp 0001_initial` y luego `alembic upgrade head`.

No use `stamp` sin verificar previamente el esquema: ese comando marca una
revisión sin aplicar cambios.
