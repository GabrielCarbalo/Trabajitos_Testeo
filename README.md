# TRABAJITOS

## Proyecto

TRABAJITOS es una plataforma web pensada para El Salvador que conecta a dos
tipos de personas: quien **necesita** un servicio puntual (limpieza,
jardinería, reparaciones, cuidado de mascotas, cocina, etc.) y quien **sabe
hacerlo** y quiere ofrecer su talento. Es un proyecto académico de la
materia de Desarrollo de Software, construido para sentirse como una
plataforma real y con identidad propia, no como un ejercicio genérico.

Flujo principal:

```
Necesito algo → Lo busco → Encuentro colaboradores → Comparo → Reviso su perfil → Contacto por WhatsApp
Sé hacer algo → Creo mi perfil → Publico mi servicio → Indico precio y disponibilidad → Personas me encuentran
```

## Tecnologías

| Capa | Tecnología | Para qué se usa |
|---|---|---|
| Backend | Python + Flask | Servidor web y lógica de la aplicación |
| ORM | SQLAlchemy (Flask-SQLAlchemy) | Mapear los modelos de datos a la base de datos |
| Base de datos | SQLite (desarrollo) | Almacenamiento local, sin instalación adicional |
| Autenticación | Flask-Login | Manejo de sesiones de usuario |
| Templates | Jinja2 | Renderizado de HTML del lado del servidor |
| Frontend | HTML5 + CSS3 + JavaScript vanilla | Interfaz, sin frameworks de frontend |

La conexión a la base de datos se controla con la variable de entorno
`DATABASE_URL`, así que en el futuro se puede migrar a PostgreSQL sin tocar
el código, solo cambiando esa variable.

## Estructura de carpetas

```
trabajitos/
├── app/
│   ├── __init__.py       # Application factory: crea y configura la app Flask
│   ├── config.py         # Configuración leída desde variables de entorno
│   ├── models.py         # Modelos de datos (User, CollaboratorProfile, Category, Service)
│   ├── routes/            # Blueprints: rutas agrupadas por área
│   │   ├── main.py        # Home, Explorar, Perfil de colaborador
│   │   ├── auth.py        # Registro, login, logout
│   │   └── dashboard.py   # Panel privado, foto de perfil, portafolio, servicios
│   ├── services/           # Lógica que no es "una ruta": subida y moderación de imágenes
│   │   ├── image_storage.py       # Dónde se guardan las fotos (local hoy, cloud a futuro)
│   │   ├── image_quality_service.py  # Señales de calidad/moderación de una foto
│   │   └── uploads.py             # Validación (formato/tamaño) + orquestación
│   ├── templates/         # Vistas Jinja2
│   └── static/
│       ├── css/style.css  # Sistema visual completo (variables, componentes)
│       ├── js/main.js     # Interacciones (menú mobile, lightbox del portafolio, etc.)
│       ├── img/           # Imágenes propias del sitio (incluye el patrón cultural SVG)
│       ├── fonts/         # Archivos .woff2 de Anybody y Barlow (ver abajo)
│       └── uploads/       # Fotos subidas por los usuarios (no se sube a Git, ver abajo)
├── instance/               # Base de datos SQLite local (no se sube a Git)
├── seed.py                 # Carga datos de demostración
├── run.py                  # Punto de entrada para levantar el servidor
├── requirements.txt
├── .env.example
└── .gitignore
```

## Instalación

### 1. Crear entorno virtual

```bash
cd trabajitos
python -m venv venv
```

Activarlo:

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (cmd)
venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

Editar `.env` y, como mínimo, definir un `SECRET_KEY` propio. `DATABASE_URL`
puede quedar como está para desarrollo (SQLite).

### 4. Crear e inicializar la base de datos

El esquema de la base de datos se maneja con **Flask-Migrate** (no hay un
`db.create_all()` automático a propósito: si conviviera con las migraciones,
una instalación nueva podría terminar con las tablas creadas pero sin el
historial de Alembic registrado, y romperse en la primera migración real).
Aplicá la migración inicial para crear las tablas:

```bash
set FLASK_APP=run.py
flask db upgrade
```

Después, para tener contenido de ejemplo y poder ver la plataforma
funcionando, cargá los datos DEMO:

```bash
python seed.py
```

Todos los nombres, teléfonos y descripciones que carga este script son
**ficticios**, pensados únicamente para pruebas. Las 6 cuentas de
colaborador que crea comparten la contraseña `demo1234` (por ejemplo,
`carlos.demo@trabajitos.test` / `demo1234`) para poder loguearse y probar
el panel de colaborador sin tener que registrar una cuenta nueva.

### 5. Ejecutar localmente

```bash
python run.py
```

La aplicación queda disponible en `http://127.0.0.1:5000`.

> **Sobre cambios futuros al esquema de datos**: cualquier cambio a
> `app/models.py` necesita su propia migración, nunca se resuelve borrando
> la base de datos:
> ```bash
> set FLASK_APP=run.py
> flask db migrate -m "Descripción del cambio"
> flask db upgrade
> ```

