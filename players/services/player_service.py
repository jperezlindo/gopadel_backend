# players/services/player_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from players.models.player import Player
from players.repositories.player_repository import PlayerRepository  # fix del import


class PlayerService:
    def __init__(self, repository: Optional[PlayerRepository] = None):
        self.repository = repository or PlayerRepository()

    def list(self) -> Any:
        return self.repository.get_all_players()

    def get(self, player_id: int) -> Optional[Player]:
        player = self.repository.get_player_by_id(player_id)
        if not player:
            raise ValidationError("Player not found.", code="not_found")
        return player

    def create(self, data: dict) -> Player:
        player = self.repository.create_player(data)
        player.full_clean()
        player.save()
        return player

    def update(self, player_id: int, data: dict) -> Optional[Player]:
        player = self.repository.update_player(player_id, data)
        if not player:
            raise ValidationError("Player not found.", code="not_found")
        player.full_clean()
        player.save()
        return player

    def delete(self, player_id: int) -> bool:
        return self.repository.delete_player(player_id)

    # === Nuevo: búsqueda por nick_name (Player) o name/last_name/email (CustomUser) ===
    def search(self, term: str, limit: Optional[int] = 50) -> QuerySet[Player]:
        q = (term or "").strip()
        if len(q) < 2:
            raise ValidationError("Search term must have at least 2 characters.", code="invalid")

        # Normalizamos y acotamos el límite
        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = 50
            # Evitamos valores extremos
            if limit <= 0:
                limit = 50
            if limit > 200:
                limit = 200

        return self.repository.search_players(q, limit=limit)
