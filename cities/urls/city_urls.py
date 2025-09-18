# cities/urls/city_urls.py
from django.urls import path
from cities.views.city_view import CityListCreateView, CityDetailView

app_name = "cities"

urlpatterns = [
    # Listado/creación:
    # GET  -> /api/v1/cities/?search=&is_active=true&include_deleted=false&ordering=name
    # POST -> /api/v1/cities/
    path("", CityListCreateView.as_view(), name="city_list_create"),

    # Detalle/actualización/borrado lógico:
    # GET    -> /api/v1/cities/<id>/
    # PUT    -> /api/v1/cities/<id>/
    # PATCH  -> /api/v1/cities/<id>/
    # DELETE -> /api/v1/cities/<id>/
    path("<int:pk>/", CityDetailView.as_view(), name="city_detail"),
]
