"""Test del cache de catalogo WooCommerce."""
import asyncio
import time

from app.services.scraping import catalogo


async def main():
    t0 = time.time()
    prods = await catalogo.obtener_catalogo("https://avelectronics.cc", forzar=True)
    print(f"Descarga catalogo: {time.time() - t0:.1f}s, {len(prods)} productos")
    caps470 = [p for p in prods if "470" in p["nombre_producto"] and "apacitor" in p["nombre_producto"]]
    print("Capacitores 470:", [p["nombre_producto"] for p in caps470])

    t0 = time.time()
    prods = await catalogo.obtener_catalogo("https://avelectronics.cc")
    print(f"Segunda llamada (cache): {time.time() - t0:.3f}s")

    terminos = [
        "resistencia 4.7kohm pack",
        "capacitor electrolitico 470uf 16v",
        "esp 32 modulo bluetooth 30 pines",
        "caja de paso pvc",
        "sensor bme680 i2c",
        "tira de pines regleta hembra 40 pines",
    ]
    for term in terminos:
        t0 = time.time()
        res = catalogo.buscar_en_catalogo(prods, term)
        print(f"\n{term!r}: {len(res)} resultados en {time.time() - t0:.3f}s")
        for r in res[:3]:
            print(f"   {r['nombre_producto']} - ${r['precio']} - disp={r['disponible']}")


asyncio.run(main())
