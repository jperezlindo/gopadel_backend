# registrations/repositories/registration_repository.py
from typing import Optional, Any, List, Dict
from django.db import transaction
from django.db.models import Q, QuerySet
from django.core.exceptions import ObjectDoesNotExist

# Uso el __init__ del package para importar modelos públicos y mantener una API clara
from registrations.models import Registration, RegistrationUnavailability
from registrations.interfaces.registration_repository_interface import IRegistrationRepository


class RegistrationRepository(IRegistrationRepository):
    """
    Mantengo este repositorio como única puerta de acceso ORM para Registration.
    - Centralizo select_related/prefetch_related para performance consistente.
    - Expongo helpers de existencia para validaciones de negocio en el service.
    - Incluyo utilidades para persistir indisponibilidades en bloque.
    """

    # ---------------------------
    # Lectura (queries base)
    # ---------------------------
    def _base_qs(self) -> QuerySet[Registration]:
        # Aplico select_related para FKs y prefetch de slots de indisponibilidad.
        # Esto me evita N+1 al serializar o componer respuestas.
        return (
            Registration.objects
            .select_related("tournament_category", "player", "partner")
            .prefetch_related("unavailability")
        )

    def list(self, tournament_category_id: Optional[int] = None) -> Any:
        # Expongo un queryset listo para paginar/filtrar en capas superiores si hace falta.
        qs = self._base_qs().order_by("-id")
        if tournament_category_id:
            qs = qs.filter(tournament_category_id=tournament_category_id)
        return qs

    def get_by_id(self, reg_id: int) -> Optional[Registration]:
        try:
            return self._base_qs().get(id=reg_id)
        except ObjectDoesNotExist:
            return None

    # ---------------------------
    # Reglas de existencia (negocio)
    # ---------------------------
    def exists_player_in_tc(self, tc_id: int, player_id: int) -> bool:
        return Registration.objects.filter(tournament_category_id=tc_id, player_id=player_id).exists()

    def exists_partner_in_tc(self, tc_id: int, partner_id: int) -> bool:
        return Registration.objects.filter(tournament_category_id=tc_id, partner_id=partner_id).exists()

    def exists_pair_in_tc(self, tc_id: int, player_id: int, partner_id: int) -> bool:
        # Contemplo el orden inverso para asegurar unicidad de la pareja en la misma TC.
        return (
            Registration.objects
            .filter(tournament_category_id=tc_id)
            .filter(
                (Q(player_id=player_id) & Q(partner_id=partner_id)) |
                (Q(player_id=partner_id) & Q(partner_id=player_id))
            )
            .exists()
        )

    # ---------------------------
    # Escritura (mutaciones)
    # ---------------------------
    def create(self, **data) -> Registration:
        # Dejo la validación a nivel service/model; acá me enfoco en persistir.
        return Registration.objects.create(**data)

    def delete(self, instance: Registration) -> None:
        # Mantengo delete directo; si en el futuro hay soft-delete, centralizo el cambio acá.
        instance.delete()

    # ---------------------------
    # Indisponibilidades (slots)
    # ---------------------------
    @transaction.atomic
    def add_unavailability(self, registration: Registration, slots: List[Dict[str, Any]]) -> None:
        """
        Inserto en bloque las indisponibilidades asociadas a una inscripción.
        - slots: lista de dicts con keys: day_of_week, start_time, end_time.
        - Uso bulk_create por eficiencia; confío en constraints de BD para duplicados exactos.
        """
        if not slots:
            return

        # Convierto cada dict en instancia ready-to-insert
        instances = [
            RegistrationUnavailability(
                registration=registration,
                day_of_week=int(s["day_of_week"]),
                start_time=s["start_time"],
                end_time=s["end_time"],
            )
            for s in slots
        ]

        # bulk_create bajo transacción; ignoro conflictos = False para surfacing de errores
        RegistrationUnavailability.objects.bulk_create(instances, ignore_conflicts=False)
