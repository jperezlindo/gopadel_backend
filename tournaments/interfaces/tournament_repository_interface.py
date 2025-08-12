from typing import Any, Optional
from abc import ABC, abstractmethod
from tournaments.models.tournament import Tournament

class TournamentRepositoryInterface(ABC):

    @abstractmethod
    def get_all_tournaments(self) -> Any:
        pass

    @abstractmethod
    def get_tournament_by_id(self, tournament_id: int) -> Optional[Tournament]:
        pass

    @abstractmethod
    def create_tournament(self, data: dict) -> Tournament:
        pass

    @abstractmethod
    def update_tournament(self, tournament_id: int, data: dict) -> Optional[Tournament]:
        pass

    @abstractmethod
    def delete_tournament(self, tournament_id: int) -> bool:
        """Retorna True si borró, False si no existía."""
        pass
