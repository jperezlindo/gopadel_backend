# tournaments/repositories/tournament_repository.py
from typing import Any, Optional, Iterable
from django.db.models import Q, QuerySet

# IMPORTANTE:
# Ajusto el import para apuntar al modelo real. Si ya exponés Tournament en __init__.py,
# podés usar: from tournaments.models import Tournament
from tournaments.models.tournament import Tournament

from tournaments.interfaces.tournament_repository_interface import TournamentRepositoryInterface


class TournamentRepository(TournamentRepositoryInterface):
    """
    Acceso a datos para Tournament, optimizado con select_related/prefetch_related.

    Decisiones:
    - Mantengo métodos de la interfaz (compatibilidad), pero agrego filtros opcionales
      en get_all_tournaments (search/is_active/facility_id/ordering).
    - La edición/creación inline de categorías por torneo se debe manejar en el Service,
      para mantener el repo enfocado en el ORM de Tournament.
    """

    # ---------------- QS base y helpers ----------------
    def _base_qs(self) -> QuerySet:
        """
        Punto único para definir las relaciones a precargar y evitar N+1.
        """
        return (
            Tournament.objects
            .select_related("facility")
            .prefetch_related("tournament_categories", "tournament_categories__category")
        )

    # ---------------- Listado ----------------
    def get_all_tournaments(
        self,
        *,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        facility_id: Optional[int] = None,
        ordering: Optional[Iterable[str]] = None,
    ) -> Any:
        """
        Listado flexible de torneos:
        - search: busca por nombre (icontains).
        - is_active: filtra por estado si se especifica.
        - facility_id: filtra por facility responsable si se especifica.
        - ordering: permite override del orden por defecto (Meta.ordering).

        Nota: por compatibilidad hacia atrás, si no se pasan filtros, devuelve todos.
        """
        qs = self._base_qs()

        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        if facility_id is not None:
            qs = qs.filter(facility_id=facility_id)

        if search:
            s = search.strip()
            if s:
                qs = qs.filter(Q(name__icontains=s))

        if ordering:
            qs = qs.order_by(*ordering)

        return qs

    # ---------------- Obtención puntual ----------------
    def get_tournament_by_id(self, tournament_id: int) -> Optional[Tournament]:
        """
        Obtengo un torneo por PK con facility y categorías precargadas.
        Devuelvo None si no existe.
        """
        return self._base_qs().filter(id=tournament_id).first()

    # ---------------- Escritura ----------------
    def create_tournament(self, data: dict) -> Tournament:
        """
        Creo el torneo. Las validaciones de dominio corren en el modelo (clean/save)
        y en el Service (transacciones + inline categories si aplica).
        """
        tournament = Tournament(**data)
        tournament.save()
        return tournament

    def update_tournament(self, tournament_id: int, data: dict) -> Optional[Tournament]:
        """
        Actualizo campos simples del torneo. Si no existe, devuelvo None.
        """
        tournament = Tournament.objects.filter(id=tournament_id).first()
        if tournament is None:
            return None

        for key, value in data.items():
            setattr(tournament, key, value)
        tournament.save()
        return tournament

    def delete_tournament(self, tournament_id: int) -> bool:
        """
        Borrado físico del torneo. Por cascada, se eliminarán las TournamentCategory relacionadas
        (según la FK definida en esa app).
        """
        tournament = Tournament.objects.filter(id=tournament_id).first()
        if tournament is None:
            return False
        tournament.delete()
        return True
