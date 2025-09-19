# tournaments/services/tournament_service.py
from typing import Any, Optional, Dict, List, Tuple
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError

from tournaments.repositories.tournament_repository import TournamentRepository
from tournaments.models.tournament import Tournament
from tournament_categories.models.tournament_category import TournamentCategory
from categories.models.category import Category  # Necesario para resolver category_id -> name


class TournamentService:
    """
    Orquesto reglas de negocio de Tournaments.
    Decisiones:
    - Cuando el recurso no existe, levanto DjangoValidationError con code="not_found"
      y payload consistente (listas) para que el handler lo mapee a HTTP 404.
    - Uso transacciones en create/update para mantener consistencia al editar categorías inline.
    - Refuerzo validaciones de dominio con full_clean() y checks explícitos (p. ej., price >= 0).
    - Normalizo el payload de categorías: permito `category_id` o `name`.
      Si viene solo `category_id`, obtengo el `name` desde Category para mantener unicidad (tournament + name).
    """

    def __init__(self, repository: Optional[TournamentRepository] = None):
        self.repository = repository or TournamentRepository()

    # =========================
    # Helpers internos
    # =========================
    def _resolve_category_name(self, category_id: Optional[int]) -> str:
        """
        Resuelvo el nombre de Category cuando solo recibo category_id.
        Devuelvo el name o lanzo un ValidationError claro si no existe.
        """
        if category_id is None:
            return ""
        category = Category.objects.filter(id=category_id).first()
        if not category:
            raise DjangoValidationError({"categories": [f"Category with id={category_id} not found."]})
        return (category.name or "").strip()

    def _validate_price_non_negative(self, price: Optional[float]) -> None:
        """
        Valido explícitamente que el precio sea >= 0 cuando venga en el payload.
        """
        if price is None:
            return
        try:
            if float(price) < 0:
                raise DjangoValidationError({"categories": ["Price must be greater than or equal to 0."]})
        except (TypeError, ValueError):
            raise DjangoValidationError({"categories": ["Price must be a valid number."]})

    def _normalize_create_item(self, tournament: Tournament, item: Dict) -> Tuple[TournamentCategory, str]:
        """
        Normalizo un item para creación:
        - Acepto `category_id` o `name` (o ambos). Si viene solo `category_id`, resuelvo name desde Category.
        - Si vienen ambos, priorizo el `name` del payload (lo asumo intencional).
        - Devuelvo la instancia sin guardar + el name normalizado (lower) para detectar duplicados.
        """
        category_id = item.get("category_id", None)
        # Compatibilidad: si el front envió `category`, lo trato como `category_id`.
        if category_id is None and "category" in item:
            category_id = item.get("category")

        raw_name = (item.get("name") or "").strip()
        if not raw_name and category_id is not None:
            raw_name = self._resolve_category_name(category_id)

        if not raw_name:
            raise DjangoValidationError({"categories": ["Category name is required (provide `name` or a valid `category_id`)."]})

        # Valido precio explícitamente
        self._validate_price_non_negative(item.get("price", None))

        # Armo la instancia en memoria (seteo FK por id para evitar fetch extra)
        inst = TournamentCategory(
            tournament=tournament,
            name=raw_name,
            price=item.get("price", 0),
            is_active=item.get("is_active", True),
            comment=item.get("comment"),
        )
        if category_id is not None:
            inst.category_id = category_id # type: ignore

        # Hago full_clean para detectar issues antes del bulk_create
        inst.full_clean()
        return inst, raw_name.strip().lower()

    def _normalize_update_item(
        self,
        instance: TournamentCategory,
        item: Dict,
        existing_names_lower: set,
        payload_names_seen: set,
    ) -> Tuple[TournamentCategory, Optional[str]]:
        """
        Normalizo un item para update:
        - Si se cambia `name` o se envía `category_id` sin `name`, derivo/uso el nombre según corresponda.
        - Valido price >= 0 si fue enviado.
        - Devuelvo la instancia lista para `bulk_update` + el name_lower resultante (si se cambia),
          para poder detectar duplicados payload+existentes antes de persistir.
        """
        new_name = None

        # Valido precio explícitamente si viene en el payload
        if "price" in item:
            self._validate_price_non_negative(item.get("price", None))

        # Si viene name, lo uso (prioridad al payload)
        if "name" in item and item["name"] is not None:
            new_name = (item["name"] or "").strip()

        # Si no viene name pero viene category_id, derivo name desde Category
        category_id = item.get("category_id", None)
        if category_id is None and "category" in item:
            category_id = item.get("category")

        if new_name is None and category_id is not None:
            new_name = self._resolve_category_name(category_id)

        # Aplico campos presentes
        if new_name is not None:
            name_lower = new_name.lower().strip()
            # Detección de duplicados a nivel payload (en caliente)
            if name_lower in payload_names_seen:
                raise DjangoValidationError({"categories": [f"Duplicated names in payload: {new_name}"]})
            payload_names_seen.add(name_lower)
            # Detección de colisión con existentes (excluyendo el propio registro si no cambió efectivamente)
            if name_lower != (instance.name or "").lower().strip() and name_lower in existing_names_lower:
                raise DjangoValidationError({"categories": [f"Name '{new_name}' already exists in this tournament."]})
            instance.name = new_name

        if "price" in item and item["price"] is not None:
            instance.price = item["price"]

        if "is_active" in item:
            instance.is_active = item["is_active"]

        if "comment" in item:
            instance.comment = item["comment"]

        # Permito reasignar category por id sin fetch
        if category_id is not None:
            instance.category_id = category_id # type: ignore

        # Valido la instancia final antes de meterla en bulk_update
        instance.full_clean()
        return instance, (new_name.lower().strip() if new_name is not None else None)

    # =========================
    # Lectura
    # =========================
    def list(self) -> Any:
        """
        Listado base. El repo ya hace select_related/prefetch para evitar N+1.
        (Si se necesitan filtros a futuro: search/is_active/facility_id, se pasan al repo.)
        """
        return self.repository.get_all_tournaments()

    def get(self, tournament_id: int) -> Tournament:
        """
        Obtengo un torneo por PK con relaciones precargadas.
        """
        instance = self.repository.get_tournament_by_id(tournament_id)
        if not instance:
            raise DjangoValidationError({"detail": ["Tournament not found."]}, code="not_found")
        return instance

    # =========================
    # Escritura
    # =========================
    @transaction.atomic
    def create(self, data: Dict) -> Tournament:
        """
        Creo torneo y, si viene `categories`, realizo creación inline.
        Reglas:
        - Valido duplicados por name dentro del payload post-normalización (case-insensitive).
        - Valido el torneo con full_clean() antes de persistir para evitar doble save.
        - Permito `category_id` o `name`; si viene solo `category_id`, derivo el `name` desde Category.
        """
        categories_payload: List[Dict] = data.pop("categories", []) or []

        # Valido el torneo ANTES de crear (evita doble save)
        tmp = Tournament(**data)
        tmp.full_clean()

        # Creo el torneo
        tournament = self.repository.create_tournament(data)

        # Si vinieron categorías, normalizo y creo en bloque
        if categories_payload:
            instances: List[TournamentCategory] = []
            seen_names_lower: set = set()

            for item in categories_payload:
                inst, name_lower = self._normalize_create_item(tournament, item)
                # Duplicados en el propio payload (post-normalización)
                if name_lower in seen_names_lower:
                    raise DjangoValidationError({"categories": [f"Duplicated names in payload: {inst.name}"]})
                seen_names_lower.add(name_lower)
                instances.append(inst)

            try:
                TournamentCategory.objects.bulk_create(instances, ignore_conflicts=False)
            except IntegrityError as e:
                # Unicidad (tournament + name)
                raise DjangoValidationError({"categories": ["Tournament + name must be unique."]}) from e

        # Devuelvo con relaciones (usa repo.get)
        return self.get(tournament.id)  # type: ignore

    @transaction.atomic
    def update(self, tournament_id: int, data: Dict) -> Tournament:
        """
        Update del torneo con soporte de edición de categorías inline.
        Estrategia: upsert sincronizado
          - items con 'id' -> UPDATE
          - items sin 'id' -> CREATE
          - items existentes no enviados -> DELETE

        Mejoras:
        - Normalizo `name` desde `category_id` si no viene explícito.
        - Valido duplicados post-normalización contra payload y existentes antes de persistir.
        - Valido explícitamente price >= 0 cuando se envía.
        """
        categories_payload: Optional[List[Dict]] = data.pop("categories", None)

        # 1) Actualizo datos del torneo
        instance = self.repository.update_tournament(tournament_id, data)
        if not instance:
            raise DjangoValidationError({"detail": ["Tournament not found."]}, code="not_found")
        instance.full_clean()
        instance.save()

        # 2) Si no enviaron 'categories', no toco categorías
        if categories_payload is None:
            return self.get(instance.id)  # type: ignore

        # 3) Cargo existentes del torneo y armo un set de nombres existentes (lower)
        existing_qs = TournamentCategory.objects.select_related("category").filter(tournament_id=tournament_id)
        existing = list(existing_qs)
        existing_by_id = {tc.id: tc for tc in existing}  # type: ignore
        existing_names_lower = { (tc.name or "").lower().strip() for tc in existing }

        to_update: List[TournamentCategory] = []
        to_create: List[TournamentCategory] = []
        payload_ids: set[int] = set()

        # Llevo control de duplicados dentro del payload (post-normalización)
        payload_names_seen: set = set()

        # 4) Preparar updates/creates con validaciones
        for item in categories_payload:
            cid = item.get("id")

            if cid:
                # UPDATE
                if cid not in existing_by_id:
                    raise DjangoValidationError({"categories": [f"Category id {cid} does not belong to this tournament."]})

                tc = existing_by_id[cid]
                tc, maybe_new_name_lower = self._normalize_update_item(
                    instance=tc,
                    item=item,
                    existing_names_lower=existing_names_lower,
                    payload_names_seen=payload_names_seen,
                )
                to_update.append(tc)
                payload_ids.add(cid)

                # Si efectivamente cambié el nombre, actualizo el set de existentes para reflejar el nuevo valor
                if maybe_new_name_lower:
                    # Quito el viejo nombre y agrego el nuevo para validar siguientes items
                    old_lower = (existing_by_id[cid].name or "").lower().strip()
                    if old_lower in existing_names_lower:
                        existing_names_lower.remove(old_lower)
                    existing_names_lower.add(maybe_new_name_lower)

            else:
                # CREATE
                inst, name_lower = self._normalize_create_item(instance, item)

                # Duplicados en el payload
                if name_lower in payload_names_seen:
                    raise DjangoValidationError({"categories": [f"Duplicated names in payload: {inst.name}"]})
                payload_names_seen.add(name_lower)

                # Colisión con existentes
                if name_lower in existing_names_lower:
                    raise DjangoValidationError({"categories": [f"Name '{inst.name}' already exists in this tournament."]})

                to_create.append(inst)
                # Actualizo el set para validar próximos ítems
                existing_names_lower.add(name_lower)

        # 5) DELETE: categorías existentes no referenciadas en el payload
        to_delete_ids = [tc.id for tc in existing if tc.id not in payload_ids]  # type: ignore

        # 6) Persisto cambios
        try:
            if to_update:
                TournamentCategory.objects.bulk_update(
                    to_update, fields=["name", "price", "is_active", "comment", "category"]
                )
            if to_create:
                TournamentCategory.objects.bulk_create(to_create, ignore_conflicts=False)
            if to_delete_ids:
                TournamentCategory.objects.filter(id__in=to_delete_ids).delete()
        except IntegrityError as e:
            # Unicidad (tournament + name)
            raise DjangoValidationError({"categories": ["Tournament + name must be unique."]}) from e

        # 7) Devuelvo con relaciones
        return self.get(instance.id)  # type: ignore

    def delete(self, tournament_id: int) -> None:
        """
        Borrado físico del torneo. Si no existe, not_found.
        """
        ok = self.repository.delete_tournament(tournament_id)
        if not ok:
            raise DjangoValidationError({"detail": ["Tournament not found."]}, code="not_found")
