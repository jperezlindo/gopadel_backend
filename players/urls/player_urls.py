# players/urls/player_urls.py
from django.urls import path
from players.views.player_view import (
    PlayerListCreateView,
    PlayerDetailView,
    PlayerSearchView,   # <- nuevo
)

urlpatterns = [
    path("", PlayerListCreateView.as_view(), name="player_list_create"),
    path("search/", PlayerSearchView.as_view(), name="player_search"),  # <- nuevo
    path("<int:player_id>/", PlayerDetailView.as_view(), name="player_detail"),
]