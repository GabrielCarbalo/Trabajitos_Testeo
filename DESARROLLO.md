# Registro de desarrollo — TRABAJITOS

Este archivo documenta decisiones técnicas, avances y pendientes reales del
proyecto, a medida que ocurren. Sirve como base para redactar después las
etapas de Desarrollo, Pruebas, Implementación y Mantenimiento del trabajo
académico.

## Sesión 5 — 2026-08-20

### Sistema de fotografías de colaborador: perfil real, portafolio y moderación

Ampliación grande, pedida como una lista de 30 partes. Resumen de lo
implementado — el detalle completo (con verificación en vivo de cada pieza)
quedó en el chat de esa sesión; acá va lo que hay que recordar después.

**Modelo de datos** (migración `0cfb1ba1a212`):
- `User.account_status` ("active" / "banned"). Se decidió ponerlo en `User`,
  no en `CollaboratorProfile` como sugería el pedido original: el login es
  una operación de `User`, así que el chequeo de baneo tiene que vivir ahí
  para poder cortar el acceso en el punto correcto (`app/routes/auth.py`).
- `CollaboratorProfile.foto_url` (texto) se **eliminó** y se reemplazó por
  `foto_filename` + `foto_hash` + `foto_moderation_status` + `foto_moderation_reason`.
- Tabla nueva `PortfolioImage`: `collaborator_profile_id`, `filename`,
  `descripcion`, `fecha_subida`, `moderation_status`, `moderation_reason`,
  `hash_exacto`, `hash_perceptual` (siempre NULL por ahora, ver abajo).
- La migración agrega columnas `NOT NULL` a tablas con datos existentes
  (las 6 cuentas DEMO): hizo falta agregar `server_default` a mano en el
  archivo de migración generado por Alembic — sin eso, `flask db upgrade`
  falla en cualquier base que ya tenga filas.

**Arquitectura nueva** (`app/services/`):
- `image_storage.py`: interfaz `ImageStorage` + `LocalImageStorage` (guarda
  en `app/static/uploads/<profile|portfolio>/<uuid>.<ext>`). El día que se
  quiera mover a un backend en la nube, solo hay que escribir una
  `CloudImageStorage` con los mismos 3 métodos.
