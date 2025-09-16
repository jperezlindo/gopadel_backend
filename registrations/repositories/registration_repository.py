# registrations/repositories/registration_repository.py
from typing import Optional, Any
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from registrations.models.registration import Registration
from registrations.interfaces.registration_repository_interface import IRegistrationRepository

class RegistrationRepository(IRegistrationRepository):
    def list(self, tournament_category_id: Optional[int] = None) -> Any:
        qs = Registration.objects.select_related("tournament_category", "player", "partner").order_by("-id")
        if tournament_category_id:
            qs = qs.filter(tournament_category_id=tournament_category_id)
        return qs

    def get_by_id(self, reg_id: int) -> Optional[Registration]:
        try:
            return Registration.objects.select_related("tournament_category", "player", "partner").get(id=reg_id)
        except ObjectDoesNotExist:
            return None

    def exists_player_in_tc(self, tc_id: int, player_id: int) -> bool:
        return Registration.objects.filter(tournament_category_id=tc_id, player_id=player_id).exists()

    def exists_partner_in_tc(self, tc_id: int, partner_id: int) -> bool:
        return Registration.objects.filter(tournament_category_id=tc_id, partner_id=partner_id).exists()

    def exists_pair_in_tc(self, tc_id: int, player_id: int, partner_id: int) -> bool:
        # contempla orden inverso
        return Registration.objects.filter(
            tournament_category_id=tc_id
        ).filter(
            (Q(player_id=player_id) & Q(partner_id=partner_id)) |
            (Q(player_id=partner_id) & Q(partner_id=player_id))
        ).exists()

    def create(self, **data) -> Registration:
        return Registration.objects.create(**data)

    def delete(self, instance: Registration) -> None:
        instance.delete()
