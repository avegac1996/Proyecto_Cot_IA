@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  CotIA - Start rapido
REM  Levanta backend y frontend SIN borrar la base de datos
REM ============================================================

echo.
echo  ============================================
echo   CotIA - Levantando servicios (sin reset)
echo  ============================================
echo.

REM ─── Verificar que Docker Desktop este corriendo ───
echo  Verificando Docker Desktop...
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

REM ─── Levantar servicios (sin borrar volumenes ni rebuild) ───
echo  Levantando servicios...
docker compose up -d
if errorlevel 1 (
    echo.
    echo  ERROR: No se pudieron levantar los servicios.
    echo  Si es la primera vez, ejecuta iniciar.bat primero.
    echo.
    pause
    exit /b 1
)
echo  Listo.
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

echo  ============================================
echo   Servicios corriendo:
echo  ============================================
docker ps --filter name=cotia --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   Swagger:   http://localhost:8000/docs
echo  ============================================
echo.
pause
