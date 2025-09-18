# tests/urls.py
"""
URLConf mínima para pruebas de integración.

Decisión:
- Solo incluyo las URLs de Categories para evitar que el cargado de la URLConf
  traiga imports de otras apps (users/players/etc.) que no son parte de estas pruebas.
- Mantengo el mismo prefijo que en producción (/api/v1/categories/) para que
  los paths sean representativos. En los tests uso reverse("category_list"/"category_detail").
"""

from django.urls import path, include

urlpatterns = [
    path("api/v1/categories/", include("categories.urls.category_urls")),
]
