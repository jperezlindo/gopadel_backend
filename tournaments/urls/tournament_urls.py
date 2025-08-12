# tournaments/urls/tournament_urls.py
from django.urls import path
from tournaments.views.tournament_view import TournamentListCreateView, TournamentDetailView

urlpatterns = [
    path('', TournamentListCreateView.as_view(), name='tournament_list_create'),
    path('<int:pk>/', TournamentDetailView.as_view(), name='tournament_detail'),
]
