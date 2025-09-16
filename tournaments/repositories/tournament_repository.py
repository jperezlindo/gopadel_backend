# tournaments/repositories/tournament_repository.py
from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from tournaments.models import Tournament
from tournaments.interfaces.tournament_repository_interface import TournamentRepositoryInterface


class TournamentRepository(TournamentRepositoryInterface):
    """
    Repository: acceso optimizado a torneos.
    - Lista: solo activos, ordenados desc, con facility (select_related)
      y categorías + category (prefetch_related).
    - Get by id: mismo esquema de optimización.
    """

    def get_all_tournaments(self) -> Any:
        return (
            Tournament.objects
            .filter(is_active=True)  # Solo activos
            .select_related("facility")
            .prefetch_related("tournament_categories", "tournament_categories__category")
            .order_by("-id")
        )

    def get_tournament_by_id(self, tournament_id: int) -> Optional[Tournament]:
        try:
            return (
                Tournament.objects
                .select_related("facility")
                .prefetch_related("tournament_categories", "tournament_categories__category")
                .get(id=tournament_id)
            )
        except ObjectDoesNotExist:
            return None

    def create_tournament(self, data: dict) -> Tournament:
        # El Service ya hace full_clean() y maneja la transacción con categorías
        tournament = Tournament(**data)
        tournament.save()
        return tournament

    def update_tournament(self, tournament_id: int, data: dict) -> Optional[Tournament]:
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            for key, value in data.items():
                setattr(tournament, key, value)
            tournament.save()
            return tournament
        except ObjectDoesNotExist:
            return None

    def delete_tournament(self, tournament_id: int) -> bool:
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            tournament.delete()  # borrará en cascada las TournamentCategory por FK
            return True
        except ObjectDoesNotExist:
            return False
