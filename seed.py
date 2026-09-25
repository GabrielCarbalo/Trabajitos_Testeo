"""
Carga datos DEMO para poder ver la plataforma funcionando sin usuarios reales.

IMPORTANTE: todo lo que crea este script es ficticio (nombres, teléfonos,
descripciones). No representa personas reales. Se usa únicamente para tener
contenido de ejemplo mientras se desarrolla y se prueba la plataforma.

Las 6 cuentas de colaborador que se crean acá son de prueba a propósito:
comparten la contraseña "demo1234" para que sea fácil iniciar sesión con
cualquiera de ellas y probar el panel de colaborador (Fase 5) sin tener que
registrar una cuenta nueva. No usar este patrón para cuentas reales.

Uso:
    python seed.py

El script es idempotente: si ya existen categorías cargadas, no vuelve a
insertar datos duplicados.
"""

from app import create_app, db
from app.models import Category, CollaboratorProfile, Service, User

CATEGORIAS_DEMO = ["Limpieza", "Jardinería", "Reparaciones", "Mascotas", "Cocina", "Otros"]

# Colaboradores ficticios de ejemplo, cada uno con un servicio publicado.
COLABORADORES_DEMO = [
    {
        "nombre": "Carlos Menjívar (demo)",
        "correo": "carlos.demo@trabajitos.test",
        "telefono": "+50370000001",
        "descripcion": "Ayudo con limpieza profunda de casas y apartamentos. Puntual y de confianza.",
        "categoria": "Limpieza",
        "servicio": {
            "titulo": "Limpieza profunda de casas",
            "descripcion": "Limpieza completa de cocina, baños y áreas comunes. Traigo mis propios insumos.",
            "precio": 15.00,
            "modalidad": "hora",
            "disponibilidad": "Lunes a sábado, todo el día",
        },
    },
    {
        "nombre": "Ana Lucía Portillo (demo)",
        "correo": "analucia.demo@trabajitos.test",
        "telefono": "+50370000002",
        "descripcion": "Diseño y mantengo jardines pequeños y medianos hace más de 5 años.",
        "categoria": "Jardinería",
        "servicio": {
            "titulo": "Poda y mantenimiento de jardín",
            "descripcion": "Poda de árboles y arbustos, corte de grama y limpieza de áreas verdes.",
            "precio": 25.00,
            "modalidad": "tarea",
            "disponibilidad": "Fines de semana",
        },
    },
    {
        "nombre": "José Ramírez (demo)",
        "correo": "jose.demo@trabajitos.test",
        "telefono": "+50370000003",
        "descripcion": "Cerrajero y reparaciones básicas del hogar (grifería, electricidad menor).",
        "categoria": "Reparaciones",
        "servicio": {
            "titulo": "Cerrajería y reparaciones del hogar",
            "descripcion": "Cambio de cerraduras, reparación de fugas menores y arreglos generales.",
            "precio": 20.00,
            "modalidad": "hora",
            "disponibilidad": "Todos los días, 8am a 6pm",
        },
    },
    {
        "nombre": "Fátima Cruz (demo)",
        "correo": "fatima.demo@trabajitos.test",
        "telefono": "+50370000004",
        "descripcion": "Paseo y cuido mascotas en mi zona. Amante de los animales.",
        "categoria": "Mascotas",
        "servicio": {
            "titulo": "Paseo y baño de perros",
            "descripcion": "Paseos de 30-45 minutos y baño con productos hipoalergénicos.",
            "precio": 8.00,
            "modalidad": "tarea",
            "disponibilidad": "Tardes, lunes a viernes",
        },
    },
    {
        "nombre": "Roberto Alas (demo)",
        "correo": "roberto.demo@trabajitos.test",
        "telefono": "+50370000005",
        "descripcion": "Cocino para eventos pequeños y pedidos especiales a domicilio.",
        "categoria": "Cocina",
        "servicio": {
            "titulo": "Preparación de comida para eventos",
            "descripcion": "Menús salvadoreños para reuniones familiares y eventos pequeños.",
            "precio": 60.00,
            "modalidad": "dia",
            "disponibilidad": "Con 3 días de anticipación",
        },
    },
    {
        "nombre": "Marta Elena Guevara (demo)",
        "correo": "martaelena.demo@trabajitos.test",
        "telefono": "+50370000006",
        "descripcion": "Hago mandados, trámites y ayudo con tareas variadas.",
        "categoria": "Otros",
        "servicio": {
            "titulo": "Mandados y trámites varios",
            "descripcion": "Hago filas, compras y trámites sencillos por vos.",
            "precio": 10.00,
            "modalidad": "hora",
            "disponibilidad": "Lunes a viernes, mañanas",
        },
    },
]


def seed():
    app = create_app()
    with app.app_context():
        if Category.query.first():
            print("Ya existen datos cargados. No se insertó nada nuevo.")
            return

        categorias = {}
        for nombre in CATEGORIAS_DEMO:
            slug = nombre.lower().replace("í", "i").replace("ó", "o").replace(" ", "-")
            categoria = Category(nombre=nombre, slug=slug)
            db.session.add(categoria)
            categorias[nombre] = categoria

        for datos in COLABORADORES_DEMO:
            usuario = User(
                nombre=datos["nombre"],
                correo=datos["correo"],
                tipo_usuario="colaborador",
            )
            usuario.set_password("demo1234")

            perfil = CollaboratorProfile(
                usuario=usuario,
                descripcion=datos["descripcion"],
                telefono_whatsapp=datos["telefono"],
            )

            servicio_datos = datos["servicio"]
            servicio = Service(
                colaborador=perfil,
                categoria=categorias[datos["categoria"]],
                titulo=servicio_datos["titulo"],
                descripcion=servicio_datos["descripcion"],
                precio=servicio_datos["precio"],
                modalidad=servicio_datos["modalidad"],
                disponibilidad=servicio_datos["disponibilidad"],
            )

            db.session.add_all([usuario, perfil, servicio])

        db.session.commit()
        print(f"Datos demo cargados: {len(CATEGORIAS_DEMO)} categorías y {len(COLABORADORES_DEMO)} colaboradores con servicios.")


if __name__ == "__main__":
    seed()
