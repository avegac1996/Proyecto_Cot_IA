import httpx
import json
import sys

BASE_URL = 'http://localhost:8000/api/v1'

# Textos extraídos de las imágenes
LISTAS = {
    "Test_1": "6 Esp 32 Modulo Wifi- Bluetooth 30 Pines, 6 Sensor BME680 (I2C), 6 Resistencias 4.7k ohm (Pack), 6 Capacitor Electrolitico 470uF 16V, 12 Fuente de Poder 5V 2A, 12 Protoboard 400 Puntos, 12 Placa Perforada Universal, 18 Regleta Tira De Pines Macho 40 Pines, 18 Regleta Tira De Pines Hembra 40 Pines, 12 Cables Jumper Dupont (Pack 40 surtido), 12 Cable Micro USB Datos, 4 Sensor Rango Laser ToF VL53L1X, 2 Bomba de Agua Periferica 220V AC, 2 Modulo Rele 1 Canal 5v Optoacoplado, 2 Sensor Nivel De Agua Liquido Boya, 2 Terminal Block 2 pines KF301, 2 Cables Jumper Dupont (Pack 40 M-M/M-H/H-H), 2 Caja de Paso PVC",
    "Test_2": "4 Diodo rectificador 1N5408, 4 Varistor 14D431K, 1 Baquelita Perforada 20x30cm, 8 Bornero Terminal con tornillo",
    "Test_3": "2 LED ROJOS, 2 LEDS VERDES, 2 LEDS AMARILLOS, 10 RESISTENCIAS 330 OHMS, 2 PULSADOR/BOTON 2 PINES, 1 BUZZER, 5 JUMPERS MACHO-HEMBRA, 5 JUMPERS MACHO-MACHO, 1 BROCHE PORTA PILA 9V, 1 BATERIA 9V, 1 PROTOBOARD PEQUEÑO",
    "Test_4": "8 100uF Capacitor, 8 100k ohm Resistor, 8 10k ohm Resistor, 3 620 ohm Resistor, 3 LED",
    "Test_5": "1 Modulo ESP32, 1 Pantalla TFT SPI 3.2, 1 Modulo USB a UART CP2102, 1 Zocalo ZIF 40 pines, 1 Pulsador con retencion 8x8mm, 2 Transistor S8050, 1 Capacitor tantalio 10 uF, 1 Capacitor tantalio 100 uF, 1 Capacitor 1 uF, 1 Capacitor 10 uF, 1 Capacitor 100 nF, 1 Resistencia 12 k ohm, 1 Memoria flash 25Q128 QuadSPI",
}


def login():
    r = httpx.post(f'{BASE_URL}/auth/login', json={'email': 'admin@cotia.com', 'password': 'Admin123!'})
    if r.status_code != 200:
        print(f'LOGIN ERROR: {r.status_code} {r.text}')
        sys.exit(1)
    return r.json()['access_token']


def buscar(token, texto):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.post(f'{BASE_URL}/buscar', json={'texto': texto}, headers=headers, timeout=120)
    if r.status_code != 200:
        print(f'  BUSCAR ERROR: {r.status_code} {r.text[:300]}')
        return None
    return r.json()


def crear_cotizacion(token, items, envio_nombre=None, envio_precio=None):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'items': items,
        'cliente_nombre': 'Cliente Prueba',
        'cliente_correo': 'prueba@test.com',
        'cliente_celular': '0999999999',
        'envio_nombre': envio_nombre,
        'envio_precio': envio_precio,
    }
    r = httpx.post(f'{BASE_URL}/cotizacion/desde-carrito', json=payload, headers=headers, timeout=30)
    if r.status_code != 201:
        print(f'  COTIZACION ERROR: {r.status_code} {r.text[:300]}')
        return None
    return r.json()


def get_cotizacion(token, cot_id):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.get(f'{BASE_URL}/cotizacion/by-id/{cot_id}', headers=headers)
    if r.status_code != 200:
        print(f'  GET COTIZACION ERROR: {r.status_code} {r.text[:300]}')
        return None
    return r.json()


