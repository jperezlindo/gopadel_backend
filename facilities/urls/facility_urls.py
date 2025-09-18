# facilities/urls/facility_urls.py
from django.urls import path
from facilities.views.facility_view import FacilityListCreateView, FacilityDetailView

app_name = "facilities"

urlpatterns = [
    # Listado/creación:
    # GET  -> /api/v1/facilities/?search=&is_active=true&include_deleted=false&ordering=name
    # POST -> /api/v1/facilities/
    path("", FacilityListCreateView.as_view(), name="facility_list_create"),

    # Detalle/actualización/borrado lógico:
    # GET    -> /api/v1/facilities/<id>/
    # PUT    -> /api/v1/facilities/<id>/
    # PATCH  -> /api/v1/facilities/<id>/
    # DELETE -> /api/v1/facilities/<id>/
    path("<int:pk>/", FacilityDetailView.as_view(), name="facility_detail"),
]
