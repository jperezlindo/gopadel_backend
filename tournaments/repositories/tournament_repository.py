from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from tournaments.models import Tournament
from tournaments.interfaces.tournament_repository_interface import TournamentRepositoryInterface

class TournamentRepository(TournamentRepositoryInterface):

    def get_all_tournaments(self) -> Any:
        return Tournament.objects.filter(is_active=True)

    def get_tournament_by_id(self, tournament_id: int) -> Optional[Tournament]:
        try:
            return Tournament.objects.select_related("facility").get(id=tournament_id)
        except ObjectDoesNotExist:
            return None

    def create_tournament(self, data: dict) -> Tournament:
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
            tournament.delete()
            return True
        except ObjectDoesNotExist:
            return False
