# roles/repositories/rol_repository.py
from typing import Optional, Iterable
from django.db.models import QuerySet
from roles.models import Rol


class RolRepository:
    """
    Centralizo el acceso a datos de Roles. Este repo es READ-ONLY porque los
    roles del sistema están predefinidos y no se permite crearlos ni editarlos
    vía API (solo ADMIN/EMPLOYEE/PLAYER). La escritura, si alguna vez hiciera
    falta (seed inicial), se resuelve con un management command separado.

    Decisiones:
    - Excluyo por defecto los roles con soft-delete (is_deleted=True).
    - Expongo helpers para listado/obtención y para validar nombres de rol.
    - No implemento create/update/delete en este repo.
    """

    # Conjunto “congelado” de roles válidos que el sistema reconoce hoy.
    FROZEN_ROLES: tuple[str, ...] = ("ADMIN", "EMPLOYEE", "PLAYER")

    # =========================
    # QuerySets base y helpers
    # =========================
    def _base_qs(self) -> QuerySet:
        """
        Devuelvo el queryset base excluyendo soft-deleted.
        Este QS es el punto de partida para todas las lecturas de roles.
        """
        return Rol.objects.filter(is_deleted=False)

    # =========================
    # Listado
    # =========================
    def list_all(
        self,
        *,
        include_inactive: bool = True,
        ordering: Optional[Iterable[str]] = None,
    ) -> QuerySet:
        """
        Listo roles del sistema.
        - include_inactive=True: devuelve activos e inactivos (pero no borrados).
          Si se quisiera ocultar inactivos en UI, setear include_inactive=False.
        - ordering: permite customizar el orden (por defecto, el Meta.ordering = ["name"]).
        """
        qs = self._base_qs()
        if not include_inactive:
            qs = qs.filter(is_active=True)

        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def list_active(self) -> QuerySet:
        """
        Devuelvo solo los roles activos (y no borrados).
        Útil para poblar dropdowns en UI.
        """
        return self._base_qs().filter(is_active=True)

    # =========================
    # Obtención puntual
    # =========================
    def get_by_id(self, rol_id: int) -> Optional[Rol]:
        """
        Busco un rol por PK respetando soft-delete.
        Devuelvo None si no existe.
        """
        return self._base_qs().filter(pk=rol_id).first()

    def get_by_name(self, name: str, *, case_insensitive: bool = True) -> Optional[Rol]:
        """
        Busco un rol por nombre. Por defecto lo hago case-insensitive
        para ser tolerante con la entrada del cliente/admin.
        """
        n = (name or "").strip()
        if not n:
            return None
        qs = self._base_qs()
        return (qs.filter(name__iexact=n).first() if case_insensitive
                else qs.filter(name=n).first())

    # =========================
    # Validación de dominio
    # =========================
    def is_valid_role_name(self, name: str) -> bool:
        """
        Valido si el nombre propuesto pertenece al conjunto de roles congelados.
        Esta verificación es útil en services para reforzar reglas de negocio.
        """
        return (name or "").strip().upper() in self.FROZEN_ROLES

    # =========================
    # Notas sobre seed
    # =========================
    # Para el seed inicial de roles (crear si faltan), se recomienda un
    # management command tipo:
    #
    #   from django.core.management.base import BaseCommand
    #   from roles.models import Rol
    #   from roles.repositories.rol_repository import RolRepository
    #
    #   class Command(BaseCommand):
    #       help = "Crea roles por defecto si no existen (ADMIN/EMPLOYEE/PLAYER)"
    #
    #       def handle(self, *args, **opts):
    #           repo = RolRepository()
    #           for name in repo.FROZEN_ROLES:
    #               Rol.objects.get_or_create(name=name, defaults={"is_active": True})
    #
    # Nota: se mantiene fuera del repo para respetar la política de “solo lectura” aquí.
