from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import Base, async_session, engine
from app.core.security import hash_password
from app.models import (
    BancoPregunta,
    ConfiguracionNegocio,
    Equivalencia,
    Producto,
    Tienda,
    Usuario,
)

logger = logging.getLogger(__name__)

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
    {
        "nombre": "ElectroStore",
        "url_base": "https://electrostoree.com/",
        "selectores": {
            "product_card": "div.product-card, .card--product, .card",
            "product_url": "a.product-title, .card__title a, .card__heading a",
            "price": ".price, .price__regular",
            "availability": ".product-form__inventory, .stock-status",
            "stock_in_classes": False,
            "search_url": "https://electrostoree.com/search?q={query}",
            "product_page_price": ".price__regular .price-item",
            "product_page_availability": ".product-form__inventory, .stock-status",
        },
        "usa_javascript": False,
        "ttl_horas": 48,
        "activa": False,
    },
]

PREGUNTAS_SEED = [
    ("Sensores", "¿Podría indicar qué tipo de sensor necesita? (ej: temperatura DHT11/DHT22, distancia, luz, movimiento)", "tipo_o_modelo", 1),
    ("Motores", "¿El motor es DC, servomotor o paso a paso (stepper)?", "tipo_o_modelo", 2),
    ("Transistores", "¿El transistor es NPN, PNP, MOSFET u otro tipo?", "tipo_o_modelo", 3),
    ("Diodos", "¿Necesita un diodo rectificador, Zener o Schottky?", "tipo_o_modelo", 4),
    ("Integrados", "¿Qué circuito integrado o chip necesita? (ej: ATmega328P, NE555)", "tipo_o_modelo", 5),
    ("General", "¿Podría indicar a qué componente se refiere exactamente?", "tipo", 6),
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

        # Seed de configuración de negocio
        result = await db.execute(select(ConfiguracionNegocio))
        if result.first() is None:
            db.add(ConfiguracionNegocio(
                clave="margen_competencia",
                valor="5.0",
                descripcion="Margen % aplicado a productos de tiendas externas",
            ))
            db.add(ConfiguracionNegocio(
                clave="tienda_propia",
                valor="AV Electronics",
                descripcion="Nombre de la tienda propia (sin margen)",
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
    # Cargar catálogo WooCommerce sincrónicamente al inicio
    from app.services.scraping import catalogo

    async with async_session() as db:
        result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
        for tienda in result.scalars().all():
            url = tienda.url_base.rstrip("/")
            try:
                if await catalogo.soporta_api_wc(url):
                    await catalogo.refrescar_catalogo(url)
                    logger.info("Catálogo inicial cargado para %s", url)
            except Exception as exc:
                logger.warning("Carga inicial de catálogo falló para %s: %s", url, exc)

    # Refresh de catálogo en background (cada hora)
    tareas_refresh = []
    async with async_session() as db:
        result = await db.execute(select(Tienda).where(Tienda.activa.is_(True)))
        for tienda in result.scalars().all():
            tareas_refresh.append(catalogo.iniciar_refresh_background(tienda.url_base.rstrip("/")))
    yield
    for tarea in tareas_refresh:
        tarea.cancel()
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
