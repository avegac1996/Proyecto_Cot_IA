import sys, os, asyncio
sys.path.insert(0, "/app")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://cotia_user:cotia_pass@cotia_db:5432/cotia_db")
from sqlalchemy import text
from app.core.database import async_session
from app.services.scraping.busqueda import _score_relevancia, _normalizar_texto, _match_tipo, _palabra_en_texto, _palabra_o_plural_en_texto

async def main():
    async with async_session() as db:
        descriptores = ["2 pines"]
        termino_base = "terminal block"
        tipo = "terminal"
        result = await db.execute(text("SELECT nombre FROM catalogo_productos WHERE tienda='AV Electronics'"))
        productos = [r[0] for r in result.fetchall()]
        scored = []
        for p in productos:
            nombre_norm = _normalizar_texto(p)
            s = _score_relevancia(p, descriptores)
            if s < 0:
                continue
            base_bonus = 0
            base_norm = _normalizar_texto(termino_base)
            if _palabra_en_texto(base_norm, nombre_norm) or base_norm.replace(" ","") in nombre_norm.replace(" ",""):
                base_bonus = 10
            elif " " in base_norm:
                for w in base_norm.split():
                    if len(w) >= 4 and _palabra_en_texto(w, nombre_norm):
                        base_bonus += 3
            total = s + base_bonus
            es_tipo = _match_tipo(nombre_norm, tipo, termino_base)
            if es_tipo and total > 0:
                scored.append((s, base_bonus, total, p))
        scored.sort(key=lambda x: -x[2])
        print("=== TERMINAL BLOCK 2 PINES (filtered) ===")
        for s, b, t, p in scored[:10]:
            print(f"  score={s:>4} base={b:>4} total={t:>4} | {p}")

asyncio.run(main())
