# tournaments/urls/tournament_urls.py
from django.urls import path
from tournaments.views.tournament_view import TournamentListCreateView, TournamentDetailView

# app_name permite namespacing: "tournaments:tournament_detail"
app_name = "tournaments"

urlpatterns = [
    # Listado/creación:
    # GET  -> /api/v1/tournaments/
    # POST -> /api/v1/tournaments/
    path("", TournamentListCreateView.as_view(), name="tournament_list_create"),

    # Detalle/actualización/borrado:
    # GET    -> /api/v1/tournaments/<id>/
    # PUT    -> /api/v1/tournaments/<id>/
    # PATCH  -> /api/v1/tournaments/<id>/
    # DELETE -> /api/v1/tournaments/<id>/
    path("<int:pk>/", TournamentDetailView.as_view(), name="tournament_detail"),
]
