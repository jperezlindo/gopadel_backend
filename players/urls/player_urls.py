# player/urls/player_urls.py
from django.urls import path
from players.views.player_view import PlayerListCreateView, PlayerDetailView

urlpatterns = [
    path('', PlayerListCreateView.as_view(), name="player_list_create"),
    path('<int:player_id>/', PlayerDetailView.as_view(), name="player_detail"),
]