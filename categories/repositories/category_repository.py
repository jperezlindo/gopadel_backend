# categories/repositories/category_repository.py
from typing import Optional, List
from django.db.models import QuerySet
from categories.models.category import Category


class CategoryRepository:
    """
    Repositorio de acceso a datos para Category.

    Objetivo:
    - Encapsular todo el acceso ORM en un solo lugar para no duplicar filtros/ordenamientos
      en services o controllers.
    - Proveer una API predecible (list/get_by_id/get_active_by_id) fácil de testear y extender.
    - Mantener un lugar único donde optimizar con select_related/prefetch_related si hace falta.
    """

    # Lista blanca de campos permitidos para ordenar desde parámetros externos.
    # Mantener controlado evita inyección de ordenamientos arbitrarios que rompan índices.
    _ALLOWED_ORDER_FIELDS: List[str] = ["id", "name", "-id", "-name"]

    def _base_qs(self) -> QuerySet[Category]:
        """
        Devuelvo el queryset base con el orden por defecto.
        Si mañana agrego relaciones (ej. owner), optimizo acá con:
            .select_related("owner")
            .prefetch_related("algo_m2m")
        De esta manera no tengo que repetir optimizaciones en cada método.
        """
        return Category.objects.all().order_by("id")

    def list(
        self,
        *,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> QuerySet[Category]:
        """
        Devuelvo un QuerySet de categorías filtrado/ordenado.

        Parámetros:
        - is_active: si viene, filtro exacto por estado True/False.
        - search: búsqueda por nombre con icontains (parcial y case-insensitive).
        - order_by: campo de orden permitido en _ALLOWED_ORDER_FIELDS (protege contra inyecciones).

        Decisión:
        - Retorno QuerySet para que la capa DRF lo pagine de forma eficiente sin materializar en memoria.
        """
        qs = self._base_qs()

        # Filtro por estado activo/inactivo solo si el valor fue provisto (None = sin filtro)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        # Búsqueda por nombre; uso strip() para evitar espacios extra que afecten el match
        if search:
            qs = qs.filter(name__icontains=search.strip())

        # Ordenamiento controlado: aplico solo si el valor está en la lista blanca
        if order_by:
            if order_by in self._ALLOWED_ORDER_FIELDS:
                qs = qs.order_by(order_by)
            else:
                # Si piden un campo no permitido, mantengo el orden por defecto sin romper el flujo
                # (alternativa: lanzar ValidationError para avisar explícitamente al caller).
                pass

        return qs

    def get_by_id(self, pk: int) -> Optional[Category]:
        """
        Obtengo una categoría por su PK.
        Devuelvo None si no existe para que la capa de servicio decida cómo responder (p. ej. 404).
        """
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get_active_by_id(self, pk: int) -> Optional[Category]:
        """
        Obtengo una categoría activa por PK.
        Útil cuando necesito garantizar que el recurso esté habilitado sin repetir filtros.
        """
        try:
            return Category.objects.get(pk=pk, is_active=True)
        except Category.DoesNotExist:
            return None
