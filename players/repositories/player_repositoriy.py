# players/repositories/player_repository.py
from typing import Any, Optional
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
