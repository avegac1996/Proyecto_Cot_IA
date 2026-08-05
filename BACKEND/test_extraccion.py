"""Test de extraccion con el texto exacto del usuario."""
import sys
sys.path.insert(0, '/app')

from app.services.ingesta.filtro import extraer_componentes

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

resultados = extraer_componentes(texto)
print(f"Total componentes: {len(resultados)}\n")
for r in resultados:
    print(f"  [{r['cantidad']:>2}x] {r['termino']:<40} tipo={r['tipo']:<15} descriptores={r['descriptores']}")
