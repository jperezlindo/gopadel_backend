# players/repositories/player_repository.py
from typing import Optional
from django.db.models import Q, QuerySet
from players.models.player import Player
from players.interfaces.player_repository_interface import PlayerRepositoryInterface


class PlayerRepository(PlayerRepositoryInterface):
    """
    Acceso a datos para Player.

    Decisiones:
    - NO se usa soft delete (el modelo no tiene is_deleted): el borrado es FÍSICO.
    - get_all_players: por defecto devuelvo jugadores activos (is_active=True).
    - get_player_by_id: trae cualquier jugador (activo o inactivo).
    - create_player/update_player: delego validaciones de modelo al save().
    """

    # -------- Listado --------
    def get_all_players(self) -> QuerySet[Player]:
        """
        Devuelvo jugadores activos. Si más adelante necesitás incluir inactivos,
        agregamos otro método o un flag opcional.
        """
        return Player.objects.filter(is_active=True)

    # -------- Obtención puntual --------
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Busco por PK sin filtrar por is_active (permite reactivar luego si hace falta).
        """
        return Player.objects.filter(id=player_id).first()

    # -------- Escritura --------
    def create_player(self, data: dict) -> Player:
        """
        Creo un jugador. El modelo valida en clean() y save() (full_clean()).
        """
        return Player.objects.create(**data)

    def update_player(self, player_id: int, data: dict) -> Optional[Player]:
        """
        Actualizo campos simples. No toco campos no presentes en data.
        """
        player = self.get_player_by_id(player_id)
        if player is None:
            return None

        for key, value in data.items():
            setattr(player, key, value)

        player.save()
        return player

    # -------- Borrado (FÍSICO) --------
    def delete_player(self, player_id: int) -> bool:
        """
        Borrado físico (no hay soft delete en Player).
        Retorna False si el jugador no existe.
        """
        player = self.get_player_by_id(player_id)
        if player is None:
            return False
        player.delete()
        return True

    # -------- Búsqueda --------
    def search_players(self, term: str, limit: Optional[int] = 50) -> QuerySet[Player]:
        """
        Busca jugadores por:
        - nick_name (icontains)
        - name / last_name / email del User relacionado
        Retorna un queryset limitado por defecto a 50 resultados.
        """
        term = (term or "").strip()
        if not term:
            return Player.objects.none()

        qs = (
            Player.objects
            .select_related("user")
            .filter(
                Q(nick_name__icontains=term)
                | Q(user__name__icontains=term)
                | Q(user__last_name__icontains=term)
                | Q(user__email__icontains=term)
            )
            .order_by("user__name", "nick_name", "id")
        )
        return qs[:limit] if isinstance(limit, int) and limit > 0 else qs
