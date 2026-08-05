"""
Pruebas de funcionalidad a nivel de Frontend.
Simula exactamente lo que hacen los componentes React:
1. Login (LoginPage)
2. Buscar componentes (CargaPage -> buscarComponentes)
3. Agregar al carrito (CargaPage -> handleAgregarCarrito)
4. Crear cotización con cliente y envío (CargaPage -> crearCotizacionDesdeCarrito)
5. Ver cotización (CotizacionPage -> getCotizacion)
6. Ver historial (HistorialPage -> getHistorial)
7. Ver detalle (HistorialPage -> getCotizacionById)
8. Cambiar envío (HistorialPage -> actualizarEnvio)
9. Configuración: obtener opciones de envío (EnvioModal -> getOpcionesEnvio)
10. Configuración: obtener IVA (CotizacionPage -> getConfiguracion)
"""
import httpx
import json
import sys

BASE_URL = 'http://localhost:8000/api/v1'

# Textos de prueba extraídos de las imágenes
TEXTOS = {
    "Test_1": "6 Esp 32 Modulo Wifi- Bluetooth 30 Pines, 6 Sensor BME680 (I2C), 6 Resistencias 4.7k ohm (Pack), 6 Capacitor Electrolitico 470uF 16V, 12 Fuente de Poder 5V 2A, 12 Protoboard 400 Puntos, 12 Placa Perforada Universal, 18 Regleta Tira De Pines Macho 40 Pines, 18 Regleta Tira De Pines Hembra 40 Pines, 12 Cables Jumper Dupont (Pack 40 surtido), 12 Cable Micro USB Datos, 4 Sensor Rango Laser ToF VL53L1X, 2 Bomba de Agua Periferica 220V AC, 2 Modulo Rele 1 Canal 5v Optoacoplado, 2 Sensor Nivel De Agua Liquido Boya, 2 Terminal Block 2 pines KF301, 2 Cables Jumper Dupont (Pack 40 M-M/M-H/H-H), 2 Caja de Paso PVC",
    "Test_2": "4 Diodo rectificador 1N5408, 4 Varistor 14D431K, 1 Baquelita Perforada 20x30cm, 8 Bornero Terminal con tornillo",
    "Test_3": "2 LED ROJOS, 2 LEDS VERDES, 2 LEDS AMARILLOS, 10 RESISTENCIAS 330 OHMS, 2 PULSADOR/BOTON 2 PINES, 1 BUZZER, 5 JUMPERS MACHO-HEMBRA, 5 JUMPERS MACHO-MACHO, 1 BROCHE PORTA PILA 9V, 1 BATERIA 9V, 1 PROTOBOARD PEQUEÑO",
    "Test_4": "8 100uF Capacitor, 8 100k ohm Resistor, 8 10k ohm Resistor, 3 620 ohm Resistor, 3 LED",
    "Test_5": "1 Modulo ESP32, 1 Pantalla TFT SPI 3.2, 1 Modulo USB a UART CP2102, 1 Zocalo ZIF 40 pines, 1 Pulsador con retencion 8x8mm, 2 Transistor S8050, 1 Capacitor tantalio 10 uF, 1 Capacitor tantalio 100 uF, 1 Capacitor 1 uF, 1 Capacitor 10 uF, 1 Capacitor 100 nF, 1 Resistencia 12 k ohm, 1 Memoria flash 25Q128 QuadSPI",
}


