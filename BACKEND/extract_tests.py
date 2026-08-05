import httpx
import json

# Login
r = httpx.post('http://localhost:8000/api/v1/auth/login', json={'email': 'admin@cotia.com', 'password': 'Admin123!'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Extraer texto de cada imagen
for i in range(1, 6):
    path = f'/app/test/Test_{i}.jpeg'
    with open(path, 'rb') as f:
        files = {'file': (f'Test_{i}.jpeg', f, 'image/jpeg')}
        r = httpx.post('http://localhost:8000/api/v1/buscar/imagen', files=files, headers=headers, timeout=60)
    if r.status_code == 200:
        data = r.json()
        print(f'=== Test_{i} ===')
        print(f'Texto: {data.get("texto", "")}')
        print(f'Componentes: {data.get("componentes", [])}')
        print()
    else:
        print(f'=== Test_{i} ERROR {r.status_code} ===')
        print(r.text[:500])
        print()
