# players/urls/player_urls.py
from django.urls import path
from players.views.player_view import (
    PlayerListCreateView,
    PlayerDetailView,
    PlayerSearchView,   # búsqueda por nick/user fields
)

# app_name permite referenciar como "players:player_detail" desde otros módulos/plantillas.
app_name = "players"

urlpatterns = [
    # Listado/creación:
    # GET  -> /api/v1/players/
    # POST -> /api/v1/players/
    path("", PlayerListCreateView.as_view(), name="player_list_create"),

    # Búsqueda (payload liviano con datos del user):
    # GET -> /api/v1/players/search/?q=texto&limit=50
    path("search/", PlayerSearchView.as_view(), name="player_search"),

    # Detalle/actualización/borrado:
    # GET    -> /api/v1/players/<id>/
    # PUT    -> /api/v1/players/<id>/
    # PATCH  -> /api/v1/players/<id>/
    # DELETE -> /api/v1/players/<id>/
    path("<int:player_id>/", PlayerDetailView.as_view(), name="player_detail"),
]
