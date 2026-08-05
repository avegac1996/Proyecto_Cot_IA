import httpx
import json
import sys

BASE_URL = 'http://localhost:8000/api/v1'

LISTAS = {
    "Test_1": "6 Esp 32 Modulo Wifi- Bluetooth 30 Pines, 6 Sensor BME680 (I2C), 6 Resistencias 4.7k ohm (Pack), 6 Capacitor Electrolitico 470uF 16V, 12 Fuente de Poder 5V 2A, 12 Protoboard 400 Puntos, 12 Placa Perforada Universal, 18 Regleta Tira De Pines Macho 40 Pines, 18 Regleta Tira De Pines Hembra 40 Pines, 12 Cables Jumper Dupont (Pack 40 surtido), 12 Cable Micro USB Datos, 4 Sensor Rango Laser ToF VL53L1X, 2 Bomba de Agua Periferica 220V AC, 2 Modulo Rele 1 Canal 5v Optoacoplado, 2 Sensor Nivel De Agua Liquido Boya, 2 Terminal Block 2 pines KF301, 2 Cables Jumper Dupont (Pack 40 M-M/M-H/H-H), 2 Caja de Paso PVC",
    "Test_2": "4 Diodo rectificador 1N5408, 4 Varistor 14D431K, 1 Baquelita Perforada 20x30cm, 8 Bornero Terminal con tornillo",
    "Test_3": "2 LED ROJOS, 2 LEDS VERDES, 2 LEDS AMARILLOS, 10 RESISTENCIAS 330 OHMS, 2 PULSADOR/BOTON 2 PINES, 1 BUZZER, 5 JUMPERS MACHO-HEMBRA, 5 JUMPERS MACHO-MACHO, 1 BROCHE PORTA PILA 9V, 1 BATERIA 9V, 1 PROTOBOARD PEQUEÑO",
    "Test_4": "8 100uF Capacitor, 8 100k ohm Resistor, 8 10k ohm Resistor, 3 620 ohm Resistor, 3 LED",
    "Test_5": "1 Modulo ESP32, 1 Pantalla TFT SPI 3.2, 1 Modulo USB a UART CP2102, 1 Zocalo ZIF 40 pines, 1 Pulsador con retencion 8x8mm, 2 Transistor S8050, 1 Capacitor tantalio 10 uF, 1 Capacitor tantalio 100 uF, 1 Capacitor 1 uF, 1 Capacitor 10 uF, 1 Capacitor 100 nF, 1 Resistencia 12 k ohm, 1 Memoria flash 25Q128 QuadSPI",
}


def login():
    r = httpx.post(f'{BASE_URL}/auth/login', json={'email': 'admin@cotia.com', 'password': 'Admin123!'})
    return r.json()['access_token']


def buscar(token, texto):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.post(f'{BASE_URL}/buscar', json={'texto': texto}, headers=headers, timeout=120)
    return r.json() if r.status_code == 200 else None


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
    return r.json() if r.status_code == 201 else None


def get_cotizacion(token, cot_id):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.get(f'{BASE_URL}/cotizacion/by-id/{cot_id}', headers=headers)
    return r.json() if r.status_code == 200 else None


def actualizar_envio(token, cot_id, envio_nombre, envio_precio):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.put(f'{BASE_URL}/cotizacion/{cot_id}/envio', json={'envio_nombre': envio_nombre, 'envio_precio': envio_precio}, headers=headers)
    return r.json() if r.status_code == 200 else None


def agregar_item(token, cot_id, texto):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.post(f'{BASE_URL}/cotizacion/{cot_id}/agregar', json={'texto': texto}, headers=headers, timeout=120)
    return r.json() if r.status_code == 200 else None


def finalizar(token, cot_id):
    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.post(f'{BASE_URL}/cotizacion/{cot_id}/finalizar', headers=headers)
    return r.json() if r.status_code == 200 else None


