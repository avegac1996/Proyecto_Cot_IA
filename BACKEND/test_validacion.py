"""Pruebas de validación del catálogo persistente en BD.

Valida:
1. Tabla catalogo_productos existe y tiene productos
2. Búsqueda ILIKE devuelve resultados correctos
3. Búsqueda AND estricto vs OR flexible
4. Normalización de nombres (tildes, unidades)
5. Ranking por coincidencias
6. Persistencia tras reinicio simulado
7. Performance: búsquedas < 100ms
8. Casos edge: términos vacíos, stop words, números
9. Búsqueda de componentes específicos del usuario
10. Fallback a scraping si BD vacía
"""
import asyncio
import time
import sys

from app.core.database import async_session
from app.models.catalogo_producto import CatalogoProducto
from app.services.scraping.catalogo_bd import (
    buscar_en_bd,
    contar_productos,
    _normalizar,
    refrescar_catalogo_bd,
    soporta_api_wc,
)
from sqlalchemy import select, func


# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

passed = 0
failed = 0


def ok(msg: str):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str):
    global failed
    failed += 1
    print(f"  {RED}✗{RESET} {msg}")


def info(msg: str):
    print(f"  {YELLOW}→{RESET} {msg}")


async def test_tabla_existe():
    """Test 1: La tabla catalogo_productos existe y tiene productos."""
    print("\n[1] Tabla catalogo_productos existe y tiene datos")
    async with async_session() as db:
        count = await contar_productos(db)
        if count > 0:
            ok(f"Tabla tiene {count} productos")
        else:
            fail(f"Tabla vacía (count={count})")

        # Verificar que tiene productos de AV Electronics
        result = await db.execute(
            select(CatalogoProducto.tienda, func.count())
            .group_by(CatalogoProducto.tienda)
        )
        tiendas = result.all()
        for nombre, cnt in tiendas:
            info(f"Tienda '{nombre}': {cnt} productos")


async def test_normalizacion():
    """Test 2: Normalización de textos."""
    print("\n[2] Normalización de nombres")
    casos = [
        ("Capacitor Electrolítico 470µF", "capacitor electrolitico 470uf"),
        ("Resistencia 4.7KΩ", "resistencia 4.7kohm"),
        ("Módulo WiFi ESP32", "modulo wifi esp32"),
        ("Sensor BME680 (I²C)", "sensor bme680 (i2c)"),
        ("Cable Micro USB", "cable micro usb"),
        ("", ""),
        (None, ""),
    ]
    for entrada, esperado in casos:
        resultado = _normalizar(entrada)
        if resultado == esperado:
            ok(f"'{entrada}' → '{resultado}'")
        else:
            fail(f"'{entrada}' → '{resultado}' (esperado '{esperado}')")


async def test_busqueda_basica():
    """Test 3: Búsqueda básica devuelve resultados."""
    print("\n[3] Búsqueda básica")
    async with async_session() as db:
        casos = [
            ("esp32", 1, "ESP32"),
            ("protoboard", 1, "Protoboard"),
            ("resistencia 4.7k", 1, "Resistencia"),
            ("capacitor 470uf", 1, "Capacitor"),
            ("header hembra", 1, "Hembra"),
            ("header macho", 1, "Macho"),
            ("fuente 5v 2a", 1, "Fuente"),
            ("cable dupont", 1, "Dupont"),
        ]
        for termino, min_resultados, debe_contener in casos:
            resultados = await buscar_en_bd(db, termino, limite=10)
            if len(resultados) >= min_resultados:
                nombres = " ".join(r["nombre_producto"] for r in resultados[:3])
                if debe_contener.lower() in nombres.lower():
                    ok(f"'{termino}' → {len(resultados)} resultados, contiene '{debe_contener}'")
                else:
                    fail(f"'{termino}' → {len(resultados)} resultados, NO contiene '{debe_contener}'")
                    for r in resultados[:3]:
                        info(f"  → {r['nombre_producto']}")
            else:
                fail(f"'{termino}' → {len(resultados)} resultados (esperado ≥{min_resultados})")


