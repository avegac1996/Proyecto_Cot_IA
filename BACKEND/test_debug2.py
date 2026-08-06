import re

def _normalizar_texto(t):
    return t.lower().strip()

def _palabra_en_texto(palabra, texto):
    patron = r'(?<![a-z0-9])' + re.escape(palabra) + r'(?![a-z0-9])'
    return bool(re.search(patron, texto))

# Test "1 canal" vs "Módulo Relé Estado Sólido 2 Canales"
desc = "1 canal"
nombre = "modulo rele estado solido 2 canales"
partes = desc.split()
partes_numericas = [p for p in partes if p.replace(".", "").replace(",", "").isdigit()]
partes_texto = [p for p in partes if p not in partes_numericas]
print(f"desc='{desc}' partes_num={partes_numericas} partes_texto={partes_texto}")
print(f"'1' in '{nombre}': {_palabra_en_texto('1', nombre)}")
print(f"'canal' in '{nombre}': {_palabra_en_texto('canal', nombre)}")
print(f"'canales' in '{nombre}': {_palabra_en_texto('canales', nombre)}")

# The issue: '1' doesn't match '2 canales' (good), but 'canal' doesn't match 'canales' (bad - singular vs plural)
# Need to also check plural: 'canales'
texto_coincide = any(
    _palabra_en_texto(p, nombre) or _palabra_en_texto(p + "s", nombre)
    for p in partes_texto if len(p) >= 3
)
print(f"texto_coincide (with plural check): {texto_coincide}")

# Now test "2 pines" vs "Bornera Terminal con Tornillo - 2-Pin"
desc2 = "2 pines"
nombre2 = "bornera terminal con tornillo 2-pin"
partes2 = desc2.split()
partes_num2 = [p for p in partes2 if p.replace(".", "").replace(",", "").isdigit()]
partes_txt2 = [p for p in partes2 if p not in partes_num2]
print(f"\ndesc='{desc2}' partes_num={partes_num2} partes_texto={partes_txt2}")
print(f"'2' in '{nombre2}': {_palabra_en_texto('2', nombre2)}")
print(f"'pines' in '{nombre2}': {_palabra_en_texto('pines', nombre2)}")
print(f"'pin' in '{nombre2}': {_palabra_en_texto('pin', nombre2)}")
