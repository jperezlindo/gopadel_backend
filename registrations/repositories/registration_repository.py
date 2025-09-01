from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from registrations.models.registration import Registration
from registrations.interfaces.registration_repository_interface import (
    RegistrationRepositoryInterface,
)


class RegistrationRepository(RegistrationRepositoryInterface):
    def list(self, **filters) -> Any:
        qs = Registration.objects.select_related(
            "tournament_category",
            "player",
            "partner",
            "tournament_category__tournament",
        ).all()

        if "tournament_id" in filters and filters["tournament_id"] is not None:
            qs = qs.filter(tournament_category__tournament_id=filters["tournament_id"])

        if "tournament_category_id" in filters and filters["tournament_category_id"] is not None:
            qs = qs.filter(tournament_category_id=filters["tournament_category_id"])

        if "player_id" in filters and filters["player_id"] is not None:
            pid = filters["player_id"]
            qs = qs.filter(Q(player_id=pid) | Q(partner_id=pid))

        if "status" in filters and filters["status"] is not None:
            qs = qs.filter(status=filters["status"])

        return qs.order_by("id")

    def get_by_id(self, reg_id: int) -> Optional[Registration]:
        try:
            return Registration.objects.select_related(
                "tournament_category",
                "player",
                "partner",
                "tournament_category__tournament",
            ).get(id=reg_id)
        except ObjectDoesNotExist:
            return None

    def create(self, data: dict) -> Registration:
        return Registration.objects.create(**data)

    def update(self, instance: Registration, data: dict) -> Registration:
        for k, v in data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def delete(self, instance: Registration) -> None:
        instance.delete()

    def exists_person_in_tournament(self, person_id: int, tournament_id: int) -> bool:
        return Registration.objects.filter(
            Q(player_id=person_id) | Q(partner_id=person_id),
            tournament_category__tournament_id=tournament_id,
        ).exists()
