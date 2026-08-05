"""Test end-to-end: busqueda con el texto real del usuario."""
import httpx

BASE_URL = 'http://localhost:8000/api/v1'

# Login
r = httpx.post(f'{BASE_URL}/auth/login', json={'email': 'admin@cotia.com', 'password': 'Admin123!'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

texto = """6 Esp 32 Modulo Wifi- Bluetooth 30 Pines
6 Sensor BME680 (I2C)
6 Resistencias 4.7kΩ (Pack)
6 Capacitor Electrolítico 470µF 16V
12 Fuente de Poder 5V 2A
12 Protoboard 400 Puntos
12 Placa Perforada Universal
18 Regleta Tira De Pines Macho 40 Pines
18 Regleta Tira De Pines Hembra 40 Pines
12 Cables Jumper Dupont (Pack 40 surtido)
12 Cable Micro USB Datos
4 Sensor Rango Laser ToF VL53L1X
2 Bomba de Agua Periférica 220V AC
2 Módulo Relé 1 Canal 5v Optoacoplado
2 Sensor Nivel De Agua Liquido Boya
2 Terminal Block 2 pines KF301
2 Cables Jumper Dupont (Pack 40 M-M/M-H/H-H)
2 Caja de Paso PVC"""

r = httpx.post(f'{BASE_URL}/buscar', json={'texto': texto}, headers=headers, timeout=600)
data = r.json()

print(f"Componentes encontrados: {len(data['resultados'])}\n")
for res in data['resultados']:
    cant = res['cantidad']
    termino = res['termino']
    encontrado = res['encontrado_propia']
    num_ops = len(res['opciones'])
    precio = res['opciones'][0]['precio_con_margen'] if res['opciones'] else 'N/A'
    nombre = res['opciones'][0]['nombre_producto'] if res['opciones'] else 'N/A'
    sugerencia = res.get('sugerencia', {}).get('sugerencia', '') if res.get('sugerencia') else ''
    sug_text = f' → sugerencia: {sugerencia}' if sugerencia else ''
    print(f"  [{cant:>2}x] {termino:<50} ops={num_ops:<3} ${precio:<8} {nombre}{sug_text}")
