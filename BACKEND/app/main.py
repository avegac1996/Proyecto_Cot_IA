from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import Base, async_session, engine
from app.core.security import hash_password
from app.models import (
    BancoPregunta,
    Equivalencia,
    Producto,
    Tienda,
    Usuario,
)

TIENDAS_SEED = [
    {
        "nombre": "AV Electronics",
        "url_base": "https://avelectronics.cc/",
        "selectores": {
            "product_card": "article.product",
            "product_url": "h2.entry-title a",
            "stock_in_classes": True,
            "search_url": "https://avelectronics.cc/?s={query}",
            "product_page_price": "p.price",
            "product_page_availability": ".stock",
        },
        "usa_javascript": False,
        "ttl_horas": 24,
    },
    {
        "nombre": "Megatronica",
        "url_base": "https://megatronica.cc/",
        "selectores": {
            "product_card": "article.product",
            "product_url": "h2.woocommerce-loop-product__title a, h2 a",
            "stock_in_classes": True,
            "search_url": "https://megatronica.cc/?s={query}",
            "product_page_price": "p.price",
            "product_page_availability": ".stock",
        },
        "usa_javascript": True,
        "ttl_horas": 12,
    },
]

PREGUNTAS_SEED = [
    ("General", "¿Podría confirmar si la lista enviada está completa?", None, 8),
    ("General", "¿Podría confirmar la cantidad exacta de unidades?", "cantidad", 6),
    ("Resistencias", "¿Cuál es el valor de la resistencia? (ej: 220 Ω, 1 kΩ, 10 kΩ)", "valor", 1),
    ("Capacitores", "¿Podría indicar la capacitancia del capacitor? (ej: 100 µF, 10 nF)", "valor", 1),
    ("LED", "¿Qué color o colores de LED necesita?", "color", 1),
    ("LED", "¿Qué tamaño de LED requiere? (3mm, 5mm, SMD)", "tamano", 2),
    ("Transistores", "¿El transistor es NPN, PNP, MOSFET u otro tipo?", "tipo_o_modelo", 1),
    ("Diodos", "¿Necesita un diodo rectificador, Zener o Schottky?", "tipo_o_modelo", 1),
    ("Integrados", "¿Necesita encapsulado DIP, SMD u otro formato?", "encapsulado", 4),
    ("Sensores", "¿Podría indicar la aplicación o función del sensor?", "tipo_o_modelo", 3),
    ("Fuentes", "¿Qué voltaje y corriente necesita la fuente?", "valor", 2),
    ("Conectores", "¿Qué tipo de conector requiere?", "tipo_o_modelo", 3),
    ("General", "¿Podría indicar a qué componente se refiere exactamente?", "tipo", 1),
]

