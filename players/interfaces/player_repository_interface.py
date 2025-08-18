from typing import Any, Optional
from abc import ABC, abstractmethod
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