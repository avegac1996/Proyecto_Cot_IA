"""Test de extraccion + scoring sin scraping."""
import sys
sys.path.insert(0, '/app')

from app.services.ingesta.filtro import extraer_componentes
from app.services.scraping.busqueda import _score_relevancia, _extraer_valores, _filtrar_y_ordenar_por_relevancia

print("=== 1. Extraccion de valores clave ===")
texto = """6 Resistencias 4.7kΩ (Pack)
6 Capacitor Electrolítico 470µF 16V
12 Fuente de Poder 5V 2A"""
for r in extraer_componentes(texto):
    print(f"  [{r['cantidad']}x] {r['termino']}  desc={r['descriptores']}")

print("\n=== 2. Matching numerico de valores ===")
casos = [
    ("4.7kω", "RPACK Arreglo de Resistencias - 4.7 KΩ"),
    ("4.7kω", "RPACK Arreglo de Resistencias - 220 Ω"),
    ("470µf", "Capacitor Electrolítico 25V - 470 uF"),
    ("470µf", "Capacitor Electrolítico 25V - 100 uF"),
    ("5v", "Fuente 5V 2A"),
    ("5v", "Fuente 9V 2A"),
    ("2a", "Fuente 5V 2A"),
    ("2a", "Fuente 5V 3A USB Tipo C"),
]
for desc, producto in casos:
    vals_d = _extraer_valores(desc)
    vals_p = _extraer_valores(producto.lower().replace("ω", "ohm").replace("Ω", "ohm"))
    match = bool(vals_d & vals_p)
    print(f"  '{desc}' vs '{producto}': {'MATCH' if match else 'no'} {vals_d} & {vals_p}")

print("\n=== 3. Score relevancia ===")
score1 = _score_relevancia("RPACK Arreglo de Resistencias - 4.7 KΩ", ["4.7kω", "pack"])
score2 = _score_relevancia("RPACK Arreglo de Resistencias - 220 Ω", ["4.7kω", "pack"])
print(f"  RPACK 4.7K: {score1} | RPACK 220: {score2} (4.7K debe ser mayor)")
score3 = _score_relevancia("Capacitor Electrolítico 25V - 470 uF", ["electrolitico", "470µf", "16v"])
score4 = _score_relevancia("Capacitor electrolítico SMD - 10 uF", ["electrolitico", "470µf", "16v"])
print(f"  Cap 470uF: {score3} | Cap 10uF: {score4} (470 debe ser mayor)")

print("\n=== 4. Filtrado por niveles (regleta hembra) ===")
opciones = [
    {"nombre_producto": "Adaptador Micro USB hembra tipo B a DIP", "precio_base": 0.5, "disponible": True},
    {"nombre_producto": "40 Header Macho", "precio_base": 0.49, "disponible": True},
]
res = _filtrar_y_ordenar_por_relevancia(
    opciones, ["regleta", "hembra", "40 pines"], "tira de pines", "regleta"
)
for op in res:
    print(f"  {op['nombre_producto']}")
print("  (40 Header Macho debe ir primero)")
