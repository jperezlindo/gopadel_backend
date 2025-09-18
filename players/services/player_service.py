# players/services/player_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import QuerySet

from players.models.player import Player
from players.repositories.player_repository import PlayerRepository


class PlayerService:
    """
    Orquesto reglas de negocio para Players, manteniendo controllers livianos y
    el repositorio enfocado en ORM. Decisiones:
    - Cuando no existe el recurso, levanto DjangoValidationError con code="not_found"
      para que el custom_exception_handler lo mapee a HTTP 404.
    - En operaciones de escritura uso transaction.atomic() para asegurar atomicidad.
    - El borrado es FÍSICO (el modelo no tiene is_deleted).
    """

    def __init__(self, repository: Optional[PlayerRepository] = None):
        # Permito inyección de repo para tests.
        self.repository = repository or PlayerRepository()

    # =========================
    # Lectura
    # =========================
    def list(self) -> Any:
        """
        Devuelvo un QuerySet de jugadores activos (según repo).
        La vista se encarga de paginar/ordenar si aplica.
        """
        return self.repository.get_all_players()

    def get(self, player_id: int) -> Player:
        """
        Obtengo un jugador por PK. Si no existe, levanto not_found.
        """
        player = self.repository.get_player_by_id(player_id)
        if not player:
            raise DjangoValidationError({"detail": ["Player not found."]}, code="not_found")
        return player

    # =========================
    # Escritura
    # =========================
    def create(self, data: Dict) -> Player:
        """
        Creo un jugador y refuerzo validaciones de modelo con full_clean().
        """
        with transaction.atomic():
            player = self.repository.create_player(data)
            player.full_clean()
            player.save()
            return player

    def update(self, player_id: int, data: Dict) -> Player:
        """
        Actualizo campos simples del jugador. Si no existe, levanto not_found.
        """
        with transaction.atomic():
            player = self.repository.update_player(player_id, data)
            if not player:
                raise DjangoValidationError({"detail": ["Player not found."]}, code="not_found")
            player.full_clean()
            player.save()
            return player

    def delete(self, player_id: int) -> None:
        """
        Borrado FÍSICO del jugador. Si no existe, levanto not_found.
        """
        with transaction.atomic():
            ok = self.repository.delete_player(player_id)
            if not ok:
                raise DjangoValidationError({"detail": ["Player not found."]}, code="not_found")

    # =========================
    # Búsqueda
    # =========================
    def search(self, term: str, limit: Optional[int] = 50) -> QuerySet[Player]:
        """
        Busco jugadores por:
        - nick_name (Player)
        - name/last_name/email (CustomUser)
        Reglas:
        - Exijo al menos 2 caracteres para evitar scans inútiles.
        - Normalizo/limito el parámetro limit entre 1 y 200.
        """
        q = (term or "").strip()
        if len(q) < 2:
            raise DjangoValidationError({"detail": ["Search term must have at least 2 characters."]}, code="invalid")

        # Normalizo y acoto límite
        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = 50
            if limit <= 0:
                limit = 50
            if limit > 200:
                limit = 200

        return self.repository.search_players(q, limit=limit)
