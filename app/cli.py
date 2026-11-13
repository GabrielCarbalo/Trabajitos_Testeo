"""
Comandos de terminal propios de TRABAJITOS (se ejecutan con "flask ...").

Crear un administrador es a propósito una acción de terminal y no de la
web: el registro público nunca puede dar permisos de administración.
"""

import click

from app import db
from app.models import RegistroInvalido, User


@click.command("crear-admin")
@click.option("--nombre", prompt="Nombre", help="Nombre de la persona administradora.")
@click.option("--correo", prompt="Correo", help="Correo con el que va a iniciar sesión.")
@click.option(
    "--password",
    prompt="Contraseña",
    hide_input=True,
    confirmation_prompt=True,
    help="Si no se pasa, se pide de forma oculta (recomendado).",
)
def crear_admin(nombre, correo, password):
    """Crea una cuenta de administrador."""
    try:
        usuario = User.crear_admin(nombre, correo, password)
    except RegistroInvalido as error:
        for mensaje in error.errores:
            click.echo(mensaje, err=True)
        raise SystemExit(1)

    db.session.add(usuario)
    db.session.commit()
    click.echo(f"Administrador creado: {usuario.correo}")
