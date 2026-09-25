# VERIFICACIÓN DE INTEGRIDAD

Fecha: 2026-09-24 14:53:43

ARCHIVOS PROPIOS DETECTADOS: 52
ARCHIVOS PROPIOS EXPORTADOS: 52
ARCHIVOS PROPIOS FALTANTES: 0
ARCHIVOS EXCLUIDOS JUSTIFICADAMENTE: 2671
ARCHIVOS AUXILIARES DE EXPORTACIÓN: 4

- Archivos en la exportación que no son propios ni auxiliares: 0
- Archivos con SHA-256 distinto entre original y exportación: 0
- Archivos prohibidos (venv, .db, .pyc, .env, uploads, exportaciones previas) dentro de la exportación: 0

## Exclusiones justificadas
- H — H. dependencias externas instaladas (venv/): 2621
- J — J. caché de Python (__pycache__/*.pyc): 20
- L — L. base de datos local con datos de ejecución/pruebas (cuentas, correos, hashes): 1
- M — M. exportación anterior (paquete de entrega MVC+POO y su ZIP): 29

## SHA-256 por archivo

| # | Archivo | Bytes | SHA-256 (idéntico en original y exportación) |
|---|---|---|---|
| 1 | `.env.example` | 973 | `b764665fbd5960c97a51bb43623ecceb25652fb09570d5a011f14b1ddee2f353` |
| 2 | `.gitignore` | 516 | `eeb21393ef7df2b7ba4fa83330f410ec656ad45ceaa4396ad8ded5c46244fce3` |
| 3 | `DESARROLLO.md` | 30902 | `6567622614e0fa38fdb088e608ff68cf13be8d5f969a1342f23a5b6ea6073e0b` |
| 4 | `README.md` | 10031 | `37fd89d36726f4583f1a951c435a72064b0b3c199007198eac5209f3281c4a7b` |
| 5 | `app/__init__.py` | 4922 | `6ba70d96cd6b98d74844479699600111988ebb11f1d752bfb017dabb9cb4c522` |
| 6 | `app/config.py` | 1875 | `4abeaf1be89ae3105129571e52ca5e18e17b84efc7664c5edcb96f23397e59cd` |
| 7 | `app/models.py` | 22328 | `40feb2830a86725f50e16d3433de23a715f412a4f7996708afa95323b2f695df` |
| 8 | `app/routes/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 9 | `app/routes/auth.py` | 5221 | `b2545813ab3a3fe30985999ee3fc30d79d1bdd14597132171a33d2f12d72af7c` |
| 10 | `app/routes/dashboard.py` | 15531 | `ca57e48020a32061df19686e88306bcb2c5ded62e34e08e5ceaa179d3831ca1d` |
| 11 | `app/routes/main.py` | 6040 | `fca5d84ef6484246c19e52a8b77773a23ef57c60abea840b74108f5c70fd2419` |
| 12 | `app/services/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 13 | `app/services/image_quality_service.py` | 4533 | `e6795df0d7cfe071f7f7953b3f2940b3a0ebab92efc79f606648e44ea6fa6700` |
| 14 | `app/services/image_storage.py` | 2675 | `11196e498653d642c4372bd5595b213abc2a625c3a67742c687ecd1c5b90dfd2` |
| 15 | `app/services/uploads.py` | 3807 | `492917c296b82455b9a94a1ae93cd823e2c7c12ac27febac93e0efb729f79f0b` |
| 16 | `app/static/css/style.css` | 38000 | `2190a39689cab4587e21d473a536665b09c8326f8b02624671fea9509d07f14a` |
| 17 | `app/static/fonts/Anybody-Expanded-ExtraBold.woff2` | 12928 | `424f0f3f89511386621ce71e1a2f174c52b2a68524e8f5fadfd07e3cbefb6b34` |
| 18 | `app/static/fonts/Barlow-Bold.woff2` | 22788 | `2d797dd8b35dcb3413e1af9d7052b3f4f8c341a147cdcb01f4f06af80db53289` |
| 19 | `app/static/fonts/Barlow-Medium.woff2` | 22008 | `cd759df8ef9efc98fee14307b4eb5ba27f08b1f8f2f3ad2872432e25c89907a8` |
| 20 | `app/static/fonts/Barlow-Regular.woff2` | 22196 | `b0a8ad37ac45f5fb22ced461576db72e44e295107aad7a9c8a7a4bad728fd03b` |
| 21 | `app/static/fonts/Barlow-SemiBold.woff2` | 22772 | `4b52ddd4836b592df0e4832b8286956883cdc651b015126bdd18f184b7f90cc3` |
| 22 | `app/static/img/patron-mesoamericano.svg` | 952 | `89b59fcfd7dd19d426158ee220fa1ade6b510c931a44861b0fda3615abb2e25c` |
| 23 | `app/static/js/main.js` | 3600 | `c6fae7749325899d566e9b86035412f4a6990a1f93349e3938e3ca686353d341` |
| 24 | `app/templates/auth/login.html` | 1288 | `87bdad4e4a20ed364e9e4dd973beca998874fa52077b264203ec0ad7d5bf164f` |
| 25 | `app/templates/auth/registro.html` | 2881 | `1cb47305e7b24adcb5325f20600883b697183f2f6d76e39f0f912429cd2a3b19` |
| 26 | `app/templates/base.html` | 1388 | `5a0a67eadd4c2eb0c4d8c9be7d29cb814dee917814cc7edb2998a2344b1d6e7c` |
| 27 | `app/templates/dashboard/editar_perfil.html` | 4956 | `3858f820b51dc3141de03e1a6ee66a5be9735f5896b2a30544bd95eb8e6dbc96` |
| 28 | `app/templates/dashboard/panel.html` | 4058 | `87689ca6e75e32462d3886ff56c214a82d42b8c6e4d99a9e7b368040cd914983` |
| 29 | `app/templates/dashboard/portafolio.html` | 5370 | `14cacb88a64168f2b4947545e58bb720c6341a601248c24bd8634e3ef263bd81` |
| 30 | `app/templates/dashboard/portafolio_requerido.html` | 828 | `2e5ad565ba8ca669d5de6d9873b107021d80d2fc7f86cb44c68e392b647adde0` |
| 31 | `app/templates/dashboard/servicio_form.html` | 4010 | `dfb473a7d06450aba4f0000970381a344ce6f1a6360bb29b0bfcad668b7e53c3` |
| 32 | `app/templates/en_construccion.html` | 612 | `9b0076271dd6c5d488af5b14189703cb492e15876efe260fd83d8e9934b6dd0d` |
| 33 | `app/templates/error.html` | 628 | `97c921cb998d2008a870f971e164f8d8921236e74a4d9d5b79207df4c4b9ee47` |
| 34 | `app/templates/explorar.html` | 2905 | `a91834537bf310eed58cc493287e54c2f84a86a91a4ff989642dfc6556c82938` |
| 35 | `app/templates/index.html` | 3808 | `9d0ae5d240ef17fbbf2c2e11ac9cbc033ecee975805ee2c210dda254572cf01f` |
| 36 | `app/templates/partials/footer.html` | 1290 | `bd3ac135e101280656f9ca6121e24aa7e9f1748f8052942897dca2f805213f13` |
| 37 | `app/templates/partials/header.html` | 1963 | `22876144db45687ab9ce70df67b43576e8ba658dee4d8b6c2dba223900d1fcda` |
| 38 | `app/templates/partials/service_card.html` | 2305 | `bc9e6aa7c84981fd3f121cb117bb5e73defd6bc34373435fef2f4c6a576281bb` |
| 39 | `app/templates/perfil_colaborador.html` | 3443 | `2c151b8c487cb1eb725acc220163e0c88ec207808f37ed226080f8d6b1e32df5` |
| 40 | `migrations/README` | 41 | `24bd0dae33abb1c3dc2a0466421d51de196fd7fae8843a2dd13be999d336ec99` |
| 41 | `migrations/alembic.ini` | 857 | `4a36049892b3cfa2bc41fb995ad2c900959c08a39d45b7d486c565a60bfca1c9` |
| 42 | `migrations/env.py` | 3344 | `89b2b586c74eb0e0735cd536c90a002336bb7ff105cda5525b038dfcd4a93734` |
| 43 | `migrations/script.py.mako` | 494 | `f3fc6003e826fce85e8673bb0a22228d68279b4d1996ccc41ed207ac0605265d` |
| 44 | `migrations/versions/0cfb1ba1a212_fotografias_de_perfil_portafolio_y_.py` | 4265 | `f6fc15d939cac579a1511f857401b6e8e8cce4ab596a4893be0f1e35360c2354` |
| 45 | `migrations/versions/e1a2ec9cfcff_modelos_iniciales_users_collaborator_.py` | 3795 | `0a8a48967271ef2d785fdff428cb9a414c52bf0668406d62729ab9318e8d62ce` |
| 46 | `requirements.txt` | 131 | `af7c4f6ca3c2e2db5c0b188a80d5064df57e53a0fc02f3351c4f71c4d3e1c147` |
| 47 | `run.py` | 601 | `a1cb220e435b3f0668d98f05120d054850766b8a5b4ea38d342d1f5105935e37` |
| 48 | `seed.py` | 6152 | `40db6bb08251000d741ab7ff17af636f861d6353149f656d0d6c4696c48468ec` |
| 49 | `tests/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 50 | `tests/base.py` | 1486 | `eaeb6cc4bd5d23e8521d88d851657a80260bed10b6f6ddd5d78267e5c699321c` |
| 51 | `tests/test_registro.py` | 6951 | `a5af7dec4714159f6cb73f72c6a0fd476ec58590f0121eaa45d87a69d9ce3378` |
| 52 | `tests/test_servicios.py` | 9837 | `abcacd0853c1aeee9fe6082decb92f10058cd0f0798f1294cf5ad9516acaa3ef` |