def run_test(test_name, texto, token):
    print(f'\n{"="*60}')
    print(f'PROBANDO {test_name}')
    print(f'{"="*60}')

    # 1. Buscar
    print(f'[1] Buscando...')
    resultado = buscar(token, texto)
    if not resultado:
        print(f'  FALLO: Busqueda')
        return False

    resultados = resultado.get('resultados', [])
    print(f'  {len(resultados)} componentes encontrados')

    items_carrito = []
    for res in resultados:
        cantidad = res.get('cantidad', 0)
        opciones = res.get('opciones', [])
        if opciones:
            disp = [op for op in opciones if op.get('disponible', False)]
            op = disp[0] if disp else opciones[0]
            items_carrito.append({
                'nombre_producto': op.get('nombre_producto', res.get('termino', '')),
                'cantidad': cantidad,
                'tienda': op.get('tienda', ''),
                'precio_unitario': op.get('precio_con_margen', 0),
                'margen_aplicado': op.get('margen_aplicado', 0),
                'disponible': op.get('disponible', True),
                'es_propio': op.get('es_propio', False),
                'url': op.get('url'),
            })
        else:
            items_carrito.append({
                'nombre_producto': res.get('termino', ''),
                'cantidad': cantidad,
                'tienda': 'No disponible',
                'precio_unitario': 0,
                'margen_aplicado': 0,
                'disponible': False,
                'es_propio': False,
                'url': None,
            })

    # 2. Crear cotizacion con envio pagado
    print(f'[2] Creando cotizacion con envio Servientrega $6.00...')
    cot = crear_cotizacion(token, items_carrito, 'Servientrega - Provincias', 6.0)
    if not cot:
        print(f'  FALLO: Crear cotizacion')
        return False

    cot_id = cot['cotizacion_id']
    subtotal = float(cot['total'])
    envio_precio = float(cot.get('envio_precio', 0))
    total_con_envio = subtotal + envio_precio
    print(f'  Cotizacion #{cot_id} | Subtotal=${subtotal:.2f} | Envio=${envio_precio:.2f} | Total+Envio=${total_con_envio:.2f}')

    # 3. Verificar
    print(f'[3] Verificando...')
    cot_v = get_cotizacion(token, cot_id)
    if not cot_v:
        print(f'  FALLO: Verificar')
        return False

    subtotal_v = float(cot_v['total'])
    envio_v = float(cot_v.get('envio_precio', 0) or 0)
    print(f'  Subtotal=${subtotal_v:.2f} | Envio={cot_v.get("envio_nombre")} ${envio_v:.2f}')

    if abs(subtotal_v - subtotal) > 0.01:
        print(f'  FALLO: Subtotal no coincide ({subtotal_v} vs {subtotal})')
        return False
    if abs(envio_v - 6.0) > 0.01:
        print(f'  FALLO: Envio no coincide ({envio_v} vs 6.0)')
        return False
    if cot_v.get('envio_nombre') != 'Servientrega - Provincias':
        print(f'  FALLO: Nombre envio no coincide')
        return False
    print(f'  OK: Datos coinciden')

    # 4. Cambiar envio
    print(f'[4] Cambiando envio a Recogida en tienda $0...')
    cot_upd = actualizar_envio(token, cot_id, 'Recogida en tienda', 0.0)
    if not cot_upd:
        print(f'  FALLO: Actualizar envio')
        return False
    if cot_upd.get('envio_nombre') != 'Recogida en tienda' or float(cot_upd.get('envio_precio', 0)) != 0:
        print(f'  FALLO: Envio no se actualizo correctamente')
        return False
    print(f'  OK: Envio actualizado')

    # 5. Agregar item adicional
    print(f'[5] Agregando item "5 LED rojo"...')
    cot_add = agregar_item(token, cot_id, '5 LED rojo')
    if not cot_add:
        print(f'  FALLO: Agregar item')
        return False
    print(f'  OK: Items ahora={len(cot_add.get("items", []))}')

    # 6. Finalizar
    print(f'[6] Finalizando cotizacion...')
    cot_fin = finalizar(token, cot_id)
    if not cot_fin:
        print(f'  FALLO: Finalizar')
        return False
    if cot_fin.get('estado') != 'finalizada':
        print(f'  FALLO: Estado={cot_fin.get("estado")}')
        return False
    print(f'  OK: Estado={cot_fin["estado"]}')

    # 7. Intentar modificar finalizada (debe fallar)
    print(f'[7] Intentando cambiar envio en cotizacion finalizada (debe dar error)...')
    cot_err = actualizar_envio(token, cot_id, 'Servientrega', 6.0)
    if cot_err is not None:
        print(f'  FALLO: Se permitio modificar cotizacion finalizada')
        return False
    print(f'  OK: Bloqueado correctamente')

    print(f'\n  RESULTADO: EXITO')
    return True


def main():
    print('PRUEBAS EXHAUSTIVAS - feature/pruebas')
    print('=' * 60)

    token = login()
    print(f'Login OK')

    resultados = {}
    for name, texto in LISTAS.items():
        ok = run_test(name, texto, token)
        resultados[name] = 'EXITO' if ok else 'FALLO'

    print(f'\n{"="*60}')
    print(f'RESUMEN FINAL')
    print(f'{"="*60}')
    for name, res in resultados.items():
        print(f'  {name}: {res}')
    total_ok = sum(1 for r in resultados.values() if r == 'EXITO')
    print(f'\n  Total: {total_ok}/{len(resultados)} pruebas exitosas')
    if total_ok == len(resultados):
        print(f'  TODAS LAS PRUEBAS PASARON - 100% FUNCIONAL')


if __name__ == '__main__':
    main()