class FrontendSimulator:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=120)
        self.token = None
        self.user = None

    def login(self, email, password):
        """Simula LoginPage -> login()"""
        r = self.client.post('/auth/login', json={'email': email, 'password': password})
        if r.status_code != 200:
            raise Exception(f'Login falló: {r.status_code} {r.text}')
        data = r.json()
        self.token = data['access_token']
        self.user = data
        self.client.headers['Authorization'] = f'Bearer {self.token}'
        return data

    def get_configuracion(self):
        """Simula CotizacionPage -> getConfiguracion()"""
        r = self.client.get('/configuracion')
        if r.status_code != 200:
            raise Exception(f'getConfiguracion falló: {r.status_code}')
        return r.json()

    def get_opciones_envio(self):
        """Simula EnvioModal -> getOpcionesEnvio()"""
        r = self.client.get('/configuracion/envio')
        if r.status_code != 200:
            raise Exception(f'getOpcionesEnvio falló: {r.status_code}')
        return r.json()

    def buscar_componentes(self, texto):
        """Simula CargaPage -> buscarComponentes()"""
        r = self.client.post('/buscar', json={'texto': texto})
        if r.status_code != 200:
            raise Exception(f'buscarComponentes falló: {r.status_code} {r.text[:300]}')
        return r.json()

    def crear_cotizacion_desde_carrito(self, items, cliente, envio):
        """Simula CargaPage -> crearCotizacionDesdeCarrito()"""
        payload = {
            'items': items.map(lambda item: {
                'nombre_producto': item['opcion_seleccionada']['nombre_producto'],
                'cantidad': item['cantidad'],
                'tienda': item['opcion_seleccionada']['tienda'],
                'precio_unitario': item['opcion_seleccionada']['precio_con_margen'] or 0,
                'margen_aplicado': item['opcion_seleccionada']['margen_aplicado'],
                'disponible': item['opcion_seleccionada']['disponible'],
                'es_propio': item['opcion_seleccionada']['es_propio'],
                'url': item['opcion_seleccionada']['url'],
            }) if hasattr(items, 'map') else [{
                'nombre_producto': item['opcion_seleccionada']['nombre_producto'],
                'cantidad': item['cantidad'],
                'tienda': item['opcion_seleccionada']['tienda'],
                'precio_unitario': item['opcion_seleccionada']['precio_con_margen'] or 0,
                'margen_aplicado': item['opcion_seleccionada']['margen_aplicado'],
                'disponible': item['opcion_seleccionada']['disponible'],
                'es_propio': item['opcion_seleccionada']['es_propio'],
                'url': item['opcion_seleccionada']['url'],
            } for item in items],
            'cotizacion_id': None,
            'cliente_nombre': cliente['nombre'] if cliente else None,
            'cliente_correo': cliente['correo'] if cliente else None,
            'cliente_celular': cliente['celular'] if cliente else None,
            'envio_nombre': envio['nombre'] if envio else None,
            'envio_precio': envio['precio'] if envio else None,
        }
        r = self.client.post('/cotizacion/desde-carrito', json=payload)
        if r.status_code != 201:
            raise Exception(f'crearCotizacion falló: {r.status_code} {r.text[:300]}')
        return r.json()

    def get_cotizacion(self, cot_id):
        """Simula CotizacionPage/HistorialPage -> getCotizacion()/getCotizacionById()"""
        r = self.client.get(f'/cotizacion/by-id/{cot_id}')
        if r.status_code != 200:
            raise Exception(f'getCotizacion falló: {r.status_code}')
        return r.json()

    def get_historial(self, page=1, limit=10):
        """Simula HistorialPage -> getHistorial()"""
        r = self.client.get('/cotizaciones', params={'page': page, 'limit': limit})
        if r.status_code != 200:
            raise Exception(f'getHistorial falló: {r.status_code}')
        return r.json()

    def actualizar_envio(self, cot_id, envio):
        """Simula HistorialPage -> actualizarEnvio()"""
        payload = {
            'envio_nombre': envio['nombre'] if envio else None,
            'envio_precio': envio['precio'] if envio else None,
        }
        r = self.client.put(f'/cotizacion/{cot_id}/envio', json=payload)
        if r.status_code != 200:
            return None
        return r.json()

    def descargar_pdf(self, cot_id):
        """Simula descargarPDF()"""
        r = self.client.get(f'/cotizacion/{cot_id}/pdf')
        return r.status_code == 200 and r.headers.get('content-type', '').startswith('application/pdf')


