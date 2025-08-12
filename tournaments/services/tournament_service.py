# tournaments/services/tournament_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError as DjangoValidationError

from tournaments.repositories.tournament_repository import TournamentRepository
from tournaments.models.tournament import Tournament


class TournamentService:
    def __init__(self, repository: Optional[TournamentRepository] = None):
        self.repository = repository or TournamentRepository()

    def list(self) -> Any:
        return self.repository.get_all_tournaments()

    def get(self, tournament_id: int) -> Tournament:
        instance = self.repository.get_tournament_by_id(tournament_id)
        if not instance:
            # Not found → levantamos ValidationError genérica (tu controller la mapea a 404)
            raise DjangoValidationError({"detail": "Tournament not found."})
        return instance

    def create(self, data: Dict) -> Tournament:
        instance = self.repository.create_tournament(data)
        # Validaciones de modelo (coherencia de fechas, etc.)
        instance.full_clean()  # si falla, levanta DjangoValidationError
        instance.save()
        return instance

    def update(self, tournament_id: int, data: Dict) -> Tournament:
        instance = self.repository.update_tournament(tournament_id, data)
        if not instance:
            raise DjangoValidationError({"detail": "Tournament not found."})
        instance.full_clean()  # si falla, levanta DjangoValidationError
        instance.save()
        return instance

    def delete(self, tournament_id: int) -> None:
        ok = self.repository.delete_tournament(tournament_id)
        if not ok:
            raise DjangoValidationError({"detail": "Tournament not found."})
