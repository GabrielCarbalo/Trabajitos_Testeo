# Despliegue de TRABAJITOS en Railway

Guía paso a paso. Desarrollo local sigue igual (SQLite + `python run.py`);
esto es solo para producción.

## Cómo queda armado

| Pieza | Desarrollo | Producción (Railway) |
|---|---|---|
| Servidor | `python run.py` (Flask) | `gunicorn run:app` (lee `gunicorn.conf.py`) |
| Base de datos | SQLite en `instance/trabajitos.db` | PostgreSQL de Railway (`DATABASE_URL`) |
| Driver | — | `psycopg` 3 (la app convierte `postgresql://` a `postgresql+psycopg://`) |
| Esquema | `flask --app run.py db upgrade` | el mismo comando, como *Pre-deploy Command* |
| Fotos (archivos) | `app/static/uploads/` | Volumen de Railway montado en `/data` → `UPLOAD_FOLDER=/data/uploads` |
| URL de las fotos | `/uploads/<profile\|portfolio>/<uuid>.<ext>` | igual |
| Healthcheck | `/health` | `/health` |

Las fotos se sirven por la ruta `main.archivo_subido` (`/uploads/...`), que
lee desde `UPLOAD_FOLDER`. Por eso la URL funciona aunque la carpeta esté
fuera de `app/static`, y además solo entrega fotos aprobadas (las demás
solo las ve su dueño o un administrador).

Las categorías (Limpieza, Jardinería, …) las crea la migración
`5c1e7d9a2b40`, así que una base nueva queda lista sin ejecutar `seed.py`.
**`seed.py` no se ejecuta en producción** (crea cuentas con contraseña
conocida; con `APP_ENV=production` se niega a correr).

## Variables del servicio web

| Variable | Valor |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | una clave aleatoria propia: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | referencia al servicio PostgreSQL: `${{Postgres.DATABASE_URL}}` (cambiar `Postgres` si el servicio tiene otro nombre) |
| `UPLOAD_FOLDER` | `/data/uploads` |
| `FLASK_DEBUG` | `0` |

`PORT` y `RAILWAY_VOLUME_MOUNT_PATH` los pone Railway solo. Si falta
`SECRET_KEY`, `DATABASE_URL` o `UPLOAD_FOLDER` (o esta no está dentro del
volumen), la app **no arranca** y el log dice qué variable falta: así no
puede quedar publicada con la clave de desarrollo, ni guardando datos o
fotos dentro del contenedor (que se borra en cada deploy).

## Pasos

1. **Subir el código a GitHub** (commit + push de la rama, y merge a la
   rama que vaya a desplegar Railway).
2. En Railway: **New Project → Deploy from GitHub repo** → elegir
   `GabrielCarbalo/Trabajitos_Testeo` y la rama.
3. En el mismo proyecto: **+ New → Database → PostgreSQL**.
4. En el servicio web → **Variables**: cargar las 5 variables de la tabla.
5. En el servicio web → clic derecho / **Attach Volume** → *Mount path*:
   `/data`.
6. En el servicio web → **Settings → Deploy**:
   - *Custom Start Command*: `gunicorn run:app`
   - *Pre-deploy Command*: `flask --app run.py db upgrade`
   - *Healthcheck Path*: `/health`
7. **Settings → Networking → Generate Domain** para tener la URL pública.
8. Deploy. En los logs del pre-deploy deben verse las 4 migraciones
   (`Running upgrade ... -> 5c1e7d9a2b40`); en los del servicio,
   `Listening at: http://0.0.0.0:<PORT>`.
9. **Crear el administrador** (la web nunca crea administradores). Desde
   una consola del servicio (`railway ssh`, o *Shell* en el panel):

   ```
   flask --app run.py crear-admin
   ```

   Pide nombre, correo y contraseña (oculta). Usar una contraseña fuerte.

## Comprobación después del deploy

1. `https://<dominio>/health` → `{"status":"ok"}`.
2. Registrar un colaborador de prueba, subir foto de perfil y 2 fotos de
   portafolio, publicar un servicio, verlo en Explorar y en el perfil
   público (botón de WhatsApp).
3. **Redeploy** (o *Restart*) del servicio web.
4. Volver a entrar: el usuario, el servicio, la foto de perfil y el
   portafolio tienen que seguir ahí, con las mismas URLs. Si una foto
   desapareció, el volumen no está montado en `/data` o `UPLOAD_FOLDER`
   no apunta a `/data/uploads`.

## Notas

- El Python de producción está fijado en `.python-version` (3.14, la misma
  versión con la que se probó).
- Con un volumen, Railway no permite réplicas y hay unos segundos sin
  servicio en cada redeploy (limitación documentada por Railway).
- El volumen no está montado durante el pre-deploy; no hace falta: las
  migraciones solo tocan la base de datos.
- La base local `instance/trabajitos.db` **no** se copia a producción:
  producción empieza limpia.
