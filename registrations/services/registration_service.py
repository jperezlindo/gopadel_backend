from typing import Any, Optional
from django.core.exceptions import ValidationError
from django.db.models import Q
from registrations.repositories.registration_repository import RegistrationRepository
from registrations.models.registration import Registration
from tournament_categories.models.tournament_category import TournamentCategory


class RegistrationService:
    def __init__(self) -> None:
        self.repo = RegistrationRepository()

    def list(self, **filters) -> Any:
        return self.repo.list(**filters)

    def get(self, reg_id: int) -> Optional[Registration]:
        return self.repo.get_by_id(reg_id)

    def _validate_unique_people_in_tournament(
        self,
        tournament_id: int,
        player_id: int,
        partner_id: int,
        exclude_id: Optional[int] = None,
    ) -> None:
        """
        Ni player ni partner pueden estar ya inscriptos en ese torneo (en ninguna categoría).
        """
        qs = Registration.objects.filter(
            Q(player_id=player_id)
            | Q(partner_id=player_id)
            | Q(player_id=partner_id)
            | Q(partner_id=partner_id),
            tournament_category__tournament_id=tournament_id,
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        if qs.exists():
            raise ValidationError(
                "Either player or partner is already registered in this tournament."
            )

    def create(self, data: dict) -> Registration:
        tc: TournamentCategory = data["tournament_category"]
        tournament_id = tc.tournament_id # type: ignore
        player_id = data["player"].id
        partner_id = data["partner"].id

        if player_id == partner_id:
            raise ValidationError("Player and partner must be different.")

        # Reglas de negocio: nadie puede duplicarse en el torneo
        self._validate_unique_people_in_tournament(tournament_id, player_id, partner_id)

        # Validaciones de modelo (incluye check player < partner y unique pair in category)
        reg = Registration(**data)
        reg.full_clean()
        reg.save()
        return reg

    def update(self, reg_id: int, data: dict) -> Registration:
        instance = self.repo.get_by_id(reg_id)
        if instance is None:
            raise ValidationError("Registration not found.")

        player = data.get("player", instance.player)
        partner = data.get("partner", instance.partner)
        if player == partner:
            raise ValidationError("Player and partner must be different.")

        tournament_id = instance.tournament_category.tournament_id # type: ignore
        self._validate_unique_people_in_tournament(
            tournament_id, player.id, partner.id, exclude_id=instance.id # type: ignore
        )

        for k, v in data.items():
            setattr(instance, k, v)

        instance.full_clean()
        instance.save()
        return instance

    def delete(self, reg_id: int) -> bool:
        instance = self.repo.get_by_id(reg_id)
        if instance is None:
            return False
        self.repo.delete(instance)
        return True
