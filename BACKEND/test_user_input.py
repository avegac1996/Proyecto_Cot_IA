"""Debug timing per component."""
import asyncio
import time
import httpx

TEXTO = """6 Esp 32 Modulo Wifi- Bluetooth 30 Pines
6 Sensor BME680 (I2C)
6 Resistencias 4.7kohm (Pack)
6 Capacitor Electrolitico 470uF 16V
12 Fuente de Poder 5V 2A
12 Protoboard 400 Puntos
12 Placa Perforada Universal
18 Regleta Tira De Pines Macho 40 Pines
18 Regleta Tira De Pines Hembra 40 Pines
12 Cables Jumper Dupont (Pack 40 surtido)
12 Cable Micro USB Datos
4 Sensor Rango Laser ToF VL53L1X
2 Esp 32 Modulo Wifi- Bluetooth 30 Pines
2 Bomba de Agua Periferica 220V AC
2 Modulo Rele 1 Canal 5v Optoacoplado
2 Sensor Nivel De Agua Liquido Boya
2 Terminal Block 2 pines KF301
2 Protoboard 400 Puntos
2 Placa Perforada Universal
2 Regleta Tira De Pines Macho 40 Pines
2 Regleta Tira De Pines Hembra 40 Pines
2 Cables Jumper Dupont (Pack 40 M-M/M-H/H-H)
2 Cable Micro USB Datos
2 Caja de Paso PVC"""


def main():
    r = httpx.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": "admin@cotia.com", "password": "Admin123!"},
        timeout=30,
    )
    token = r.json().get("access_token", "")

    t0 = time.time()
    r = httpx.post(
        "http://localhost:8000/api/v1/buscar",
        json={"texto": TEXTO},
        headers={"Authorization": f"Bearer {token}"},
        timeout=300,
    )
    dt = time.time() - t0
    print(f"buscar: {r.status_code} en {dt:.1f}s")
    total_ops = 0
    for res in r.json().get("resultados", []):
        ops = res.get("opciones", [])
        total_ops += len(ops)
        primera = ops[0]["nombre_producto"] if ops else "NO ENCONTRADO"
        print(f"  {res['termino'][:40]:<40} x{res['cantidad']:<3} ops={len(ops)} -> {primera}")
    print(f"\nTotal: {len(r.json().get('resultados', []))} componentes, {total_ops} opciones")


main()
