# players/services/player_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from players.models.player import Player
from players.repositories.player_repositoriy import PlayerRepository

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
