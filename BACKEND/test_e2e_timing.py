"""Test end-to-end con medición de tiempo total."""
import asyncio
import time

import httpx

from app.core.database import async_session
from app.services.ingesta.filtro import extraer_componentes
from app.services.scraping.busqueda import buscar_por_termino_priorizado

TEXTO = """Hola necesito para un proyecto de IoT con bomba de agua:
6 ESP32 dev module (Bluetooth, 30 pines)
6 Sensor BME680 (I2C)
6 Resistencias 4.7kΩ (Pack)
6 Capacitor Electrolítico 470µF 16V
12 Fuente de Poder 5V 2A
18 Tira de pines (regleta) macho 40 pines
18 Tira de pines (regleta) hembra 40 pines
2 Terminal block 2 pines
1 Caja de paso PVC"""


async def main():
    componentes = extraer_componentes(TEXTO)
    async with async_session() as db:
        t_total = time.time()
        for comp in componentes:
            t0 = time.time()
            r = await buscar_por_termino_priorizado(
                db, comp["termino"], comp["cantidad"],
                termino_base=comp.get("termino_base"),
                descriptores=comp.get("descriptores", []),
                tipo=comp.get("tipo"),
            )
            dt = time.time() - t0
            ops = r.get("opciones", [])
            primera = ops[0]["nombre_producto"] if ops else "N/A"
            print(f"[{dt:5.1f}s] {comp['termino'][:45]:<45} ops={len(ops)} → {primera}")
        print(f"\nTOTAL: {time.time() - t_total:.1f}s para {len(componentes)} componentes")


asyncio.run(main())
