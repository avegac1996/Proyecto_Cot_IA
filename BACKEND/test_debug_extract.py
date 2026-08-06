from app.services.ingesta.filtro import extraer_componentes

texto = """6 Esp 32 Modulo Wifi- Bluetooth 30 Pines
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
2 Bomba de Agua Periferica 220V AC
2 Modulo Rele 1 Canal 5v Optoacoplado
2 Sensor Nivel De Agua Liquido Boya
2 Terminal Block 2 pines KF301
2 Cables Jumper Dupont (Pack 40 M-M/M-H/H-H)
2 Cable Micro USB Datos
2 Caja de Paso PVC"""

comps = extraer_componentes(texto)
for c in comps:
    print(f"termino={c['termino'][:45]:<45} base={c.get('termino_base','')[:25]:<25} tipo={c.get('tipo',''):<12} desc={c.get('descriptores',[])}")
