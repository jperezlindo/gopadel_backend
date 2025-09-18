# conftest.py
"""
Configuración de pruebas para pytest-django.

- BD SQLite en memoria (rápido y sin depender de MySQL).
- Sin migraciones en apps de dominio (crea tablas desde modelos).
- DRF relajado (sin JWT, AllowAny) para tests unitarios/integración simples.
- URLConf mínima 'tests.urls' aislada (solo Categories) y forzada limpiando
  la caché del resolutor para que Django la tome en cada test run.
- Idioma estable en tests para evitar segmentación por idioma en URL resolver.
"""

import importlib
import pytest
from django.urls import clear_url_caches, set_urlconf


@pytest.fixture(autouse=True)
def _test_settings(settings):
    # --- Base de datos efímera ---
    settings.DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
    }

    # --- Hash de contraseñas rápido ---
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

    # --- Sin migraciones en apps de dominio (más veloz) ---
    domain_apps = {
        "users",
        "facilities",
        "cities",
        "roles",
        "categories",
        "tournaments",
        "players",
        "tournament_categories",
        "registrations",
    }
    settings.MIGRATION_MODULES = {app: None for app in domain_apps}

    # --- DRF sin auth para tests ---
    rest = getattr(settings, "REST_FRAMEWORK", {})
    rest.update(
        {
            "DEFAULT_AUTHENTICATION_CLASSES": [],
            "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
        }
    )
    settings.REST_FRAMEWORK = rest

    # --- URLConf mínima (solo categories) ---
    settings.ROOT_URLCONF = "tests.urls"
    # Fuerzo recarga de la URLConf y limpio cachés del resolutor para evitar 404 por URLs cacheadas
    clear_url_caches()
    set_urlconf(None)
    importlib.invalidate_caches()
    try:
        importlib.import_module("tests.urls")
    except ModuleNotFoundError:
        # Si no existe el módulo, dejo que falle el test con trace claro
        pass

    # --- Idioma estable en tests ---
    settings.LANGUAGE_CODE = "en-us"
