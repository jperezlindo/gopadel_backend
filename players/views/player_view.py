# players/views/player_view.py
# Este archivo actúa como un puente estable entre urls.py y los controllers.
# La idea es importar siempre desde "players.views.player_view" en las rutas,
# así si en el futuro cambian paths o nombres de los controllers,
# no hay que tocar las urls de la app.

from players.controllers.player_controller import (
    PlayerListCreateView,
    PlayerDetailView,
    PlayerSearchView,
)

# Expongo explícitamente qué vistas están disponibles desde este módulo.
__all__ = ["PlayerListCreateView", "PlayerDetailView", "PlayerSearchView"]
