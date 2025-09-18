# tournaments/views/tournament_view.py
# Este módulo actúa como PUENTE estable para las rutas de la app.
# La idea es que urls.py siempre importe desde "tournaments.views.tournament_view"
# y no dependa de la estructura interna de controllers. Si algún día movemos o
# renombramos controllers, las URLs no cambian.

from tournaments.controllers.tournament_controller import (
    TournamentListCreateView,
    TournamentDetailView,
)

# Expongo explícitamente qué vistas ofrece este bridge.
__all__ = ["TournamentListCreateView", "TournamentDetailView"]