### 6. Detener el servidor

Presionar `Ctrl + C` en la terminal donde está corriendo.

## Errores comunes

- **`ModuleNotFoundError: No module named 'flask'`**: el entorno virtual no
  está activado, o no se instalaron las dependencias (`pip install -r requirements.txt`).
- **La página carga sin estilos**: verificar que el servidor esté corriendo
  desde la carpeta `trabajitos/` (para que `static/` se sirva bien) y que no
  haya errores 404 en la consola del navegador para `style.css`.
- **`sqlite3.OperationalError: unable to open database file`**: la carpeta
  `instance/` no existe. Crearla manualmente (`mkdir instance`) y volver a
  correr `flask db upgrade`.
- **`sqlite3.OperationalError: no such table: users`** (u otra tabla):
  falta correr `flask db upgrade` (paso 4). El proyecto no crea las tablas
  automáticamente al arrancar.
- **Los datos DEMO no aparecen**: correr `python seed.py`. Si ya se había
  corrido antes, el script no vuelve a insertar (evita duplicados).
- **Cambié `SECRET_KEY` o `DATABASE_URL` y no pasa nada**: revisar que el
  archivo se llame exactamente `.env` (no `.env.example`) y que esté en la
  raíz de `trabajitos/`.

## Sobre las fuentes tipográficas (Anybody y Barlow)

El proyecto usa dos familias tipográficas, ambas de **Google Fonts** (SIL
Open Font License — gratuitas y con licencia adecuada para un sitio
público):

- **Anybody** (Expanded, ExtraBold 800) — reservada casi exclusivamente al
  wordmark "TRABAJITOS" en el header y el footer. Es una fuente variable;
  acá se usa una única instancia estática ancha (`font-stretch: 125%`) para
  darle presencia sin cargar el rango completo de la variable.
- **Barlow** (400, 500, 600, 700) — conduce el resto del sitio: navegación,
  títulos, párrafos, botones, formularios, tarjetas, precios y perfiles.

Los archivos `.woff2` están alojados localmente en `app/static/fonts/`
(descargados directamente desde `fonts.gstatic.com`, no de sitios de
terceros) para que el sitio no dependa de un CDN externo en tiempo de
ejecución:

```
app/static/fonts/
├── Anybody-Expanded-ExtraBold.woff2
├── Barlow-Regular.woff2
├── Barlow-Medium.woff2
├── Barlow-SemiBold.woff2
└── Barlow-Bold.woff2
```

Las reglas `@font-face` están al inicio de `app/static/css/style.css`. Si
alguno de estos archivos llegara a faltar, el navegador cae automáticamente
en la fuente de respaldo del sistema definida en `--font-wordmark` /
`--font-base`, así que el sitio nunca deja de ser legible.

## Sobre las imágenes

Las fotografías del PDF de referencia (moodboard) son solo inspiración
visual y **no se usan como contenido real** del sitio. Mientras no haya
fotografía propia, el Hero y las tarjetas usan bloques de color con la
paleta de marca. Los espacios donde debe ir fotografía real están marcados
en el código con comentarios (`hero__foto`, `tarjeta-servicio__imagen`).

## Sistema de fotografías (perfil, portafolio, moderación)

Los colaboradores suben su foto de perfil y fotos de trabajos realizados
(portafolio) directamente desde su dispositivo — nada de links externos.

- **Foto de perfil**: JPG/PNG/WEBP, máximo 5 MB. `/dashboard/perfil`.
- **Portafolio**: hasta 8 fotos, con descripción opcional. Hace falta un
  mínimo de **2 fotos aprobadas** para poder publicar un servicio nuevo
  (no afecta a servicios ya publicados). `/dashboard/portafolio`.
- Los archivos se guardan en `app/static/uploads/profile/` y
  `app/static/uploads/portfolio/` con un nombre generado (UUID), nunca con
  el nombre original. La base de datos solo guarda esa referencia, no el
  archivo — ver `app/services/image_storage.py`, pensado para poder
  reemplazarse por un backend en la nube más adelante sin tocar las rutas.
- Cada foto pasa por un estado de moderación (`pending` / `approved` /
  `flagged` / `rejected`, ver `app/models.py`). Hoy, sin ningún detector
  externo activo, una foto se marca `flagged` únicamente si coincide
  exactamente (hash SHA-256) con una foto ya subida por **otra** cuenta —
  el resto queda `approved` automáticamente. El resto de la arquitectura de
  moderación (hash perceptual, NSFW, detección de IA) está preparada pero
  inactiva a propósito: necesita aprobar una librería nueva primero (ver
  `app/services/image_quality_service.py` y `DESARROLLO.md`).
- Una cuenta con `account_status = "banned"` no puede iniciar sesión, y sus
  servicios y fotos dejan de mostrarse públicamente. Todavía no hay un
  panel de administración para banear cuentas — hoy es una operación manual
  directa sobre la base de datos, documentada como pendiente.

## Estado del proyecto

Ver [`DESARROLLO.md`](DESARROLLO.md) para el registro de decisiones,
funcionalidades completadas y pendientes.
