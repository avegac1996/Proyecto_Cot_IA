"""Debug full search pipeline for hembra vs macho."""
import asyncio
from app.services.scraping import catalogo
from app.services.scraping.busqueda import (
    _filtrar_y_ordenar_por_relevancia,
    _normalizar_texto,
    _match_tipo,
    _score_relevancia,
)


async def main():
    productos = await catalogo.obtener_catalogo("https://avelectronics.cc", forzar=True)
    print(f"Catalogo: {len(productos)} productos")

    for termino, termino_base, descriptores, tipo in [
        ("tira de pines regleta hembra 40 pines", "tira de pines", ["hembra", "40 pines"], "regleta"),
        ("tira de pines regleta macho 40 pines", "tira de pines", ["macho", "40 pines"], "regleta"),
    ]:
        print(f"\n=== {termino} ===")
        print(f"  termino_base={termino_base}, descriptores={descriptores}, tipo={tipo}")

        # Catalog search
        res = catalogo.buscar_en_catalogo(productos, termino)
        print(f"  Catalog search: {len(res)} results")

        # Simulate engine mapping
        opciones = []
        for item in res:
            opciones.append({
                "tienda": "AV Electronics",
                "nombre_producto": item.get("nombre_producto") or termino,
                "precio_base": float(item["precio"]) if item["precio"] is not None else None,
                "disponible": item["disponible"],
                "url": item["url"],
                "variantes": item.get("variantes", []),
            })

        # Filter
        filtradas = _filtrar_y_ordenar_por_relevancia(opciones, descriptores, termino_base, tipo)
        print(f"  After filter: {len(filtradas)} results")
        for op in filtradas[:5]:
            print(f"    {op['nombre_producto']} - ${op['precio_base']}")

        # Debug: show scoring for header products
        print(f"\n  Scoring debug for header products:")
        for op in opciones:
            nombre = op.get("nombre_producto", "")
            if "header" not in nombre.lower():
                continue
            nombre_norm = _normalizar_texto(nombre)
            score = _score_relevancia(nombre, descriptores)
            es_tipo = _match_tipo(nombre_norm, tipo, termino_base)
            # termino_base bonus
            base_norm = _normalizar_texto(termino_base)
            base_sin = base_norm.replace(" ", "")
            nombre_sin = nombre_norm.replace(" ", "")
            bonus = 0
            if _palabra_en_texto(base_norm, nombre_norm) or base_sin in nombre_sin:
                bonus = 20
            print(f"    {nombre:<40} score={score} bonus={bonus} es_tipo={es_tipo} total={score+bonus}")


asyncio.run(main())
