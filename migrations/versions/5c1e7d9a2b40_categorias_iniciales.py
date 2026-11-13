"""Categorias iniciales (datos de referencia)

Revision ID: 5c1e7d9a2b40
Revises: 0bea2d090669
Create Date: 2026-11-12 12:00:00.000000

Las categorías son un catálogo fijo: sin ellas un colaborador no puede
publicar servicios. Antes solo las creaba seed.py, junto con cuentas DEMO
que no deben existir en producción. Esta migración inserta únicamente las
categorías que falten (por slug), así que no cambia nada en una base que ya
las tiene y puede aplicarse tanto en desarrollo como en producción.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c1e7d9a2b40'
down_revision = '0bea2d090669'
branch_labels = None
depends_on = None

CATEGORIAS = [
    ("Limpieza", "limpieza"),
    ("Jardinería", "jardineria"),
    ("Reparaciones", "reparaciones"),
    ("Mascotas", "mascotas"),
    ("Cocina", "cocina"),
    ("Otros", "otros"),
]


def upgrade():
    conexion = op.get_bind()
    categorias = sa.table("categories", sa.column("nombre", sa.String), sa.column("slug", sa.String))
    existentes = {fila.slug for fila in conexion.execute(sa.select(categorias.c.slug))}
    faltantes = [
        {"nombre": nombre, "slug": slug} for nombre, slug in CATEGORIAS if slug not in existentes
    ]
    if faltantes:
        op.bulk_insert(categorias, faltantes)


def downgrade():
    # A propósito no se borran: puede haber servicios que las referencian.
    pass