PRODUCTOS_SEED = [
    {"nombre": "Resistencia 220Ω 1/4W", "categoria": "resistencia", "especificaciones": {"valor": "220", "unidad": "ohm", "potencia": "1/4W"}, "terminos_coloquiales": ["resistencia de 220"]},
    {"nombre": "Resistencia 1kΩ 1/4W", "categoria": "resistencia", "especificaciones": {"valor": "1000", "unidad": "ohm", "potencia": "1/4W"}, "terminos_coloquiales": ["resistencia de 1k"]},
    {"nombre": "Resistencia 10kΩ 1/4W", "categoria": "resistencia", "especificaciones": {"valor": "10000", "unidad": "ohm", "potencia": "1/4W"}, "terminos_coloquiales": ["resistencia de 10k"]},
    {"nombre": "Capacitor Electrolítico 100µF 25V", "categoria": "capacitor", "especificaciones": {"valor": "100", "unidad": "uF", "voltaje": "25V"}, "terminos_coloquiales": ["condensador de 100"]},
    {"nombre": "Capacitor Cerámico 100nF", "categoria": "capacitor", "especificaciones": {"valor": "100", "unidad": "nF"}, "terminos_coloquiales": ["capacitor 104"]},
    {"nombre": "LED Rojo 5mm", "categoria": "led", "especificaciones": {"color": "rojo", "tamano": "5mm"}, "terminos_coloquiales": ["foquito rojo", "el foquito ese chiquito"]},
    {"nombre": "LED Verde 5mm", "categoria": "led", "especificaciones": {"color": "verde", "tamano": "5mm"}, "terminos_coloquiales": ["foquito verde"]},
    {"nombre": "LED RGB 5mm", "categoria": "led", "especificaciones": {"color": "rgb", "tamano": "5mm"}, "terminos_coloquiales": ["led de colores"]},
    {"nombre": "Transistor 2N2222 NPN", "categoria": "transistor", "especificaciones": {"tipo": "NPN", "modelo": "2N2222"}, "terminos_coloquiales": ["transistor pequeño negro"]},
    {"nombre": "Diodo 1N4007 Rectificador", "categoria": "diodo", "especificaciones": {"tipo": "rectificador", "modelo": "1N4007"}, "terminos_coloquiales": []},
    {"nombre": "Arduino UNO R3", "categoria": "arduino", "especificaciones": {"chip": "ATmega328P", "voltaje": "5V"}, "terminos_coloquiales": ["placa arduino", "tarjeta de desarrollo"]},
    {"nombre": "Protoboard 830 puntos", "categoria": "protoboard", "especificaciones": {"puntos": 830}, "terminos_coloquiales": ["tablita blanca de huequitos", "tabla de pruebas"]},
    {"nombre": "Cable Jumper Macho-Macho (pack 40)", "categoria": "cable", "especificaciones": {"tipo": "macho-macho", "cantidad_pack": 40}, "terminos_coloquiales": ["jumpers", "cablecitos"]},
    {"nombre": "Sensor de Temperatura LM35", "categoria": "sensor", "especificaciones": {"tipo": "temperatura", "modelo": "LM35"}, "terminos_coloquiales": ["sensor de calor"]},
]


async def seed_catalogos():
    """Crea tiendas, banco de preguntas, productos y equivalencias si no existen."""
    async with async_session() as db:
        result = await db.execute(select(Tienda))
        if result.first() is None:
            for t in TIENDAS_SEED:
                db.add(Tienda(**t))

        result = await db.execute(select(BancoPregunta))
        if result.first() is None:
            for categoria, pregunta, campo, prioridad in PREGUNTAS_SEED:
                db.add(BancoPregunta(
                    categoria=categoria,
                    pregunta=pregunta,
                    campo_a_desambiguar=campo,
                    prioridad=prioridad,
                ))

        result = await db.execute(select(Producto))
        if result.first() is None:
            for p in PRODUCTOS_SEED:
                producto = Producto(**p)
                db.add(producto)
                await db.flush()
                for termino in p["terminos_coloquiales"]:
                    db.add(Equivalencia(
                        producto_id=producto.id,
                        termino_equivalente=termino,
                        tipo_match="coloquial",
                        confianza=1.0,
                    ))

        await db.commit()


async def seed_default_users():
    """Crea los usuarios por defecto (admin y user) si no existen."""
    async with async_session() as db:
        # Admin
        result = await db.execute(select(Usuario).where(Usuario.username == "admin"))
        if result.scalar_one_or_none() is None:
            admin = Usuario(
                username="admin",
                email="admin@cotia.com",
                password_hash=hash_password("Admin123!"),
                rol="admin",
                activo=True,
            )
            db.add(admin)

        # User
        result = await db.execute(select(Usuario).where(Usuario.username == "user"))
        if result.scalar_one_or_none() is None:
            user = Usuario(
                username="user",
                email="user@cotia.com",
                password_hash=hash_password("User123!"),
                rol="user",
                activo=True,
            )
            db.add(user)

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed de usuarios por defecto
    await seed_default_users()
    # Seed de catálogos (tiendas, preguntas, productos)
    await seed_catalogos()
    yield
    await engine.dispose()


app = FastAPI(
    title="CotIA API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
