"""Test end-to-end via API HTTP (proceso real del servidor, con cache)."""
import time

import httpx

TEXTO = """6 ESP32 dev module (Bluetooth, 30 pines)
6 Sensor BME680 (I2C)
6 Resistencias 4.7kohm (Pack)
6 Capacitor Electrolitico 470uF 16V
12 Fuente de Poder 5V 2A
18 Tira de pines (regleta) macho 40 pines
18 Tira de pines (regleta) hembra 40 pines
2 Terminal block 2 pines
1 Caja de paso PVC"""


def main():
    r = httpx.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": "admin@cotia.com", "password": "Admin123!"},
        timeout=30,
    )
    print("login:", r.status_code)
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
    if r.status_code != 200:
        print(r.text[:500])
        return
    for res in r.json().get("resultados", []):
        ops = res.get("opciones", [])
        primera = ops[0]["nombre_producto"] if ops else "NO ENCONTRADO"
        print(f"  {res['termino'][:40]:<40} ops={len(ops)} -> {primera}")


main()
