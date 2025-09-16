# players/interfaces/player_repository_interface.py
from typing import Any, Optional
from abc import ABC, abstractmethod
from django.db.models import QuerySet
from players.models.player import Player

class PlayerRepositoryInterface(ABC):

    @abstractmethod
    def get_all_players(self) -> Any:
        pass

    @abstractmethod
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        pass

    @abstractmethod
    def create_player(self, data: dict) -> Player:
        pass

    @abstractmethod
    def update_player(self, player_id: int, data: dict) -> Optional[Player]:
        pass

    @abstractmethod
    def delete_player(self, player_id: int) -> bool:
        pass

    # Nueva firma para búsqueda combinada por nick_name (Player) y name/last_name/email (CustomUser)
    @abstractmethod
    def search_players(self, term: str, limit: Optional[int] = 50) -> QuerySet[Player]:
        pass
