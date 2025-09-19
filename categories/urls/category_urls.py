# categories/urls/category_urls.py
# En este módulo solo defino rutas y no importo ningún urls.py del proyecto ni de otras apps.
# De esta forma evito cualquier posibilidad de recursión por includes cruzados.

from django.urls import path
from categories.views.category_view import (
    CategoryListCreateView,
    CategoryDetailView,
)

# Declaro app_name para poder namespear rutas (reverse("categories:category_detail")).
app_name = "categories"

urlpatterns = [
    # Listado y creación
    # GET  -> /api/v1/categories/
    # POST -> /api/v1/categories/
    path("", CategoryListCreateView.as_view(), name="category_list_create"),

    # Detalle / actualización / borrado
    # GET    -> /api/v1/categories/<pk>/
    # PUT    -> /api/v1/categories/<pk>/
    # PATCH  -> /api/v1/categories/<pk>/
    # DELETE -> /api/v1/categories/<pk>/
    path("<int:pk>/", CategoryDetailView.as_view(), name="category_detail"),
]
