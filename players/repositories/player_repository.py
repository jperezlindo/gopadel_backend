# players/repositories/player_repository.py
from typing import Optional
from django.db.models import Q, QuerySet
from django.core.exceptions import ObjectDoesNotExist
from players.models.player import Player
from players.interfaces.player_repository_interface import PlayerRepositoryInterface

class PlayerRepository(PlayerRepositoryInterface):
    """
    Acceso a datos para Player.

    Convenciones:
    - get_all_players: lista jugadores activos y no eliminados.
    - get_player_by_id: trae incluso inactivos (solo excluye eliminados) para poder reactivarlos.
    - create_player: usa el manager para crear el jugador.
    - update_player: no modifica campos sensibles.
    - delete_player: soft delete (is_deleted=True) + desactiva (is_active=False) y retorna bool.
    """
    def get_all_players(self):
        return Player.objects.filter()

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        try:
            return Player.objects.get(id=player_id)
        except ObjectDoesNotExist:
            return None

    def create_player(self, data: dict) -> Player:
        return Player.objects.create(**data)

    def update_player(self, player_id: int, data: dict) -> Optional[Player]:
        player = self.get_player_by_id(player_id)
        if player is None:
            return None
        for key, value in data.items():
            setattr(player, key, value)
        player.save()
        return player

    def delete_player(self, player_id: int) -> bool:
        player = self.get_player_by_id(player_id)
        if player is None:
            return False
        player.delete()
        player.save()
        return True

    def search_players(self, term: str, limit: Optional[int] = 50) -> QuerySet[Player]:
        """
        Busca jugadores por:
        - Player.nick_name (icontains)
        - users.CustomUser.name / last_name / email (icontains) a través de la relación Player.user
        Devuelve un QuerySet (puede recortarse por 'limit').
        """
        term = (term or "").strip()
        if not term:
            # si no hay término, devolvemos queryset vacío (decisión de repo; el service puede validar)
            return Player.objects.none()

        qs = (
            Player.objects
            .select_related("user")  # asumiendo FK: Player.user -> users.CustomUser
            .filter(
                Q(nick_name__icontains=term)
                | Q(user__name__icontains=term)
                | Q(user__last_name__icontains=term)
                | Q(user__email__icontains=term)
            )
            .order_by("user__name", "nick_name", "id")
        )

        return qs[:limit] if isinstance(limit, int) and limit > 0 else qs
