# registrations/urls/registration_urls.py
"""
Mantengo las rutas de registrations desacopladas del controller importando desde 'views',
igual que en tournaments. Así puedo cambiar la implementación interna sin tocar las urls.

Sugerencia profesional:
- Si en el proyecto empiezo a usar namespaces, puedo agregar `app_name = "registrations"`
  y luego referenciar como "registrations:registration_detail". Por ahora sigo la convención
  existente (sin app_name) para ser consistente con tournaments.
- Estas rutas se incluyen desde el router principal bajo /api/v1/registrations/ para
  mantener un versionado claro de la API.
"""

from django.urls import path
from registrations.views.registration_view import (
    RegistrationListCreateView,
    RegistrationDetailView,
)

urlpatterns = [
    # GET  /api/v1/registrations/?tournament_category_id=<id> -> lista con filtro opcional
    # POST /api/v1/registrations/                             -> crea inscripción + unavailability opcional
    path("", RegistrationListCreateView.as_view(), name="registration_list_create"),

    # GET    /api/v1/registrations/<pk>/ -> detalle con unavailability
    # PATCH  /api/v1/registrations/<pk>/ -> actualización parcial (reemplaza unavailability si viene)
    # DELETE /api/v1/registrations/<pk>/ -> elimina inscripción
    path("<int:pk>/", RegistrationDetailView.as_view(), name="registration_detail"),
]
