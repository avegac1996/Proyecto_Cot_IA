import sys, os
sys.path.insert(0, "/app")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://cotia_user:cotia_pass@cotia_db:5432/cotia_db")

import asyncio
from sqlalchemy import text
from app.core.database import async_session
from app.services.scraping.busqueda import _score_relevancia, _normalizar_texto, _filtrar_y_ordenar_por_relevancia

async def main():
    async with async_session() as db:
        # Rele
        print("=== RELE 1 CANAL 5V ===")
        descriptores = ["modulo", "1 canal", "5v", "optoacoplado"]
        termino_base = "rele"
        tipo = "rele"
        result = await db.execute(text("SELECT nombre FROM catalogo_productos WHERE tienda='AV Electronics'"))
        productos = [r[0] for r in result.fetchall()]
        scored = []
        for p in productos:
            s = _score_relevancia(p, descriptores)
            if s > 0 or True:
                nombre_norm = _normalizar_texto(p)
                # check termino_base bonus
                base_norm = _normalizar_texto(termino_base)
                if _normalizar_texto(termino_base) in nombre_norm or base_norm.replace(" ","") in nombre_norm.replace(" ",""):
                    s2 = s + 20
                else:
                    s2 = s
                if s2 > 0:
                    scored.append((s, s2, p))
        scored.sort(key=lambda x: -x[1])
        for s, s2, p in scored[:10]:
            print(f"  score={s:>4} total={s2:>4} | {p}")

        print("\n=== TERMINAL BLOCK 2 PINES ===")
        descriptores = ["2 pines"]
        termino_base = "terminal block"
        tipo = "terminal"
        scored = []
        for p in productos:
            s = _score_relevancia(p, descriptores)
            nombre_norm = _normalizar_texto(p)
            base_norm = _normalizar_texto(termino_base)
            if base_norm in nombre_norm or base_norm.replace(" ","") in nombre_norm.replace(" ",""):
                s2 = s + 20
            elif " " in base_norm:
                extra = sum(5 for w in base_norm.split() if len(w)>=4 and w in nombre_norm)
                s2 = s + extra
            else:
                s2 = s
            if s2 > 0:
                scored.append((s, s2, p))
        scored.sort(key=lambda x: -x[1])
        for s, s2, p in scored[:10]:
            print(f"  score={s:>4} total={s2:>4} | {p}")

        print("\n=== BOMBA PERIFERICA 220V ===")
        descriptores = ["periferica", "220v", "ac"]
        termino_base = "bomba de agua"
        tipo = "bomba"
        scored = []
        for p in productos:
            s = _score_relevancia(p, descriptores)
            nombre_norm = _normalizar_texto(p)
            base_norm = _normalizar_texto(termino_base)
            if base_norm in nombre_norm or base_norm.replace(" ","") in nombre_norm.replace(" ",""):
                s2 = s + 20
            elif " " in base_norm:
                extra = sum(5 for w in base_norm.split() if len(w)>=4 and w in nombre_norm)
                s2 = s + extra
            else:
                s2 = s
            if s2 > 0:
                scored.append((s, s2, p))
        scored.sort(key=lambda x: -x[1])
        for s, s2, p in scored[:10]:
            print(f"  score={s:>4} total={s2:>4} | {p}")

asyncio.run(main())
