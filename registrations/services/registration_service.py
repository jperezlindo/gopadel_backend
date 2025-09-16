# registrations/services/registration_service.py
from django.core.exceptions import ValidationError
from registrations.repositories.registration_repository import RegistrationRepository
from registrations.models.registration import Registration

class RegistrationService:
    def __init__(self, repo: RegistrationRepository | None = None):
        self.repo = repo or RegistrationRepository()

    def list(self, tournament_category_id: int | None = None):
        return self.repo.list(tournament_category_id)

    def get(self, reg_id: int):
        reg = self.repo.get_by_id(reg_id)
        if not reg:
            raise ValidationError("Registration no encontrada.")
        return reg

    def create(
        self,
        *,
        tournament_category,
        player,
        partner,
        paid_amount,
        payment_reference: str = "",
        comment: str = "",
        is_active: bool | None = None,
        payment_status: str | None = None,
    ):
        tc_id = tournament_category.id if hasattr(tournament_category, "id") else int(tournament_category)
        player_id = player.id if hasattr(player, "id") else int(player)
        partner_id = partner.id if hasattr(partner, "id") else int(partner)

        # Duplicidades de negocio
        if self.repo.exists_player_in_tc(tc_id, player_id):
            raise ValidationError("El jugador ya está inscripto en esta categoría de torneo.")
        if self.repo.exists_partner_in_tc(tc_id, partner_id):
            raise ValidationError("El partner ya está inscripto en esta categoría de torneo.")
        if self.repo.exists_pair_in_tc(tc_id, player_id, partner_id):
            raise ValidationError("Esta pareja ya está inscripta en esta categoría (o en orden inverso).")

        data = {
            "tournament_category": tournament_category,
            "player": player,
            "partner": partner,
            "paid_amount": paid_amount,
            "payment_reference": (payment_reference or "").strip(),
            "comment": (comment or "").strip(),
            "is_active": True if is_active is None else bool(is_active),
            "payment_status": (payment_status or ""),
        }

        # Validación de modelo antes de crear
        tmp = Registration(**data)
        tmp.full_clean()

        return self.repo.create(**data)

    def delete(self, reg_id: int):
        reg = self.get(reg_id)
        self.repo.delete(reg)
        return True
