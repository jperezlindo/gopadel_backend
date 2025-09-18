# gopadel_backend/settings.py
"""
Django settings para el proyecto GoPadel.

Este archivo centraliza configuración de seguridad, base de datos, DRF, JWT,
paginación, CORS/CSRF, logging y otras piezas transversales. La idea es que
cualquier dev del equipo pueda entender rápido el porqué de cada ajuste.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# =========================
# Paths base del proyecto
# =========================
# Defino BASE_DIR para construir rutas relativas (static, media, etc.).
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# Seguridad base
# =========================
# Cargo SECRET_KEY desde .env para no commitearlo en el repo.
# En producción, este valor es crítico para CSRF, sesiones y firmas.
SECRET_KEY = config('SECRET_KEY')

# Activo/Desactivo DEBUG por variable de entorno. En prod siempre va False.
DEBUG = config('DEBUG', default=False, cast=bool)

# Defino hosts permitidos. En dev uso localhost:5173 para el front.
# Nota: con decouple+Csv, default='' puede dar [''] si no se setea en .env.
# En producción, configurar ALLOWED_HOSTS correctamente (p. ej. dominio o IP).
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='')

# =========================
# Apps instaladas
# =========================
# Mantengo orden: Django core → terceros → apps de dominio.
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros (infra API)
    "corsheaders",          # Habilito CORS para el front (Vite/Vue)
    "django_filters",       # Habilito filtros declarativos en vistas DRF
    'rest_framework',       # DRF como base para API REST
    'drf_spectacular',      # Generación de OpenAPI/Swagger

    # Apps del dominio (capas por entidad siguiendo arquitectura limpia)
    'users',
    'facilities',
    'cities',
    'roles',
    'categories',
    'tournaments',
    'players',
    'tournament_categories',
    'registrations',
]

# =========================
# Middleware
# =========================
# Orden importante: CORS va antes que CommonMiddleware para inyectar headers.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# =========================
# URLs / WSGI
# =========================
# Expongo el punto de entrada de URLConf y WSGI (deploy clásico).
ROOT_URLCONF = 'gopadel_backend.urls'
WSGI_APPLICATION = 'gopadel_backend.wsgi.application'

# =========================
# Templates (no usados por ahora)
# =========================
# Dejo configuración mínima por si más adelante extiendo el admin.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Si más adelante expongo templates propios, agrego paths acá
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =========================
# Database
# =========================
# Uso MySQL según stack acordado. Parametrizo por .env.
# En prod conviene activar sql_mode estricto a nivel servidor para datos sanos.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

# =========================
# Password validators
# =========================
# Mantengo validadores por defecto de Django para contraseñas más seguras.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================
# I18N / TZ
# =========================
# Seteo español Argentina y TZ local. DRF serializa con TZ si USE_TZ=True.
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = "America/Argentina/Cordoba"
USE_I18N = True
USE_TZ = True

# =========================
# Static / Media
# =========================
# En dev sirve Django; en prod conviene CDN/reverse proxy (Nginx).
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =========================
# Default PK
# =========================
# Uso BigAutoField para evitar overflow a futuro.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================
# DRF
# =========================
# Centralizo configuración de esquema, auth, permisos, paginación y filtros.
REST_FRAMEWORK = {
    # Esquema OpenAPI con drf-spectacular
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Autenticación por defecto: JWT global (SimpleJWT)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    # Permisos por defecto: requiero autenticación.
    # En vistas públicas (p. ej. healthcheck) uso AllowAny a nivel view.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Handler de excepciones centralizado para formato uniforme (utils/exceptions.py)
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',

    # Paginación por defecto (utils/pagination.py)
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.DefaultPagination',
    'PAGE_SIZE': 20,

    # Filtros: habilito django-filter, ordering y búsqueda.
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
}

# =========================
# Usuario custom
# =========================
# Registro el modelo de usuario propio para futuras extensiones (roles, FK, etc.).
AUTH_USER_MODEL = 'users.CustomUser'

# =========================
# SimpleJWT
# =========================
# Defino ventanas temporales conservadoras; se ajustan según UX/riesgo.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# =========================
# drf-spectacular (OpenAPI)
# =========================
# Expongo esquema de la API con seguridad JWT para que el front/testing lo aproveche.
SPECTACULAR_SETTINGS = {
    'TITLE': 'GoPadel API',
    'DESCRIPTION': 'API REST para la gestión de torneos de pádel',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'SECURITY': [{'bearerAuth': []}],
}

# =========================
# CORS / CSRF
# =========================
# En dev permito el front local (Vite en 5173). En prod, setear dominios reales en .env.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# Si uso cookies entre dominios, habilitar:
# CORS_ALLOW_CREDENTIALS = True

# Si expongo vistas con SessionAuth/CSRF, declaro orígenes confiables.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# =========================
# Endurecimiento mínimo HTTP
# =========================
# Estas banderas suman capas defensivas. En prod, reforzar con HTTPS y secure cookies.
SECURE_CONTENT_TYPE_NOSNIFF = True

# Nota: SECURE_BROWSER_XSS_FILTER quedó deprecado en versiones recientes de Django/Chrome.
# Se deja como referencia histórica; la protección XSS real va por otras capas (templating, CSP).
SECURE_BROWSER_XSS_FILTER = True

# Cookies httpOnly para mitigar XSS. CSRF_COOKIE_HTTPONLY=False si el front necesita leerlo.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

# Evito iframes para prevenir clickjacking, salvo que más adelante se requiera integrar widgets.
X_FRAME_OPTIONS = "DENY"

# =========================
# Logging base
# =========================
# En dev imprimo a consola; en prod lo recolecta systemd/Docker y se envía a observabilidad si aplica.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[%(levelname)s] %(asctime)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "WARNING"},
        # Si necesito más detalle del dominio, creo un logger 'gopadel' o subo nivel en apps.
    },
}

# =========================
# Sugerencias operativas
# =========================
# 1) Mantener JWT global y marcar explícitamente las vistas públicas con AllowAny
#    (p. ej. healthcheck, open-tournaments si hiciera falta).
# 2) Ya están referenciados utils/response_handler.py, utils/exceptions.py y utils/pagination.py.
#    Con esto el proyecto compila sin ImportError y el front recibe errores/paginación consistentes.
# 3) En caso de CORS en dev, validar que el front consuma con http://localhost:5173
#    y que no haya puertos o protocolos inconsistentes.
# 4) En prod, mover estáticos a CDN y servir con Nginx/Reverse Proxy, forzando HTTPS (SECURE_SSL_REDIRECT).
