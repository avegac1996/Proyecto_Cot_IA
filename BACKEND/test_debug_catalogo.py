"""Debug catalog search for hembra vs macho."""
import asyncio
from app.services.scraping import catalogo


async def main():
    productos = await catalogo.obtener_catalogo("https://avelectronics.cc", forzar=True)
    print(f"Catalogo: {len(productos)} productos")

    # Buscar productos con 'hembra' en el nombre
    hembra_products = [p for p in productos if "hembra" in (p["nombre_producto"] or "").lower()]
    print(f"\nProductos con 'hembra': {len(hembra_products)}")
    for p in hembra_products:
        print(f"  {p['nombre_producto']} - ${p['precio_base']}")

    # Buscar productos con 'header' en el nombre
    header_products = [p for p in productos if "header" in (p["nombre_producto"] or "").lower()]
    print(f"\nProductos con 'header': {len(header_products)}")
    for p in header_products:
        print(f"  {p['nombre_producto']} - ${p['precio_base']}")

    # Buscar en catalogo
    res_hembra = catalogo.buscar_en_catalogo(productos, "tira de pines regleta hembra 40 pines")
    print(f"\nBusqueda 'tira de pines regleta hembra 40 pines': {len(res_hembra)} resultados")
    for r in res_hembra[:5]:
        print(f"  {r['nombre_producto']}")

    res_macho = catalogo.buscar_en_catalogo(productos, "tira de pines regleta macho 40 pines")
    print(f"\nBusqueda 'tira de pines regleta macho 40 pines': {len(res_macho)} resultados")
    for r in res_macho[:5]:
        print(f"  {r['nombre_producto']}")


asyncio.run(main())