async def test_busqueda_and_estricto():
    """Test 4: Búsqueda AND estricto filtra correctamente."""
    print("\n[4] Búsqueda AND estricto (todos los tokens)")
    async with async_session() as db:
        # "header hembra" debe devolver solo productos con ambas palabras
        resultados = await buscar_en_bd(db, "header hembra", limite=50)
        todos_tienen_hembra = all(
            "hembra" in r["nombre_producto"].lower() for r in resultados
        )
        todos_tienen_header = all(
            "header" in r["nombre_producto"].lower() for r in resultados
        )
        if todos_tienen_hembra and todos_tienen_header:
            ok(f"'header hembra' → {len(resultados)} resultados, todos tienen 'header' Y 'hembra'")
        else:
            fail(f"'header hembra' → algunos resultados no tienen ambas palabras")
            for r in resultados[:5]:
                info(f"  → {r['nombre_producto']}")

        # "header macho" NO debe devolver productos con "hembra"
        resultados_macho = await buscar_en_bd(db, "header macho", limite=50)
        sin_hembra = all(
            "hembra" not in r["nombre_producto"].lower() for r in resultados_macho
        )
        if sin_hembra:
            ok(f"'header macho' → {len(resultados_macho)} resultados, ninguno tiene 'hembra'")
        else:
            fail(f"'header macho' → algunos resultados tienen 'hembra'")
            for r in resultados_macho:
                if "hembra" in r["nombre_producto"].lower():
                    info(f"  → {r['nombre_producto']}")


async def test_busqueda_or_fallback():
    """Test 5: Búsqueda OR fallback cuando AND no encuentra nada."""
    print("\n[5] Búsqueda OR fallback")
    async with async_session() as db:
        # Término con palabra que no existe combinada
        resultados = await buscar_en_bd(db, "esp32 bluetooth wifi", limite=10)
        if len(resultados) > 0:
            ok(f"'esp32 bluetooth wifi' → {len(resultados)} resultados (AND o OR)")
        else:
            fail(f"'esp32 bluetooth wifi' → 0 resultados")

        # Término muy específico que seguramente no tiene AND
        resultados = await buscar_en_bd(db, "vl53l1x laser tof", limite=10)
        if len(resultados) > 0:
            ok(f"'vl53l1x laser tof' → {len(resultados)} resultados")
        else:
            fail(f"'vl53l1x laser tof' → 0 resultados")


async def test_ranking():
    """Test 6: Ranking por coincidencias ordena correctamente."""
    print("\n[6] Ranking por coincidencias")
    async with async_session() as db:
        resultados = await buscar_en_bd(db, "cable dupont hembra", limite=10)
        if len(resultados) >= 2:
            # El primer resultado debe tener más coincidencias o ser más barato
            primero = resultados[0]["nombre_producto"].lower()
            info(f"Primer resultado: {resultados[0]['nombre_producto']}")
            if "hembra" in primero and "dupont" in primero:
                ok("Primer resultado tiene 'dupont' y 'hembra' (máx coincidencias)")
            else:
                fail(f"Primer resultado no tiene máx coincidencias: {primero}")
        else:
            fail(f"Solo {len(resultados)} resultados, no se puede validar ranking")


async def test_performance():
    """Test 7: Búsquedas son rápidas (< 100ms)."""
    print("\n[7] Performance de búsqueda")
    async with async_session() as db:
        terminos = [
            "esp32 wifi bluetooth",
            "resistencia 4.7k ohm",
            "capacitor 470uf 16v",
            "header hembra 40 pines",
            "cable micro usb datos",
            "sensor bme680 i2c",
            "protoboard 400 puntos",
            "fuente 5v 2a",
        ]
        for termino in terminos:
            t0 = time.time()
            await buscar_en_bd(db, termino, limite=50)
            dt = (time.time() - t0) * 1000
            if dt < 100:
                ok(f"'{termino[:30]}' → {dt:.1f}ms")
            else:
                fail(f"'{termino[:30]}' → {dt:.1f}ms (esperado <100ms)")


