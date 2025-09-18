# roles/urls/rol_urls.py
from django.urls import path
from roles.views.rol_view import RolListView, RolDetailView

# Uso app_name para namespacing. Así se pueden referenciar rutas como "roles:role_list".
app_name = "roles"

urlpatterns = [
    # Listado solo lectura:
    # GET -> /api/v1/roles/?is_active=true&search=adm&ordering=name
    path("", RolListView.as_view(), name="role_list"),

    # Detalle solo lectura:
    # GET -> /api/v1/roles/<id>/
    path("<int:pk>/", RolDetailView.as_view(), name="role_detail"),
]
