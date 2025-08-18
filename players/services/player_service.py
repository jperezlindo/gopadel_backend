# players/services/player_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError as DjangoValidationError 

from players.models.player import Player
from players.repositories.player_repositoriy import PlayerRepository

class PlayerService:
    def __init__(self, repository: Optional[PlayerRepository] = None):
        self.repository = repository or PlayerRepository()

    def list(self) -> Any:
        return self.repository.get_all_players()

    def get(self, player_id: int) -> Optional[Player]:
        instance = self.repository.get_player_by_id(player_id)
        if not instance:
            raise DjangoValidationError({"detail": "Player not found."})
        return instance

    def create(self, data: dict) -> Player:
        instance = self.repository.create_player(data)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, player_id: int, data: dict) -> Optional[Player]:
        instance = self.repository.update_player(player_id, data)
        if not instance:
            raise DjangoValidationError({"detail": "Player not found."})
        instance.full_clean()
        instance.save()
        return instance

    def delete(self, player_id: int) -> bool:
        return self.repository.delete_player(player_id)