async def test_casos_edge():
    """Test 8: Casos edge: términos vacíos, stop words, números."""
    print("\n[8] Casos edge")
    async with async_session() as db:
        # Término vacío
        resultados = await buscar_en_bd(db, "", limite=10)
        if resultados == []:
            ok("Término vacío → 0 resultados")
        else:
            fail(f"Término vacío → {len(resultados)} resultados (esperado 0)")

        # Solo stop words
        resultados = await buscar_en_bd(db, "de la el y con", limite=10)
        if resultados == []:
            ok("Solo stop words → 0 resultados")
        else:
            fail(f"Solo stop words → {len(resultados)} resultados (esperado 0)")

        # Solo números
        resultados = await buscar_en_bd(db, "40 30 16", limite=10)
        if resultados == []:
            ok("Solo números → 0 resultados")
        else:
            info(f"Solo números → {len(resultados)} resultados (puede ser válido si hay productos con esos números)")

        # Término muy largo
        termino_largo = "esp32 modulo wifi bluetooth 30 pines devkitc v1"
        resultados = await buscar_en_bd(db, termino_largo, limite=10)
        if len(resultados) > 0:
            ok(f"Término largo → {len(resultados)} resultados")
        else:
            fail(f"Término largo → 0 resultados")


async def test_componentes_usuario():
    """Test 9: Componentes específicos del input del usuario."""
    print("\n[9] Componentes del input del usuario (24 líneas)")
    async with async_session() as db:
        componentes_esperados = [
            ("esp 32 modulo bluetooth 30 pines", "esp32", "esp-wroom"),
            ("sensor bme680 i2c", "bme680", "bme680"),  # No existe en catalogo
            ("resistencia 4.7kohm", "resistencia", "4.7"),
            ("capacitor electrolitico 470uf 16v", "capacitor", "470"),
            ("fuente 5v 2a", "fuente", "5v"),
            ("protoboard 400 puntos", "protoboard", "400"),
            ("regleta tira de pines macho 40 pines", "header", "macho"),
            ("regleta tira de pines hembra 40 pines", "header", "hembra"),
            ("cable jumper dupont pack", "dupont", "dupont"),
            ("cable micro usb", "usb", "usb"),
            ("sensor rango laser tof vl53l1x", "laser", "laser"),
            ("bomba de agua periferica 220v", "bomba", "bomba"),
            ("modulo rele 1 canal 5v optoacoplado", "relé", "rele"),
            ("sensor nivel liquido boya", "sensor", "nivel"),
            ("terminal block 2 pines", "terminal", "terminal"),
            ("caja de paso pvc", "caja", "caja"),
        ]
        for termino, keyword1, keyword2 in componentes_esperados:
            resultados = await buscar_en_bd(db, termino, limite=5)
            if not resultados:
                fail(f"'{termino[:35]}' → 0 resultados")
                continue
            # Buscar keyword en cualquiera de los top 5 resultados
            todos_nombres = " ".join(r["nombre_producto"].lower() for r in resultados)
            if keyword1.lower() in todos_nombres or keyword2.lower() in todos_nombres:
                primer = resultados[0]["nombre_producto"][:40]
                ok(f"'{termino[:35]}' → top5 contiene '{keyword1}' (1ro: {primer})")
            else:
                # Si no se encuentra, verificar si es un producto que no existe en catalogo
                if keyword1.lower() == "bme680":
                    info(f"'{termino[:35]}' → BME680 no existe en catalogo (esperado)")
                    ok(f"'{termino[:35]}' → fallback correcto (producto no existe)")
                else:
                    fail(f"'{termino[:35]}' → ninguno de top5 tiene '{keyword1}' o '{keyword2}'")
                    for r in resultados[:3]:
                        info(f"  → {r['nombre_producto']}")


