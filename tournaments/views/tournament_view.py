# tournaments/views/tournament_view.py
from tournaments.controllers.tournament_controller import (
    TournamentListCreateView as TournamentListCreateView,
    TournamentDetailView as TournamentDetailView,
)

__all__ = ["TournamentListCreateView", "TournamentDetailView"]