- `uploads.py`: valida formato real (por bytes de cabecera — "magic
  numbers" — no por extensión ni Content-Type, ambos falseables) y tamaño
  (5 MB), y orquesta guardar + evaluar cada imagen. **Cero dependencias
  nuevas**: la detección de formato es Python puro.
- `image_quality_service.py`: hoy solo calcula hash SHA-256 (duplicados
  exactos). Deja preparadas (con flags `AI_IMAGE_CHECK` / `NSFW_CHECK` /
  `PERCEPTUAL_HASH_CHECK` en `False`) las funciones para hash perceptual,
  NSFW e IA — devuelven `None` ("no evaluado") hasta que se apruebe e
  instale una librería para cada una (ver la sección de dependencias
  propuestas en el reporte de esa sesión).

**Moderación implementada hoy**: una foto nueva se marca `flagged` (con un
motivo explicado, no acusatorio) únicamente si su hash exacto ya existe en
**otra** cuenta — subir la misma foto a tu propio perfil y portafolio, o
reemplazarla, nunca cuenta como sospechoso (se excluye explícitamente la
propia cuenta en la comparación). Si no hay coincidencia, la foto queda
`approved` automáticamente: es la decisión honesta dado que hoy no hay
ningún detector NSFW/IA activo — dejar todo en `pending` sin un proceso de
revisión manual real detrás habría sido peor (fotos nunca visibles).
Ningún chequeo automático puede banear una cuenta: eso queda para una
decisión manual (`account_status`), tal como pedía explícitamente el brief.

**Regla de confianza**: `CollaboratorProfile.puede_publicar_servicio`
exige 2 fotos de portafolio **aprobadas** antes de poder publicar un
servicio nuevo (`/dashboard/servicios/nuevo` bloquea con una pantalla
amigable si no se cumple, tanto en GET como revalidando en POST). No es
retroactivo: servicios ya publicados no se ocultan si después de aprobados
la cuenta queda con menos de 2 fotos.

**Perfil público y tarjetas**: `/colaborador/<id>` ahora muestra avatar
real (o inicial, nunca una foto ficticia de stock) y una galería de
portafolio (solo fotos `approved`) con vista ampliada mediante `<dialog>`
nativo — cero librerías de "lightbox". Las tarjetas de servicio (Home,
Explorar) usan la foto de perfil del colaborador como fondo cuando existe,
sin cambiar el layout de la tarjeta. Un colaborador baneado muestra un
aviso de cuenta suspendida en vez de su perfil, y sus servicios
desaparecen de Home/Explorar (join contra `User.account_status`, sin
tocar `Service.activo`, que sigue significando otra cosa).

**Patrón cultural** (`app/static/img/patron-mesoamericano.svg`): un único
patrón geométrico original (grid de rombos escalonados construido con
`<rect>`, sin librerías), descrito internamente como *"patrón geométrico
original inspirado en referencias visuales mesoamericanas Maya/Nahua"* —
no reproduce ningún glifo, calendario ni pieza arqueológica específica. Se
aplica vía CSS `mask-image` sobre un `::before` (así un mismo SVG se puede
recolorear con cualquier color de la paleta según la sección, sin duplicar
el archivo), a opacidad muy baja (0.045–0.07), en el Hero, el bloque CTA de
colaboradores y la cabecera del perfil público — inspirado explícitamente
en el tratamiento tono-sobre-tono de camisetas de selecciones (se revisó
el PDF de referencia para confirmarlo, incluyendo notar que varias de esas
imágenes traían marcas de agua de bancos de imágenes que no se usaron para
nada). `.contenedor` ahora tiene `position:relative; z-index:1` de forma
global para garantizar que el contenido quede siempre por encima del
patrón, sin tener que acordarse caso por caso.

**Dependencias nuevas**: ninguna. Todo lo implementado en esta sesión usa
solo la librería estándar de Python y las dependencias que ya estaban.

**Pendiente — necesita aprobación antes de instalarse** (no implementado a
propósito, ver Parte 29 del pedido original):
- Hash perceptual (detectar copias recortadas/comprimidas, no solo
  idénticas): candidata `imagehash` (MIT, depende de Pillow — que tampoco
  está instalado hoy).
- Detección de contenido NSFW: sin decidir todavía; las opciones locales
  razonables (ej. NudeNet vía ONNX Runtime) son más livianas que las
  basadas en TensorFlow, pero igual agregan dependencias no triviales.
- Detección de imágenes generadas por IA: hoy no hay una opción local
  madura y confiable — se recomienda no instalar nada todavía en esta
  categoría.

**Verificado en el navegador y con pruebas HTTP directas** (no solo
revisado el código): registro colaborador → bloqueo de "publicar servicio"
sin portafolio → subida de 2 fotos → desbloqueo → publicación exitosa;
rechazo de archivo no-imagen (texto con extensión .jpg) y de archivo
>5 MB; duplicado exacto entre dos cuentas distintas → `flagged` con motivo
claro; la misma foto reusada dentro de la propia cuenta (perfil + dos
portafolios) → nunca marcada; límite de 8 fotos alcanzado y bloqueado en
la 9na; eliminar una foto propia; intento de eliminar una foto ajena →
403; acceso sin sesión → redirect a login; cuenta baneada → login
bloqueado con mensaje claro, sesión ya abierta cortada en el siguiente
request, servicio desaparece de Explorar, perfil público muestra aviso de
suspensión. Responsive verificado en mobile (375px) y confirmado sin
overflow. Todas las cuentas y fotos de prueba se borraron al terminar
(incluyendo los archivos en `app/static/uploads/`), dejando la base como
estaba.

### Fase 7: revisión responsive dedicada en tablet (768px)

Hasta ahora cada fase se había probado en desktop (1280px) y mobile
(375px), pero no en un ancho de tablet dedicado. Se revisaron a 768px:
Home, Explorar (con filtros), Registro (elección cliente/colaborador),
Login, formulario de publicar/editar servicio, panel de colaborador,
editar perfil y el perfil público de un colaborador.

**Resultado: sin hallazgos.** En todas las páginas `scrollWidth` coincide
con `clientWidth` (sin scroll horizontal), el header se mantiene en una
sola fila sin superposición, los grids de 2 columnas (elección de tipo de
usuario, categoría/modalidad del formulario de servicio, foto+info del
perfil) tienen suficiente espacio para no sentirse apretados, y el listado
de filtros de Explorar se envuelve (`flex-wrap`) prolijamente en vez de
desbordar. No hizo falta ningún ajuste de CSS.

### Fase 8: checklist de pruebas end-to-end

Se corrió de punta a punta, en una sola sesión de navegador y en orden, el
checklist completo pedido en el brief original. Cuentas de prueba nuevas
(`pedro.checklist@trabajitos.test` / cliente, `laura.checklist@trabajitos.test`
/ colaboradora) para no depender de las cuentas DEMO ya existentes:

| # | Caso | Resultado |
|---|---|---|
| 1 | Registro cliente | ✅ Redirige a Home, mensaje de bienvenida, CTA correcto |
| 2 | Registro colaborador | ✅ Redirige al panel, perfil vacío con invitación a completarlo |
| 3 | Logout | ✅ Sesión cerrada, mensaje de confirmación |
| 4 | Login incorrecto | ✅ Mensaje de error genérico, no filtra cuál dato falló |
| 5 | Login correcto | ✅ Redirige a Home con saludo, CTA cambia a "Ir a mi panel" |
| 6 | Publicar servicio | ✅ Aparece de inmediato en el panel |
| 7 | Editar servicio | ✅ Cambio de precio reflejado correctamente |
| 8 | Editar servicio de otro usuario | ✅ 403 (Laura no pudo editar un servicio de Carlos) |
| 9 | Explorar servicios | ✅ Lista los 7 servicios activos (6 demo + el de la cuenta de prueba) |
| 10 | Buscar | ✅ `q=guitarra` devuelve exactamente el resultado esperado |
| 11 | Filtrar | ✅ `categoria=limpieza&modalidad=hora` combinados, 1 resultado correcto |
| 12 | Abrir perfil | ✅ Perfil público de Carlos con sus servicios |
| 13 | Contacto por WhatsApp | ✅ Link `https://wa.me/50370000001` generado correctamente |

**13/13 casos pasaron.** Sin errores de servidor durante toda la corrida.
Las cuentas y el servicio de prueba se borraron al terminar; la base
quedó con exactamente los 6 colaboradores DEMO originales.

**Con esto se cierran las Fases 2 a 8 del plan de trabajo original.** Lo
único pendiente documentado es de baja prioridad (paginación de
`/explorar`, decisión ya tomada de dejar la contraseña compartida de las
cuentas DEMO) — ver "Pendiente" en la sesión anterior.

### Revisión Fable de las Fases 4-6 y correcciones aplicadas

Pedimos una revisión de Fable enfocada en seguridad, validación y calidad
de código de las Fases 4-6 (no repitió las pruebas funcionales, que ya se
habían hecho a mano). Encontró 2 bloqueantes y varios importantes/menores;
se corrigieron todos salvo la paginación de `/explorar` (queda como mejora
futura, no urgente con 7 servicios en la base):

**Bloqueantes:**
- **Open redirect en login** (`auth.py`): `next=//evil.com` pasaba el
  chequeo `startswith("/")` porque los navegadores tratan `//host` como
  protocol-relative. Se reemplazó por `_es_redireccion_segura()`, que usa
  `urlsplit()` para confirmar que no haya ni esquema ni host. Verificado:
  `next=//evil.com` ahora redirige a Home, no a un sitio externo.
- **`float("nan")`/`float("inf")` pasaban la validación de precio**
  (`dashboard.py`): `nan <= 0` es `False`, así que un precio inválido se
  guardaba. Se agregó `math.isfinite()` antes de aceptar el valor, más un
  tope máximo (`$999,999.99`, acorde a `Numeric(8,2)`). Verificado con
  POST directo (bypaseando el `<input type="number">`): `precio=nan` y
  `precio=inf` devuelven 400 y no crean el registro.

**Importantes:**
- **`db.create_all()` convivía con Flask-Migrate**: en una instalación
  nueva, `create_all()` creaba las tablas sin dejar registro de versión de
  Alembic, y la primera migración real iba a fallar por "la tabla ya
  existe". Se quitó `create_all()` de `create_app()`; se regeneró la
  migración inicial contra una base vacía (ahora sí contiene los `CREATE
  TABLE` reales) y `flask db upgrade` quedó documentado en el README como
  paso obligatorio de instalación (antes era automático).
- **Sin límites de longitud en los formularios**: se agregó validación de
  longitud máxima en servidor (nombre, correo, título, disponibilidad,
  teléfono, link de foto) más `maxlength` en el HTML como refuerzo. Antes,
  SQLite ignoraba los límites de `VARCHAR` del modelo; iba a fallar recién
  al migrar a PostgreSQL.
- **Tarjeta de servicio duplicada**: `perfil_colaborador.html` reimplementaba
  a mano la misma tarjeta de `partials/service_card.html` (con su propio
  diccionario de modalidades repetido). Se agregó `Service.modalidad_legible`
  (property del modelo) para no repetir ese diccionario en 3 templates, y
  se parametrizó `service_card.html` con la variable `ocultar_datos_colaborador`
  para que perfil_colaborador.html lo reutilice en vez de duplicarlo.

**Menores:**
- Race condition en registro con correos duplicados simultáneos: el commit
  ahora está en un `try/except IntegrityError` (la constraint UNIQUE de la
  base es la defensa real; el chequeo previo es solo para el mensaje de
  error amigable en el caso común).
- **Logout por GET → POST**: un `<a href="/logout">` permitía que cualquier
  página externa desloguee al usuario con solo cargar la URL (o el
  prefetch del navegador). Ahora es un `<form method="post">` con CSRF,
  en header y footer. Verificado: `GET /logout` devuelve 405.
- Validación de teléfono reforzada con regex (`^\+?[\d ]{8,20}$`) en vez
  de un chequeo manual que dejaba pasar casos raros.
- `foto_url` ahora exige `https://` (antes aceptaba `http://`, riesgo de
  mixed content si el sitio se sirve por HTTPS).
- Búsqueda de `/explorar` escapa `%` y `_` antes de armar el patrón de
  `ILIKE`, para que buscar un texto con esos caracteres no se comporte
  como un wildcard.
- N+1 query en el panel de colaborador resuelta con `joinedload`.
- Defensa extra en `dashboard.before_request`: si por algún motivo un
  colaborador no tuviera `perfil_colaborador` (no debería pasar dado cómo
  se registra hoy), devuelve 403 en vez de un 500.

**Verificado en el navegador** después de aplicar todo: home, login,
logout (por POST), intento de open redirect, publicar servicio válido,
intento de publicar con `precio=nan`/`precio=inf` (ambos rechazados sin
crear el registro), perfil público con la tarjeta refactorizada (sin
duplicar "Ver perfil"), y `/explorar` con la tarjeta original intacta (7
servicios, cada uno con su botón "Ver perfil"). Sin errores de servidor.
Los datos de prueba se limpiaron al terminar.

## Sesión 3 — 2026-08-19

### Fase 6 completa: Exploración (listado, filtros, perfil público, WhatsApp)

- **`/explorar`**: listado real conectado a la base de datos, con búsqueda
  de texto libre (título/descripción, `ILIKE`) y filtros combinables por
  categoría, modalidad y precio máximo — todos opcionales y por
  querystring (`GET`), así que la URL con filtros se puede compartir o
  recargar. Un valor de precio no numérico se ignora en vez de romper la
  búsqueda. Estado vacío ("No encontramos trabajitos...") cuando ningún
  servicio matchea. Reutiliza `partials/service_card.html`, el mismo
  componente de tarjeta del Home.
- **`/colaborador/<id>`**: perfil público real — foto (o inicial del
  nombre como placeholder si no cargó una), descripción, lista de sus
  servicios activos, y botón **"Contactar por WhatsApp"** que solo aparece
  si el colaborador cargó un teléfono. El link se arma con
  `_link_whatsapp()` en `app/routes/main.py`, que sanitiza el teléfono
  guardado (le saca todo lo que no sea dígito) para armar una URL
  `https://wa.me/<dígitos>` válida. Colaborador inexistente → 404.
- El riel de categorías y el buscador del Hero (construidos en la Fase 3)
  ya apuntaban a `/explorar?categoria=<slug>` y `/explorar?q=<texto>`
  respectivamente — no hizo falta tocarlos, solo dejaron de ser enlaces a
  una página "Próximamente".

**Verificado en el navegador**: `/explorar` sin filtros muestra los 6
servicios demo; filtro por categoría (`jardineria`) devuelve 1 resultado
con el singular/plural correcto en el contador; búsqueda de texto
(`q=perros`) combinada con precio máximo (`precio_max=10`) devuelve
exactamente el resultado esperado; una búsqueda sin coincidencias muestra
el estado vacío; perfil público de un colaborador demo muestra sus datos y
un link de WhatsApp bien formado (`https://wa.me/50370000004` a partir de
`+503 7000 0000`); perfil de un id inexistente → 404 con página de marca.
Sin scroll horizontal en mobile (375px), filtros se apilan correctamente.
Sin errores de servidor.

**Con esto se cierra el flujo funcional completo del MVP** descrito en el
brief original (seguí en la próxima entrada con lo que queda: Fase 7
responsive fino, Fase 8 checklist de pruebas formal).

### Fase 5 completa: Colaboradores y servicios (dashboard funcional)

El panel de colaborador (`/dashboard/`) dejó de ser un placeholder:

- **Panel principal**: resumen del perfil (descripción, WhatsApp) y lista
  de los servicios publicados, cada uno con su categoría, precio, modalidad
  y disponibilidad. Si el perfil está incompleto o no hay servicios, se
  muestra una invitación a completarlos en vez de una sección vacía.
- **Editar perfil** (`/dashboard/perfil`): descripción, WhatsApp y link a
  foto (los tres opcionales salvo la descripción). Validación en servidor:
  el teléfono solo acepta números/espacios/"+", y el link de foto tiene que
  empezar con `http(s)://`.
- **Publicar servicio** (`/dashboard/servicios/nuevo`) y **editar servicio**
  (`/dashboard/servicios/<id>/editar`) comparten el mismo template de
  formulario (`dashboard/servicio_form.html`). Validación en servidor:
  título/descripción/disponibilidad no vacíos, categoría y modalidad
  válidas, precio numérico mayor a 0.
- **Verificación de dueño**: `_obtener_servicio_propio()` en
  `app/routes/dashboard.py` comprueba que el servicio a editar pertenezca
  al colaborador logueado (`servicio.collaborator_profile_id == current_user.perfil_colaborador.id`).
  Si no, 403 (no 404), para no filtrar si el id existe o no. Esto evita que
  un colaborador edite servicios de otro cambiando el id en la URL.

**Verificado en el navegador** con una cuenta DEMO real
(`carlos.demo@trabajitos.test`): el panel mostró correctamente su perfil y
su servicio existente; publiqué un servicio nuevo (apareció al instante en
la lista); lo edité (cambio de precio reflejado); confirmé que intentar
editar el servicio de otro colaborador (id de otra cuenta) devuelve 403;
probé una validación de teléfono inválida (rechazada con mensaje claro) y
después guardé un teléfono válido (aceptado). Sin errores de consola
reales (los 403/400 que aparecieron eran los que yo mismo provoqué a
propósito para probar la protección). Sin scroll horizontal en mobile
(375px). Los datos de prueba creados durante la verificación se borraron
al terminar, dejando la base DEMO como estaba.

### Fase 4 completa: Usuarios (registro, login, logout, protección de rutas)

- **Registro** (`/registro`): formulario mínimo (nombre, correo, contraseña)
  con elección explícita entre "Necesito contratar" (cliente) y "Quiero
  ofrecer servicios" (colaborador) mediante radios accesibles con
  apariencia de tarjeta. Validación en servidor (correo con formato válido,
  contraseña de al menos 8 caracteres, correo no duplicado, tipo de usuario
  válido) — nunca se confía solo en los `required` del HTML. Si el tipo
  elegido es colaborador, se crea de una vez un `CollaboratorProfile` vacío,
  para completarlo después desde el panel (Fase 5).
- **Login** (`/login`): valida contra el hash de la contraseña
  (`User.check_password`), con mensaje de error genérico ("Correo o
  contraseña incorrectos") para no revelar cuál de los dos datos falló.
  Soporta `?next=` para volver a la página que exigió login, validando que
  sea una ruta interna (empiece con "/") para evitar un *open redirect*.
- **Logout** (`/logout`): cierra la sesión de Flask-Login.
- **Protección de rutas**: el blueprint completo de `dashboard` exige sesión
  iniciada Y cuenta de tipo colaborador (`before_request` + `login_required`
  en `app/routes/dashboard.py`). Un cliente que intenta entrar recibe 403.
- **CSRF**: se agregó Flask-WTF (`CSRFProtect`) a nivel de toda la app.
  Los formularios de registro/login incluyen `{{ csrf_token() }}`; se
  verificó que un POST sin ese token es rechazado con 400.
- **Páginas de error con marca**: 403 y 404 ya no muestran la página en
  blanco por defecto de Flask, sino una vista consistente con el resto del
  sitio (`app/templates/error.html`).
- **UI consciente de sesión**: el header y el footer cambian según haya o
  no sesión activa (nombre del usuario, "Mi panel", "Cerrar sesión" vs.
  "Iniciar sesión"/"Crear cuenta"); el CTA de colaboradores en la Home
  apunta al panel en vez de al registro si ya sos colaborador logueado.
- Se agregaron mensajes flash (éxito/error/info) renderizados en
  `base.html`, con estilos propios (`.flash--success/error/info`).

**Verificado en el navegador** (no solo revisado el código): registro como
colaborador → login automático → redirección al panel con mensaje de
bienvenida; registro como cliente → redirección a Home (no al panel);
login con contraseña incorrecta → mensaje de error, sin revelar la cuenta;
logout; acceso de un cliente a `/dashboard/` → 403 con página de marca;
ruta inexistente → 404 con página de marca; usuario sin sesión que intenta
entrar a `/dashboard/` → redirigido a `/login?next=/dashboard/` y, tras
loguearse, devuelto exactamente ahí. Las cuentas de prueba usadas para
verificar se borraron de la base de datos al terminar.

### Pendiente (próximas fases)

- Fase 7: revisión responsive fina en tablet (ya se probó desktop y mobile
  en cada fase, pero falta un pase dedicado a anchos intermedios).
- Fase 8: checklist de pruebas formal end-to-end (la lista completa de
  section 39 del brief: registro cliente/colaborador, login
  correcto/incorrecto, logout, publicar/editar servicio, intentar editar
  servicio ajeno, explorar, buscar, filtrar, abrir perfil, contacto por
  WhatsApp). La mayoría de estos casos ya se probaron sueltos durante el
  desarrollo de cada fase; falta correrlos todos juntos como checklist y
  dejarlo documentado formalmente.
- Se decidió (sesión 3) dejar la contraseña compartida `demo1234` de las
  cuentas DEMO tal cual, documentada como cuenta de prueba a propósito
  (ver README y encabezado de `seed.py`) — no es una cuenta real.

## Sesión 2 — 2026-08-18

### Cambio de sistema tipográfico: Horizon/Banburi → Anybody/Barlow

Se decidió abandonar Horizon y Banburi (nunca se consiguieron los archivos)
para garantizar que el proyecto sea 100% gratuito y con licencia adecuada
para publicarse. Se reemplazaron por dos familias de Google Fonts (SIL Open
Font License):

- **Anybody**, instancia estática Expanded/ExtraBold (`font-weight: 800`,
  `font-stretch: 125%`), exclusiva para el wordmark "TRABAJITOS".
- **Barlow**, pesos 400/500/600/700, para el resto del sitio.

Los `.woff2` se descargaron directamente de `fonts.gstatic.com` (servidor
oficial de Google Fonts, no un tercero) y quedaron alojados en
`app/static/fonts/`, sin depender de un CDN externo en tiempo de ejecución.
No se modificó ningún color de la paleta ni el layout de ningún componente;
el cambio quedó acotado a `@font-face`, las variables `--font-wordmark` /
`--font-base`, y los ajustes de `font-stretch`/`letter-spacing`/`line-height`
del wordmark en `.header__logo` y `.footer__logo`.

## Sesión 1 — 2026-08-18

### Auditoría inicial

- No existía carpeta de proyecto previa; se partió de cero.
- El PDF de referencia (`Diseño de Pagina WebTrabajitos.pdf`) tiene 5
  páginas reales (el conteo automático inicial de 124 páginas era
  incorrecto; se verificó renderizando el PDF con PyMuPDF).
- Se revisaron las 5 páginas del moodboard: anuncios editoriales retro
  (Mitsubishi, Sony), ejemplos de catálogo/grid (Apple Store, "SearchYou"),
  bloques editoriales grandes (Carhartt, Camp Flog Gnaw), carrusel horizontal
  "ARCHIVES" y la paleta de colores oficial confirmada sobre foto de cancha
  de tenis.
- No se encontraron los archivos de las fuentes Horizon ni Banburi en el
  equipo (se buscó en Documentos, Descargas, Escritorio y el proyecto). Se
  documentó en el README qué archivos se necesitan y dónde colocarlos.

### Decisiones técnicas

- **Arquitectura**: Flask con patrón *application factory* (`create_app()`
  en `app/__init__.py`), blueprints separados por área (`main`, `auth`,
  `dashboard`).
- **Modelos**: `User`, `CollaboratorProfile` (1:1 con `User`), `Category`,
  `Service`. Se decidió **no crear una tabla `availability` separada**: la
  disponibilidad de un servicio es un campo de texto simple en `Service`.
  Si más adelante se necesitan horarios estructurados o calendarios, ese es
  el punto natural para introducir una tabla propia.
- **Autenticación**: se preparó Flask-Login (modelo `User` con `UserMixin`,
  `password_hash` con Werkzeug) pero la implementación completa de
  registro/login queda para la Fase 4, según el plan de trabajo acordado.
- **Tipografía**: sin archivos de Horizon/Banburi disponibles, se definieron
  variables CSS (`--font-wordmark`, `--font-base`) con stacks de respaldo
  del sistema. Las reglas `@font-face` ya apuntan a `static/fonts/` para que
  sea un simple reemplazo de archivos cuando estén disponibles.
- **Imágenes**: no se usó fotografía de stock sin licencia conocida. El Hero
  y las tarjetas de servicio usan bloques de color de la paleta de marca en
  los espacios donde eventualmente irá fotografía real.

### Funcionalidades completadas

- Estructura base del proyecto Flask (config, modelos, blueprints, templates).
- Sistema visual completo en `app/static/css/style.css`: variables de
  colores/tipografía/espaciado/radios/sombras, header responsive con menú
  mobile, Hero editorial con buscador, riel horizontal de categorías
  (inspirado en el carrusel "ARCHIVES" del moodboard), grid de servicios
  destacados con datos reales de la base de datos, bloque CTA para
  colaboradores, footer.
- Modelos de datos y conexión a SQLite vía `DATABASE_URL`.
- Script `seed.py` con datos DEMO explícitamente ficticios (6 categorías, 6
  colaboradores con un servicio cada uno).
- Páginas placeholder ("en construcción") para Explorar, Login, Registro,
  Dashboard y Perfil de colaborador, para que la navegación del sitio no
  tenga enlaces rotos mientras esas fases no se implementan.
- Verificado en navegador: la Home carga con los datos demo, no hay errores
  de consola salvo los 404 esperados de las fuentes faltantes, no hay
  scroll horizontal en mobile (375px) y el menú hamburguesa funciona
  correctamente (toggle de `aria-expanded` y clase `header__nav--abierto`).

### Pendiente (próximas fases, según el plan acordado)

- **Fase 4 — Usuarios**: registro (elegir cliente/colaborador), login,
  logout, protección de rutas.
- **Fase 5 — Colaboradores y servicios**: edición de perfil, publicar y
  editar servicio, dashboard funcional.
- **Fase 6 — Exploración**: listado real en `/explorar` con búsqueda y
  filtros (categoría, modalidad, precio), página de detalle del colaborador
  con botón de contacto por WhatsApp (`https://wa.me/...`).
- **Fase 7 — Responsive**: revisión fina en tablet además de mobile/desktop.
- **Fase 8 — Pruebas**: checklist funcional completo (registro, login,
  publicar/editar servicio, permisos, búsqueda, contacto).
- **Fase 9 — Revisión Fable/Opus**: revisión de arquitectura, UX, fidelidad
  visual y deuda técnica antes de avanzar a la Fase 4.
- Sustituir los bloques de color del Hero y las tarjetas por fotografía real
  cuando esté disponible.
- Incorporar los archivos de fuente Horizon y Banburi cuando se entreguen.

### Errores encontrados y corregidos

- Ninguno bloqueante en esta sesión. El único hallazgo fue que la
  herramienta de lectura de PDF reportó un conteo de páginas incorrecto
  (124 en vez de 5); se resolvió renderizando el PDF directamente con
  PyMuPDF para confirmar el contenido real.

### Revisión Fable (Fase 9) y correcciones aplicadas

Se pidió una revisión de arquitectura/UX/seguridad con Fable sobre las
Fases 2-3. No encontró nada bloqueante. Se aplicaron todas las correcciones
"importantes" y la mayoría de las "menores" antes de continuar:

- **Migraciones**: se agregó Flask-Migrate (`migrations/`) para poder
  alterar el esquema en las próximas fases sin perder datos. `db.create_all()`
  se mantiene en `create_app()` solo como bootstrap de primera ejecución;
  los cambios de esquema futuros deben hacerse con `flask db migrate` /
  `flask db upgrade`, no editando esa función.
- **Integridad de datos**: se agregaron `CheckConstraint` en
  `User.tipo_usuario` y `Service.modalidad`, e índices en
  `Service.collaborator_profile_id` y `Service.category_id` (se usarán en
  los filtros de Explorar, Fase 6). Esto requirió recrear la base de datos
  local y volver a correr `seed.py`.
- **Accesibilidad del menú mobile**: los enlaces de navegación quedaban
  tabulables aunque el menú estuviera visualmente cerrado. Se corrigió con
  el atributo `inert` (se activa/desactiva según si el botón hamburguesa es
  visible), se agregó cierre con `Escape`, y el texto del botón ahora
  alterna entre "Abrir menú" / "Cerrar menú".
- **Código**: `datetime.utcnow()` (deprecado) reemplazado por
  `datetime.now(timezone.utc)`; `User.query.get()` (deprecado) reemplazado
  por `db.session.get()`; N+1 queries en la Home resueltas con
  `joinedload`; `!important` en `.header__cta` resuelto con especificidad
  de selector; año del footer ahora viene de un `context_processor` en vez
  de estar hardcodeado; `role="region"` agregado al riel de categorías.
- **`.env.example`**: se corrigió una inconsistencia donde `DATABASE_URL`
  con ruta relativa podía generar un archivo SQLite distinto al que usa
  `config.py` por defecto. Ahora queda comentada para desarrollo, y
  `FLASK_ENV` (removido en Flask 2.3+) se reemplazó por `FLASK_DEBUG`,
  conectado de verdad en `run.py`.

**Pendiente, documentado pero no implementado todavía** (decisiones que
corresponden a la Fase 4, cuando exista login real):
- Las cuentas DEMO de `seed.py` comparten la contraseña `demo1234`. Cuando
  se implemente login, hay que decidir cómo tratarlas (marcarlas como demo,
  desactivar su login, o cambiarles la contraseña) para que no queden como
  cuentas reales con contraseña conocida.
- Se evaluó agregar un campo de zona/ubicación a `CollaboratorProfile` para
  facilitar filtros geográficos, pero no está en el alcance del MVP descrito
  (los filtros mínimos pedidos son categoría y disponibilidad), así que se
  deja fuera por ahora para no adelantar funcionalidad no solicitada.