def run_frontend_test(test_name, texto, sim):
    print(f'\n{"="*60}')
    print(f'FRONTEND TEST: {test_name}')
    print(f'{"="*60}')

    errors = []

    # 1. Obtener configuración (IVA)
    print('[1] Obteniendo configuración (IVA)...')
    try:
        config = sim.get_configuracion()
        iva = config.get('iva', 0)
        print(f'  IVA: {iva}%')
    except Exception as e:
        errors.append(f'getConfiguracion: {e}')
        iva = 0
        print(f'  ERROR: {e}')

    # 2. Obtener opciones de envío
    print('[2] Obteniendo opciones de envío...')
    try:
        opciones_envio = sim.get_opciones_envio()
        print(f'  {len(opciones_envio)} opciones:')
        for op in opciones_envio:
            print(f'    - {op["nombre"]}: ${op["precio"]}')
    except Exception as e:
        errors.append(f'getOpcionesEnvio: {e}')
        opciones_envio = []
        print(f'  ERROR: {e}')

    # 3. Buscar componentes
    print(f'[3] Buscando componentes...')
    try:
        resultado = sim.buscar_componentes(texto)
        resultados = resultado.get('resultados', [])
        print(f'  {len(resultados)} resultados')
    except Exception as e:
        errors.append(f'buscarComponentes: {e}')
        print(f'  ERROR: {e}')
        return errors

    # 4. Construir carrito (como lo hace CargaPage)
    print(f'[4] Construyendo carrito...')
    carrito = []
    for res in resultados:
        opciones = res.get('opciones', [])
        cantidad = res.get('cantidad', 0)
        if opciones:
            disp = [op for op in opciones if op.get('disponible', False)]
            op = disp[0] if disp else opciones[0]
            carrito.append({
                'termino': res.get('termino', ''),
                'cantidad': cantidad,
                'opcion_seleccionada': {
                    'tienda': op.get('tienda', ''),
                    'nombre_producto': op.get('nombre_producto', res.get('termino', '')),
                    'precio_base': op.get('precio_base', 0),
                    'precio_con_margen': op.get('precio_con_margen', 0),
                    'margen_aplicado': op.get('margen_aplicado', 0),
                    'disponible': op.get('disponible', True),
                    'url': op.get('url'),
                    'es_propio': op.get('es_propio', False),
                },
            })
        else:
            carrito.append({
                'termino': res.get('termino', ''),
                'cantidad': cantidad,
                'opcion_seleccionada': {
                    'tienda': 'No disponible',
                    'nombre_producto': res.get('termino', ''),
                    'precio_base': 0,
                    'precio_con_margen': 0,
                    'margen_aplicado': 0,
                    'disponible': False,
                    'url': None,
                    'es_propio': False,
                },
            })
    print(f'  Carrito: {len(carrito)} items')

    # Calcular total del carrito (como CarritoPreview)
    total_carrito = sum(item['opcion_seleccionada']['precio_con_margen'] * item['cantidad'] for item in carrito)
    print(f'  Total carrito (CarritoPreview): ${total_carrito:.2f}')

    # 5. Seleccionar envío (como EnvioModal)
    envio_seleccionado = opciones_envio[1] if len(opciones_envio) > 1 else (opciones_envio[0] if opciones_envio else None)
    if envio_seleccionado:
        print(f'[5] Envío seleccionado: {envio_seleccionado["nombre"]} ${envio_seleccionado["precio"]}')
    else:
        print(f'[5] No hay opciones de envío')
        envio_seleccionado = {'nombre': 'Recogida', 'precio': 0}

    # 6. Crear cotización (como handleFinalizar)
    cliente = {'nombre': 'Cliente Frontend', 'correo': 'frontend@test.com', 'celular': '0987654321'}
    print(f'[6] Creando cotización con cliente y envío...')
    try:
        cot = sim.crear_cotizacion_desde_carrito(carrito, cliente, envio_seleccionado)
        cot_id = cot['cotizacion_id']
        print(f'  Cotización #{cot_id}')
        print(f'  Total BD: ${cot["total"]}')
        print(f'  Envío: {cot.get("envio_nombre")} ${cot.get("envio_precio")}')
        print(f'  Cliente: {cot.get("cliente_nombre")}')
        print(f'  Items: {len(cot.get("items", []))}')
    except Exception as e:
        errors.append(f'crearCotizacion: {e}')
        print(f'  ERROR: {e}')
        return errors

    # 7. Verificar totales
    subtotal_bd = float(cot['total'])
    envio_bd = float(cot.get('envio_precio', 0) or 0)
    total_esperado = subtotal_bd + envio_bd
    if iva > 0:
        iva_amount = total_esperado * iva / 100
        total_con_iva = total_esperado + iva_amount
    else:
        total_con_iva = total_esperado

    print(f'[7] Verificando totales:')
    print(f'  Subtotal: ${subtotal_bd:.2f}')
    print(f'  Envío: ${envio_bd:.2f}')
    if iva > 0:
        print(f'  IVA ({iva}%): ${iva_amount:.2f}')
    print(f'  Total esperado (con IVA): ${total_con_iva:.2f}')

    # Comparar total carrito vs subtotal BD
    if abs(total_carrito - subtotal_bd) > 0.01:
        errors.append(f'Total carrito (${total_carrito:.2f}) != subtotal BD (${subtotal_bd:.2f})')
        print(f'  ADVERTENCIA: Total carrito != subtotal BD')
    else:
        print(f'  OK: Total carrito == subtotal BD')

    # 8. Verificar en historial
    print(f'[8] Verificando en historial...')
    try:
        historial = sim.get_historial()
        encontrada = any(c['cotizacion_id'] == cot_id for c in historial['cotizaciones'])
        if encontrada:
            print(f'  OK: Cotización #{cot_id} encontrada en historial')
        else:
            errors.append(f'Cotización #{cot_id} no encontrada en historial')
            print(f'  ADVERTENCIA: No encontrada en historial')
    except Exception as e:
        errors.append(f'getHistorial: {e}')
        print(f'  ERROR: {e}')

    # 9. Ver detalle (como HistorialPage handleVer)
    print(f'[9] Obteniendo detalle...')
    try:
        detalle = sim.get_cotizacion(cot_id)
        items_det = detalle.get('items', [])
        print(f'  Items: {len(items_det)}')
        for item in items_det:
            print(f'    - {item["producto_nombre"]} x{item["cantidad"]} = ${item["subtotal"]}')
        print(f'  Subtotal: ${detalle["total"]}')
        print(f'  Envío: {detalle.get("envio_nombre")} ${detalle.get("envio_precio")}')

        # Verificar que coincide con lo creado
        if len(items_det) != len(carrito):
            errors.append(f'Items detalle ({len(items_det)}) != carrito ({len(carrito)})')
        if abs(float(detalle['total']) - subtotal_bd) > 0.01:
            errors.append(f'Total detalle ({detalle["total"]}) != creado ({subtotal_bd})')
        if detalle.get('envio_nombre') != envio_seleccionado['nombre']:
            errors.append(f'Envío detalle ({detalle.get("envio_nombre")}) != seleccionado ({envio_seleccionado["nombre"]})')
        if abs(float(detalle.get('envio_precio', 0) or 0) - envio_seleccionado['precio']) > 0.01:
            errors.append(f'Precio envío detalle ({detalle.get("envio_precio")}) != seleccionado ({envio_seleccionado["precio"]})')
    except Exception as e:
        errors.append(f'getDetalle: {e}')
        print(f'  ERROR: {e}')

    # 10. Cambiar envío (como HistorialPage handleCambiarEnvio)
    nuevo_envio = opciones_envio[0] if opciones_envio else {'nombre': 'Recogida', 'precio': 0}
    print(f'[10] Cambiando envío a: {nuevo_envio["nombre"]} ${nuevo_envio["precio"]}')
    try:
        cot_upd = sim.actualizar_envio(cot_id, nuevo_envio)
        if cot_upd:
            print(f'  OK: Envío actualizado a {cot_upd.get("envio_nombre")} ${cot_upd.get("envio_precio")}')
            if cot_upd.get('envio_nombre') != nuevo_envio['nombre']:
                errors.append('Envío actualizado no coincide')
        else:
            errors.append('actualizarEnvio retornó None')
            print(f'  ERROR: No se pudo actualizar')
    except Exception as e:
        errors.append(f'actualizarEnvio: {e}')
        print(f'  ERROR: {e}')

    # 11. Descargar PDF
    print(f'[11] Descargando PDF...')
    try:
        pdf_ok = sim.descargar_pdf(cot_id)
        if pdf_ok:
            print(f'  OK: PDF generado correctamente')
        else:
            errors.append('PDF no se generó correctamente')
            print(f'  ADVERTENCIA: PDF falló')
    except Exception as e:
        errors.append(f'descargarPDF: {e}')
        print(f'  ERROR: {e}')

    # Resultado
    if errors:
        print(f'\n  RESULTADO: FALLO ({len(errors)} errores)')
        for e in errors:
            print(f'    - {e}')
    else:
        print(f'\n  RESULTADO: EXITO')

    return errors


def main():
    print('PRUEBAS FRONTEND - Simulando componentes React')
    print('=' * 60)

    sim = FrontendSimulator()

    # Login
    print('Haciendo login...')
    try:
        user = sim.login('admin@cotia.com', 'Admin123!')
        print(f'Login OK: {user["username"]} ({user["rol"]})')
    except Exception as e:
        print(f'LOGIN FALLO: {e}')
        sys.exit(1)

    all_errors = {}
    for name, texto in TEXTOS.items():
        errors = run_frontend_test(name, texto, sim)
        if errors:
            all_errors[name] = errors

    print(f'\n{"="*60}')
    print(f'RESUMEN FRONTEND')
    print(f'{"="*60}')
    for name in TEXTOS:
        status = 'EXITO' if name not in all_errors else f'FALLO ({len(all_errors[name])} errores)'
        print(f'  {name}: {status}')

    total_ok = sum(1 for n in TEXTOS if n not in all_errors)
    print(f'\n  Total: {total_ok}/{len(TEXTOS)} pruebas exitosas')
    if total_ok == len(TEXTOS):
        print(f'  FRONTEND 100% FUNCIONAL')
    else:
        print(f'  HAY ERRORES - Revisar detalle arriba')


if __name__ == '__main__':
    main()
