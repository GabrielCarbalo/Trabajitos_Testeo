# TRABAJITOS — CÓDIGO COMPLETO

## Qué contiene
Copia completa y fiel del código **propio** actual de TRABAJITOS: 52 archivos, con las mismas rutas relativas que el original. No incluye dependencias instaladas, cachés, datos de ejecución ni secretos.

## Estado de la exportación
- Fecha/hora: 2026-09-24 14:53:43
- Ruta fuente: `C:\Users\gabog\OneDrive\Documentos\Testeo_Claude\trabajitos`
- Branch: no aplica (no es un repositorio Git)
- Commit/HEAD: no aplica
- Cambios sin commit: no aplica; se exportó el estado actual del sistema de archivos.

## Stack real detectado (verificado en `requirements.txt`, `app/config.py`, `migrations/` y el código)
- Python 3.14.4 (versión del entorno virtual del proyecto)
- Flask 3.0.3 · Werkzeug 3.0.3 · Jinja2 (templates)
- Flask-SQLAlchemy 3.1.1 (ORM) · SQLite por defecto, configurable con `DATABASE_URL`
- Flask-Migrate 4.0.7 (Alembic) · Flask-Login 0.6.3 · Flask-WTF 1.2.1 (CSRF) · python-dotenv 1.0.1
- Frontend: HTML (Jinja), CSS y JavaScript vanilla; fuentes Anybody y Barlow self-hosted
- Pruebas: `unittest` (librería estándar)
- No existen: `apps/web`, `apps/api`, `packages/shared`, Node/pnpm, Docker, `.github/` (CI/CD), Husky.

## Estructura
- `app/` — aplicación Flask: `__init__.py`, `config.py`, `models.py` (Models), `routes/` (Controllers), `services/` (imágenes y moderación), `templates/` (Views), `static/` (CSS, JS, fuentes, SVG)
- `migrations/` — migraciones Alembic
- `tests/` — pruebas
- `run.py`, `seed.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `DESARROLLO.md`

## Frontend
`app/templates/` y `app/static/` (CSS, JS, fuentes, SVG).

## Backend
`app/__init__.py`, `app/config.py`, `app/models.py`, `app/routes/`, `app/services/`, `run.py`.

## Shared
No existe un paquete shared independiente en la implementación actual.

## Base de datos
El esquema se recrea con Flask-Migrate (no hay `db.create_all()` automático). Los datos DEMO ficticios se cargan con `seed.py`. La base local real no se exporta.

## Instalación de dependencias (comandos del README original)
```
python -m venv venv
venv\Scripts\activate.bat          (Windows cmd)  |  venv\Scripts\Activate.ps1 (PowerShell)  |  source venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
```

## Variables de entorno
Copiar `.env.example` a `.env` y ajustar: `SECRET_KEY` (definir una propia), `DATABASE_URL` (opcional; por defecto SQLite en `instance/`), `FLASK_DEBUG` (1 en desarrollo, 0 en producción). No escribir secretos reales en `.env.example`.

## Cómo ejecutar
```
set FLASK_APP=run.py
flask db upgrade
python seed.py            (opcional: datos DEMO)
python run.py
```
Pruebas: `python -m unittest tests.test_registro tests.test_servicios -v`

## Cómo abrir localmente
`http://127.0.0.1:5000`

## Archivos excluidos
- **H** — H. dependencias externas instaladas (venv/): 2621 archivos
- **J** — J. caché de Python (__pycache__/*.pyc): 20 archivos
- **L** — L. base de datos local con datos de ejecución/pruebas (cuentas, correos, hashes): 1 archivos
- **M** — M. exportación anterior (paquete de entrega MVC+POO y su ZIP): 29 archivos
- Además, `.git/` no existe; no hay `.env` reales; `app/static/uploads/` solo contiene carpetas vacías (sin fotografías).

## Restauración
Descomprimir `TRABAJITOS-CODIGO-COMPLETO.zip`, entrar a la carpeta, crear el entorno virtual e instalar dependencias (ver arriba), copiar `.env.example` a `.env`, ejecutar `flask db upgrade` y `python run.py`.