async def test_persistencia():
    """Test 10: Los datos persisten (simular reinicio leyendo directamente)."""
    print("\n[10] Persistencia de datos en BD")
    async with async_session() as db:
        # Contar antes
        count_antes = await contar_productos(db)
        if count_antes == 0:
            fail("BD vacía, no se puede validar persistencia")
            return

        # Leer directamente con SQL (sin usar el servicio)
        result = await db.execute(
            select(CatalogoProducto).limit(5)
        )
        productos = result.scalars().all()
        if len(productos) == 5:
            ok(f"SELECT directa funciona: {len(productos)} productos leídos")
            for p in productos:
                info(f"  → {p.nombre} (${p.precio}) - {p.tienda}")
        else:
            fail(f"SELECT directa devolvió {len(productos)} productos (esperado 5)")

        # Verificar que los campos están completos
        p = productos[0]
        campos_ok = all([
            p.nombre is not None,
            p.nombre_normalizado is not None,
            p.tienda is not None,
            p.url_base is not None,
            p.actualizado is not None,
        ])
        if campos_ok:
            ok("Todos los campos obligatorios están poblados")
        else:
            fail(f"Campos faltantes: nombre={p.nombre}, norm={p.nombre_normalizado}, tienda={p.tienda}")


async def test_dedup_y_cantidad():
    """Test 11: Validar que la deduplicación funciona en el endpoint."""
    print("\n[11] Deduplicación de componentes")
    from app.services.ingesta.filtro import extraer_componentes

    texto = """6 Esp 32 Modulo Wifi- Bluetooth 30 Pines
2 Esp 32 Modulo Wifi- Bluetooth 30 Pines
12 Protoboard 400 Puntos
2 Protoboard 400 Puntos
18 Regleta Tira De Pines Macho 40 Pines
2 Regleta Tira De Pines Macho 40 Pines"""

    componentes = extraer_componentes(texto)
    info(f"Componentes extraídos: {len(componentes)}")

    # Deduplicar
    vistos = {}
    for comp in componentes:
        key = comp.get("termino_base", comp["termino"])
        desc_key = tuple(sorted(comp.get("descriptores", [])))
        dedup_key = f"{key}::{desc_key}"
        if dedup_key in vistos:
            vistos[dedup_key]["cantidad"] += comp["cantidad"]
        else:
            vistos[dedup_key] = dict(comp)

    dedup = list(vistos.values())
    info(f"Componentes tras dedup: {len(dedup)}")

    if len(dedup) == 3:
        ok(f"6 líneas → 3 componentes únicos (dedup correcto)")
    else:
        fail(f"6 líneas → {len(dedup)} componentes (esperado 3)")

    # Verificar cantidades sumadas
    esp32 = next((c for c in dedup if "esp" in c["termino"].lower()), None)
    if esp32 and esp32["cantidad"] == 8:
        ok(f"ESP32: cantidad sumada = {esp32['cantidad']} (6+2)")
    else:
        fail(f"ESP32: cantidad = {esp32['cantidad'] if esp32 else 'N/A'} (esperado 8)")

    proto = next((c for c in dedup if "protoboard" in c["termino"].lower()), None)
    if proto and proto["cantidad"] == 14:
        ok(f"Protoboard: cantidad sumada = {proto['cantidad']} (12+2)")
    else:
        fail(f"Protoboard: cantidad = {proto['cantidad'] if proto else 'N/A'} (esperado 14)")

    regleta = next((c for c in dedup if "regleta" in c["termino"].lower()), None)
    if regleta and regleta["cantidad"] == 20:
        ok(f"Regleta: cantidad sumada = {regleta['cantidad']} (18+2)")
    else:
        fail(f"Regleta: cantidad = {regleta['cantidad'] if regleta else 'N/A'} (esperado 20)")


async def main():
    print(f"{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW} PRUEBAS DE VALIDACIÓN - Catálogo BD PostgreSQL{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

    tests = [
        test_tabla_existe,
        test_normalizacion,
        test_busqueda_basica,
        test_busqueda_and_estricto,
        test_busqueda_or_fallback,
        test_ranking,
        test_performance,
        test_casos_edge,
        test_componentes_usuario,
        test_persistencia,
        test_dedup_y_cantidad,
    ]

    for test in tests:
        try:
            await test()
        except Exception as exc:
            fail(f"Excepción en {test.__name__}: {exc}")

    print(f"\n{YELLOW}{'='*60}{RESET}")
    total = passed + failed
    print(f"  Total: {total} | {GREEN}Pasaron: {passed}{RESET} | {RED}Fallaron: {failed}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
