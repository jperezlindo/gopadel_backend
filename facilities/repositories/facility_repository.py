# facilities/repositories/facility_repository.py
from typing import Iterable, Optional
from django.db.models import Q, QuerySet
from facilities.models import Facility


class FacilityRepository:
    """
    Centralizo acceso al ORM de Facility.
    - Por defecto oculto soft-deleted (is_deleted=False).
    - Expondo helpers de búsqueda, listado y cambios de estado.
    """

    def _base_qs(self) -> QuerySet:
        return Facility.objects.filter(is_deleted=False)

    def _base_qs_including_deleted(self) -> QuerySet:
        return Facility.objects.all()

    # -------- Listado / búsqueda --------
    def list(
        self,
        *,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        ordering: Optional[Iterable[str]] = None,
    ) -> QuerySet:
        qs = self._base_qs_including_deleted() if include_deleted else self._base_qs()

        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        if search:
            s = search.strip()
            if s:
                qs = qs.filter(
                    Q(name__icontains=s) |
                    Q(address__icontains=s)
                )

        if ordering:
            qs = qs.order_by(*ordering)

        return qs

    # -------- Obtención puntual --------
    def get_by_id(self, facility_id: int, *, include_deleted: bool = False) -> Optional[Facility]:
        qs = self._base_qs_including_deleted() if include_deleted else self._base_qs()
        return qs.filter(pk=facility_id).first()

    # -------- Escritura --------
    def create(self, data: dict) -> Facility:
        """
        Creo facility con validaciones de modelo (clean en save).
        """
        return Facility.objects.create(**data)

    def update(self, instance: Facility, data: dict) -> Facility:
        """
        Actualizo campos simples. El model.save() dispara full_clean() del override.
        """
        for k, v in data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    # -------- Cambios de estado --------
    def soft_delete(self, instance: Facility) -> Facility:
        instance.is_deleted = True
        instance.is_active = False
        instance.save(update_fields=["is_deleted", "is_active", "updated_at"])
        return instance

    def restore(self, instance: Facility) -> Facility:
        instance.is_deleted = False
        instance.save(update_fields=["is_deleted", "updated_at"])
        return instance
