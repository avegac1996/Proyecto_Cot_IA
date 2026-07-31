@echo off
REM ============================================================
REM  CotIA - Script de Iniciacion
REM  Recrea Docker, base de datos y levanta todos los servicios
REM ============================================================

echo.
echo  ============================================
echo   CotIA - Iniciando entorno desde cero
echo  ============================================
echo.

REM ─── Paso 1: Detener contenedores existentes ───
echo  [1/5] Deteniendo contenedores existentes...
docker compose down
echo  Listo.
echo.

REM ─── Paso 2: Borrar volumenes (recrea BD desde cero) ───
echo  [2/5] Borrando volumenes (BD se recreara desde cero)...
docker compose down -v
echo  Listo.
echo.

REM ─── Paso 3: Construir imagenes ───
echo  [3/5] Construyendo imagenes Docker...
docker compose build --no-cache
echo  Listo.
echo.

REM ─── Paso 4: Levantar todos los servicios ───
echo  [4/5] Levantando servicios...
docker compose up -d
echo  Listo.
echo.

REM ─── Paso 5: Esperar a que PostgreSQL este healthy ───
echo  [5/5] Esperando que PostgreSQL este listo...
:wait_pg
docker inspect --format="{{.State.Health.Status}}" cotia_postgres 2>nul | findstr healthy >nul
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_pg
)
echo  PostgreSQL listo.
echo.

REM ─── Esperar al backend ───
echo  Esperando que el backend este listo...
:wait_be
docker logs cotia_backend 2>&1 | findstr "Application startup complete" >nul
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_be
)
echo  Backend listo.
echo.

REM ─── Mostrar estado ───
echo  ============================================
echo   Todos los servicios estan corriendo:
echo  ============================================
echo.
docker ps --filter name=cotia --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo  ============================================
echo   URLs de acceso:
echo  ============================================
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   Swagger:   http://localhost:8000/docs
echo   pgAdmin:   http://localhost:5050
echo.
echo   Login Admin: admin@cotia.com / Admin123!
echo   Login User:  user@cotia.com  / User123!
echo  ============================================
echo.
pause