def run_test(test_name, texto, token):
    print(f'\n{"="*60}')
    print(f'PROBANDO {test_name}')
    print(f'{"="*60}')
    print(f'Texto: {texto[:100]}...')

    # 1. Buscar componentes
    print(f'\n[1] Buscando componentes...')
    resultado = buscar(token, texto)
    if not resultado:
        print(f'  FALLO: No se pudo buscar')
        return False

    resultados = resultado.get('resultados', [])
    print(f'  Resultados: {len(resultados)} componentes encontrados')

    if len(resultados) == 0:
        print(f'  FALLO: No se encontraron resultados')
        return False

    # Mostrar detalle de cada resultado
    items_carrito = []
    for res in resultados:
        termino = res.get('termino', '?')
        cantidad = res.get('cantidad', 0)
        opciones = res.get('opciones', [])
        encontrado = res.get('encontrado_propia', False)
        print(f'  - {termino} (cant={cantidad}, opciones={len(opciones)}, propio={encontrado})')
        if opciones:
            for op in opciones[:3]:
                precio = op.get('precio_con_margen')
                tienda = op.get('tienda')
                disp = op.get('disponible')
                print(f'      -> {tienda}: ${precio} disp={disp}')
            # Seleccionar primera opción disponible
            disp_opciones = [op for op in opciones if op.get('disponible', False)]
            if disp_opciones:
                op = disp_opciones[0]
            else:
                op = opciones[0]
            items_carrito.append({
                'nombre_producto': op.get('nombre_producto', termino),
                'cantidad': cantidad,
                'tienda': op.get('tienda', ''),
                'precio_unitario': op.get('precio_con_margen', 0),
                'margen_aplicado': op.get('margen_aplicado', 0),
                'disponible': op.get('disponible', True),
                'es_propio': op.get('es_propio', False),
                'url': op.get('url'),
            })
        else:
            print(f'      -> SIN OPCIONES')
            # Agregar como no disponible
            items_carrito.append({
                'nombre_producto': termino,
                'cantidad': cantidad,
                'tienda': 'No disponible',
                'precio_unitario': 0,
                'margen_aplicado': 0,
                'disponible': False,
                'es_propio': False,
                'url': None,
            })

    # 2. Crear cotización
    print(f'\n[2] Creando cotizacion con {len(items_carrito)} items...')
    cot = crear_cotizacion(token, items_carrito, 'Recogida en tienda', 0.0)
    if not cot:
        print(f'  FALLO: No se pudo crear cotizacion')
        return False

    cot_id = cot.get('cotizacion_id')
    total = cot.get('total')
    envio_nombre = cot.get('envio_nombre')
    envio_precio = cot.get('envio_precio')
    print(f'  Cotizacion #{cot_id} creada')
    print(f'  Total: ${total}')
    print(f'  Envio: {envio_nombre} (${envio_precio})')
    print(f'  Items: {len(cot.get("items", []))}')

    # 3. Verificar cotización
    print(f'\n[3] Verificando cotizacion en historial...')
    cot_verif = get_cotizacion(token, cot_id)
    if not cot_verif:
        print(f'  FALLO: No se pudo obtener cotizacion')
        return False

    print(f'  Cotizacion #{cot_verif["cotizacion_id"]}')
    print(f'  Estado: {cot_verif["estado"]}')
    print(f'  Total: ${cot_verif["total"]}')
    print(f'  Cliente: {cot_verif.get("cliente_nombre")}')
    print(f'  Envio: {cot_verif.get("envio_nombre")} (${cot_verif.get("envio_precio")})')

    # Verificar items
    items_verif = cot_verif.get('items', [])
    print(f'  Items verificados: {len(items_verif)}')
    for item in items_verif:
        print(f'    - {item["producto_nombre"]} x{item["cantidad"]} = ${item["subtotal"]} ({item["proveedor"]})')

    # Validar que coinciden
    if len(items_verif) != len(items_carrito):
        print(f'  ADVERTENCIA: Items enviados={len(items_carrito)} vs verificados={len(items_verif)}')

    total_calculado = sum(float(i['subtotal']) for i in items_verif)
    print(f'\n  Total calculado: ${total_calculado:.2f}')
    print(f'  Total en BD: ${float(total):.2f}')
    if abs(total_calculado - float(total)) > 0.01:
        print(f'  ADVERTENCIA: Diferencia en total!')
    else:
        print(f'  OK: Totales coinciden')

    print(f'\n  RESULTADO: EXITO')
    return True


def main():
    print('INICIANDO PRUEBAS DE FUNCIONALIDAD')
    print('=' * 60)

    token = login()
    print(f'Login OK')

    resultados = {}
    for name, texto in LISTAS.items():
        ok = run_test(name, texto, token)
        resultados[name] = 'EXITO' if ok else 'FALLO'

    print(f'\n{"="*60}')
    print(f'RESUMEN DE PRUEBAS')
    print(f'{"="*60}')
    for name, res in resultados.items():
        emoji = 'OK' if res == 'EXITO' else 'FAIL'
        print(f'  {name}: {res} {emoji}')

    total_ok = sum(1 for r in resultados.values() if r == 'EXITO')
    print(f'\n  Total: {total_ok}/{len(resultados)} pruebas exitosas')


if __name__ == '__main__':
    main()
