@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  CotIA - Script de Iniciacion
REM  Recrea Docker, base de datos y levanta todos los servicios
REM ============================================================

echo.
echo  ============================================
echo   CotIA - Iniciando entorno desde cero
echo  ============================================
echo.

REM ─── Paso 0: Verificar que Docker Desktop este corriendo ───
echo  [0/5] Verificando que Docker Desktop este corriendo...
set /a docker_wait=0
:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    set /a docker_wait+=1
    if !docker_wait! geq 30 (
        echo.
        echo  ERROR: Docker Desktop no esta corriendo o no responde.
        echo  Inicia Docker Desktop y vuelve a ejecutar este script.
        echo.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto wait_docker
)
echo  Docker listo.
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
set /a pg_wait=0
:wait_pg
docker inspect --format="{{.State.Health.Status}}" cotia_postgres 2>nul | findstr healthy >nul
if errorlevel 1 (
    set /a pg_wait+=1
    if !pg_wait! geq 60 (
        echo.
        echo  ERROR: PostgreSQL no respondio en 2 minutos. Revisa los logs:
        echo  docker logs cotia_postgres
        echo.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto wait_pg
)
echo  PostgreSQL listo.
echo.

REM ─── Esperar al backend ───
echo  Esperando que el backend este listo...
set /a be_wait=0
:wait_be
docker logs cotia_backend 2>&1 | findstr "Application startup complete" >nul
if errorlevel 1 (
    set /a be_wait+=1
    if !be_wait! geq 60 (
        echo.
        echo  ERROR: El backend no levanto en 2 minutos. Revisa los logs:
        echo  docker logs cotia_backend
        echo.
        pause
        exit /b 1
    )
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
