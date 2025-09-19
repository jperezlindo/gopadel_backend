# categories/repositories/category_repository.py
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet
from categories.models.category import Category


class CategoryRepository:
    """
    Repositorio de acceso a datos para Category.

    Yo concentro acá todo el acceso ORM para:
    - No duplicar filtros/ordenamientos en services/controllers.
    - Exponer una API estable y fácil de testear.
    - Tener un único lugar donde optimizar select_related/prefetch_related si más adelante hace falta.
    """

    # Lista blanca de campos permitidos para ordenar desde parámetros externos.
    _ALLOWED_ORDER_FIELDS: List[str] = ["id", "name", "-id", "-name"]

    # ---------- QuerySets base ----------
    def _base_qs(self) -> QuerySet[Category]:
        """
        Devuelvo el queryset base con orden por defecto.
        Si mañana agrego relaciones, optimizo acá (select_related/prefetch_related).
        """
        return Category.objects.all().order_by("id")

    # ---------- Lectura ----------
    def list(
        self,
        *,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> QuerySet[Category]:
        """
        Devuelvo un QuerySet filtrado/ordenado.
        Mantengo QuerySet para que DRF pagine sin materializar en memoria.
        """
        qs = self._base_qs()

        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        if search:
            qs = qs.filter(name__icontains=search.strip())

        if order_by:
            if order_by in self._ALLOWED_ORDER_FIELDS:
                qs = qs.order_by(order_by)
            else:
                # Si piden un campo no permitido, mantengo el orden por defecto (o podría lanzar error).
                pass

        return qs

    def get_by_id(self, pk: int) -> Optional[Category]:
        """
        Obtengo por PK. Devuelvo None si no existe: la capa de servicio decide (p. ej. 404).
        """
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get_active_by_id(self, pk: int) -> Optional[Category]:
        """
        Obtengo una categoría activa por PK. Útil cuando necesito asegurar el estado.
        """
        try:
            return Category.objects.get(pk=pk, is_active=True)
        except Category.DoesNotExist:
            return None

    # ---------- Escritura ----------
    def create(self, data: Dict[str, Any]) -> Category:
        """
        Creo y guardo una categoría. Asumo que el service ya validó con full_clean().
        """
        instance = Category(**{k: v for k, v in data.items() if k in {f.name for f in Category._meta.fields}})
        instance.save()
        return instance

    def save(self, instance: Category) -> Category:
        """
        Persisto cambios en una instancia existente. El service hace full_clean() antes.
        """
        instance.save()
        return instance

    def delete(self, instance: Category) -> None:
        """
        Borrado físico. Si más adelante quiero soft-delete, lo centralizo acá.
        """
        instance.delete()
