import httpx

BASE_URL = 'http://localhost:8000/api/v1'

# Login
r = httpx.post(f'{BASE_URL}/auth/login', json={'email': 'admin@cotia.com', 'password': 'Admin123!'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Buscar una cotizacion pendiente
r = httpx.get(f'{BASE_URL}/cotizaciones', params={'page': 1, 'limit': 10}, headers=headers)
cotizaciones = r.json()['cotizaciones']
cot_pendiente = None
for c in cotizaciones:
    if c['estado'] == 'pendiente':
        cot_pendiente = c
        break

if not cot_pendiente:
    print('No hay cotizaciones pendientes, creando una...')
    # Crear una cotizacion rapida
    r = httpx.post(f'{BASE_URL}/buscar', json={'texto': '2 led rojo'}, headers=headers, timeout=60)
    resultados = r.json()['resultados']
    items = []
    for res in resultados:
        opciones = res.get('opciones', [])
        if opciones:
            op = opciones[0]
            items.append({
                'nombre_producto': op.get('nombre_producto', res['termino']),
                'cantidad': res['cantidad'],
                'tienda': op.get('tienda', ''),
                'precio_unitario': op.get('precio_con_margen', 0),
                'margen_aplicado': op.get('margen_aplicado', 0),
                'disponible': op.get('disponible', True),
                'es_propio': op.get('es_propio', False),
                'url': op.get('url'),
            })
    r = httpx.post(f'{BASE_URL}/cotizacion/desde-carrito', json={
        'items': items,
        'cliente_nombre': 'Cliente Original',
        'cliente_correo': 'original@test.com',
        'cliente_celular': '0991111111',
        'envio_nombre': 'Recogida local',
        'envio_precio': 0,
    }, headers=headers)
    cot_pendiente = r.json()
    print(f'Cotizacion creada: #{cot_pendiente["cotizacion_id"]}')

cot_id = cot_pendiente['cotizacion_id']
print(f'\nUsando cotizacion #{cot_id}')

# Obtener detalle
r = httpx.get(f'{BASE_URL}/cotizacion/by-id/{cot_id}', headers=headers)
detalle = r.json()
print(f'Cliente antes: {detalle["cliente_nombre"]} | {detalle["cliente_correo"]} | {detalle["cliente_celular"]}')

# Actualizar cliente
r = httpx.put(f'{BASE_URL}/cotizacion/{cot_id}/cliente', json={
    'cliente_nombre': 'Cliente Modificado',
    'cliente_correo': 'modificado@test.com',
    'cliente_celular': '0987654321',
}, headers=headers)
print(f'PUT status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Cliente despues: {data["cliente_nombre"]} | {data["cliente_correo"]} | {data["cliente_celular"]}')
    
    # Verificar
    r2 = httpx.get(f'{BASE_URL}/cotizacion/by-id/{cot_id}', headers=headers)
    verif = r2.json()
    if verif['cliente_nombre'] == 'Cliente Modificado':
        print('OK: Datos del cliente actualizados correctamente')
    else:
        print(f'ERROR: No se actualizo. Nombre={verif["cliente_nombre"]}')
else:
    print(f'ERROR: {r.text[:300]}')
