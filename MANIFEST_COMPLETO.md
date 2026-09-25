# MANIFEST COMPLETO

Una fila por archivo exportado (copias byte a byte idénticas a las originales).

| # | Ruta original | Ruta exportada | Área | Tipo | Descripción |
|---|---|---|---|---|---|
| 1 | `.env.example` | `TRABAJITOS-CODIGO-COMPLETO/.env.example` | Configuración | Configuración | Ejemplo de variables de entorno (SECRET_KEY, DATABASE_URL, FLASK_DEBUG); sin secretos reales. |
| 2 | `.gitignore` | `TRABAJITOS-CODIGO-COMPLETO/.gitignore` | Configuración | Configuración | Reglas de Git del proyecto (venv, .env, instance/*.db, uploads). |
| 3 | `DESARROLLO.md` | `TRABAJITOS-CODIGO-COMPLETO/DESARROLLO.md` | Documentación | Documentación | Registro de desarrollo del proyecto (decisiones, fases, pruebas). |
| 4 | `README.md` | `TRABAJITOS-CODIGO-COMPLETO/README.md` | Documentación | Documentación | README original del proyecto: instalación, ejecución y estructura. |
| 5 | `app/__init__.py` | `TRABAJITOS-CODIGO-COMPLETO/app/__init__.py` | Backend | Código fuente | Application factory de Flask: extensiones, blueprints, manejadores de error, helpers de plantillas. |
| 6 | `app/config.py` | `TRABAJITOS-CODIGO-COMPLETO/app/config.py` | Configuración | Configuración | Configuración leída de variables de entorno (SECRET_KEY, DATABASE_URL, tope de subida). |
| 7 | `app/models.py` | `TRABAJITOS-CODIGO-COMPLETO/app/models.py` | Backend | Código fuente | Models (POO): User, CollaboratorProfile, PortfolioImage, Category, Service y excepciones de dominio. |
| 8 | `app/routes/__init__.py` | `TRABAJITOS-CODIGO-COMPLETO/app/routes/__init__.py` | Backend | Código fuente | Marca app/routes como paquete. |
| 9 | `app/routes/auth.py` | `TRABAJITOS-CODIGO-COMPLETO/app/routes/auth.py` | Backend | Código fuente | Controller: registro, login y logout. |
| 10 | `app/routes/dashboard.py` | `TRABAJITOS-CODIGO-COMPLETO/app/routes/dashboard.py` | Backend | Código fuente | Controller del panel del colaborador: perfil, portafolio y servicios. |
| 11 | `app/routes/main.py` | `TRABAJITOS-CODIGO-COMPLETO/app/routes/main.py` | Backend | Código fuente | Controller público: Home, Explorar y perfil público del colaborador. |
| 12 | `app/services/__init__.py` | `TRABAJITOS-CODIGO-COMPLETO/app/services/__init__.py` | Backend | Código fuente | Marca app/services como paquete. |
| 13 | `app/services/image_quality_service.py` | `TRABAJITOS-CODIGO-COMPLETO/app/services/image_quality_service.py` | Backend | Código fuente | Señales de calidad/moderación de imágenes (hash exacto; NSFW/IA/perceptual preparados e inactivos). |
| 14 | `app/services/image_storage.py` | `TRABAJITOS-CODIGO-COMPLETO/app/services/image_storage.py` | Backend | Código fuente | Almacenamiento de imágenes (interfaz + LocalImageStorage con nombres UUID). |
| 15 | `app/services/uploads.py` | `TRABAJITOS-CODIGO-COMPLETO/app/services/uploads.py` | Backend | Código fuente | Validación (formato real por bytes, tamaño) y orquestación de subida de imágenes. |
| 16 | `app/static/css/style.css` | `TRABAJITOS-CODIGO-COMPLETO/app/static/css/style.css` | Frontend | Código fuente | Sistema visual completo de TRABAJITOS (paleta, tipografías, componentes, responsive, patrón). |
| 17 | `app/static/fonts/Anybody-Expanded-ExtraBold.woff2` | `TRABAJITOS-CODIGO-COMPLETO/app/static/fonts/Anybody-Expanded-ExtraBold.woff2` | Assets | Asset | Fuente Anybody (wordmark), self-hosted, Google Fonts (OFL). |
| 18 | `app/static/fonts/Barlow-Bold.woff2` | `TRABAJITOS-CODIGO-COMPLETO/app/static/fonts/Barlow-Bold.woff2` | Assets | Asset | Fuente Barlow 700 (interfaz), self-hosted, Google Fonts (OFL). |
| 19 | `app/static/fonts/Barlow-Medium.woff2` | `TRABAJITOS-CODIGO-COMPLETO/app/static/fonts/Barlow-Medium.woff2` | Assets | Asset | Fuente Barlow 500 (interfaz), self-hosted, Google Fonts (OFL). |
| 20 | `app/static/fonts/Barlow-Regular.woff2` | `TRABAJITOS-CODIGO-COMPLETO/app/static/fonts/Barlow-Regular.woff2` | Assets | Asset | Fuente Barlow 400 (interfaz), self-hosted, Google Fonts (OFL). |
| 21 | `app/static/fonts/Barlow-SemiBold.woff2` | `TRABAJITOS-CODIGO-COMPLETO/app/static/fonts/Barlow-SemiBold.woff2` | Assets | Asset | Fuente Barlow 600 (interfaz), self-hosted, Google Fonts (OFL). |
| 22 | `app/static/img/patron-mesoamericano.svg` | `TRABAJITOS-CODIGO-COMPLETO/app/static/img/patron-mesoamericano.svg` | Assets | Asset | Patrón geométrico original (máscara SVG) usado como textura sutil de fondo. |
| 23 | `app/static/js/main.js` | `TRABAJITOS-CODIGO-COMPLETO/app/static/js/main.js` | Frontend | Código fuente | JavaScript vanilla: menú móvil y vista ampliada (lightbox) del portafolio. |
| 24 | `app/templates/auth/login.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/auth/login.html` | Frontend | Código fuente | View: formulario de inicio de sesión. |
| 25 | `app/templates/auth/registro.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/auth/registro.html` | Frontend | Código fuente | View: formulario de registro (Cliente / Colaborador). |
| 26 | `app/templates/base.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/base.html` | Frontend | Código fuente | Plantilla base: head, header, mensajes flash, footer, scripts. |
| 27 | `app/templates/dashboard/editar_perfil.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/dashboard/editar_perfil.html` | Frontend | Código fuente | View: edición de perfil del colaborador con foto de perfil. |
| 28 | `app/templates/dashboard/panel.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/dashboard/panel.html` | Frontend | Código fuente | View: panel del colaborador (perfil, portafolio, servicios). |
| 29 | `app/templates/dashboard/portafolio.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/dashboard/portafolio.html` | Frontend | Código fuente | View: administración del portafolio de trabajos. |
| 30 | `app/templates/dashboard/portafolio_requerido.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/dashboard/portafolio_requerido.html` | Frontend | Código fuente | View: aviso de fotos de portafolio necesarias para publicar. |
| 31 | `app/templates/dashboard/servicio_form.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/dashboard/servicio_form.html` | Frontend | Código fuente | View: formulario de publicar/editar servicio. |
| 32 | `app/templates/en_construccion.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/en_construccion.html` | Frontend | Código fuente | View genérica para secciones aún no implementadas. |
| 33 | `app/templates/error.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/error.html` | Frontend | Código fuente | View de errores HTTP (403, 404, 413). |
| 34 | `app/templates/explorar.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/explorar.html` | Frontend | Código fuente | View: catálogo con búsqueda y filtros. |
| 35 | `app/templates/index.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/index.html` | Frontend | Código fuente | View: Home (hero, categorías, servicios destacados, CTA). |
| 36 | `app/templates/partials/footer.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/partials/footer.html` | Frontend | Código fuente | Parcial: pie de página. |
| 37 | `app/templates/partials/header.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/partials/header.html` | Frontend | Código fuente | Parcial: encabezado y navegación. |
| 38 | `app/templates/partials/service_card.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/partials/service_card.html` | Frontend | Código fuente | Parcial: tarjeta de servicio reutilizable. |
| 39 | `app/templates/perfil_colaborador.html` | `TRABAJITOS-CODIGO-COMPLETO/app/templates/perfil_colaborador.html` | Frontend | Código fuente | View: perfil público del colaborador (portafolio y servicios). |
| 40 | `migrations/README` | `TRABAJITOS-CODIGO-COMPLETO/migrations/README` | Base de datos / Migraciones | Migración | README generado por Flask-Migrate/Alembic. |
| 41 | `migrations/alembic.ini` | `TRABAJITOS-CODIGO-COMPLETO/migrations/alembic.ini` | Base de datos / Migraciones | Migración | Configuración de Alembic. |
| 42 | `migrations/env.py` | `TRABAJITOS-CODIGO-COMPLETO/migrations/env.py` | Base de datos / Migraciones | Migración | Entorno de ejecución de migraciones Alembic. |
| 43 | `migrations/script.py.mako` | `TRABAJITOS-CODIGO-COMPLETO/migrations/script.py.mako` | Base de datos / Migraciones | Migración | Plantilla de nuevas migraciones. |
| 44 | `migrations/versions/0cfb1ba1a212_fotografias_de_perfil_portafolio_y_.py` | `TRABAJITOS-CODIGO-COMPLETO/migrations/versions/0cfb1ba1a212_fotografias_de_perfil_portafolio_y_.py` | Base de datos / Migraciones | Migración | Migración: fotos de perfil, portafolio, moderación y account_status. |
| 45 | `migrations/versions/e1a2ec9cfcff_modelos_iniciales_users_collaborator_.py` | `TRABAJITOS-CODIGO-COMPLETO/migrations/versions/e1a2ec9cfcff_modelos_iniciales_users_collaborator_.py` | Base de datos / Migraciones | Migración | Migración inicial: users, collaborator_profiles, categories, services. |
| 46 | `requirements.txt` | `TRABAJITOS-CODIGO-COMPLETO/requirements.txt` | Configuración | Configuración | Dependencias Python con versiones fijas. |
| 47 | `run.py` | `TRABAJITOS-CODIGO-COMPLETO/run.py` | Backend | Código fuente | Entrypoint local: crea la app y la ejecuta (python run.py). |
| 48 | `seed.py` | `TRABAJITOS-CODIGO-COMPLETO/seed.py` | Scripts | Script | Script que carga datos DEMO ficticios (categorías, 6 colaboradores y servicios). |
| 49 | `tests/__init__.py` | `TRABAJITOS-CODIGO-COMPLETO/tests/__init__.py` | Tests | Test | Marca tests/ como paquete. |
| 50 | `tests/base.py` | `TRABAJITOS-CODIGO-COMPLETO/tests/base.py` | Tests | Test | Base común de las pruebas (app + SQLite en memoria). |
| 51 | `tests/test_registro.py` | `TRABAJITOS-CODIGO-COMPLETO/tests/test_registro.py` | Tests | Test | Pruebas unittest del módulo Registro de usuarios. |
| 52 | `tests/test_servicios.py` | `TRABAJITOS-CODIGO-COMPLETO/tests/test_servicios.py` | Tests | Test | Pruebas unittest del módulo Gestión/publicación de servicios. |

**Total: 52 archivos.**
