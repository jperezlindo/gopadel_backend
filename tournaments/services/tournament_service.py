# tournaments/services/tournament_service.py
from typing import Any, Optional, Dict, List
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError

from tournaments.repositories.tournament_repository import TournamentRepository
from tournaments.models.tournament import Tournament
from tournament_categories.models.tournament_category import TournamentCategory


class TournamentService:
    def __init__(self, repository: Optional[TournamentRepository] = None):
        self.repository = repository or TournamentRepository()

    def list(self) -> Any:
        return self.repository.get_all_tournaments()

    def get(self, tournament_id: int) -> Tournament:
        instance = self.repository.get_tournament_by_id(tournament_id)
        if not instance:
            raise DjangoValidationError({"detail": "Tournament not found."})
        return instance

    @transaction.atomic
    def create(self, data: Dict) -> Tournament:
        categories_payload: List[Dict] = data.pop("categories", []) or []

        # Validar duplicados por nombre en payload (case-insensitive)
        seen = set()
        dups = set()
        for c in categories_payload:
            n = (c.get("name") or "").strip().lower()
            if not n:
                raise DjangoValidationError({"categories": ["Category name is required."]})
            if n in seen:
                dups.add(n)
            seen.add(n)
        if dups:
            raise DjangoValidationError({"categories": [f"Duplicated names in payload: {', '.join(sorted(dups))}"]})

        tournament = self.repository.create_tournament(data)
        tournament.full_clean()
        tournament.save()

        if categories_payload:
            instances: List[TournamentCategory] = []
            for item in categories_payload:
                instance = TournamentCategory(
                    tournament=tournament,
                    name=(item.get("name") or "").strip(),
                    price=item.get("price", 0),
                    is_active=item.get("is_active", True),
                    comment=item.get("comment"),
                    category=item.get("category"),
                )
                instance.full_clean()
                instances.append(instance)
            try:
                TournamentCategory.objects.bulk_create(instances, ignore_conflicts=False)
            except IntegrityError as e:
                raise DjangoValidationError({"categories": ["Tournament + name must be unique."]}) from e

        return tournament

    @transaction.atomic
    def update(self, tournament_id: int, data: Dict) -> Tournament:
        """
        Update del torneo con soporte de edición de categorías inline.
        Estrategia: upsert sincronizado
          - items con 'id' -> UPDATE
          - items sin 'id' -> CREATE
          - items existentes no enviados -> DELETE
        """
        categories_payload: Optional[List[Dict]] = data.pop("categories", None)

        # 1) Actualizar campos del torneo
        instance = self.repository.update_tournament(tournament_id, data)
        if not instance:
            raise DjangoValidationError({"detail": "Tournament not found."})
        instance.full_clean()
        instance.save()

        # 2) Si no enviaron 'categories', no tocamos categorías
        if categories_payload is None:
            return instance

        # 3) Validar duplicados por nombre dentro del payload (case-insensitive)
        names_seen = set()
        for c in categories_payload:
            if "name" in c and c["name"] is not None:
                n = (c.get("name") or "").strip().lower()
            else:
                # si viene id sin name, tomaremos su nombre actual al construir updates
                n = None
            if n:
                if n in names_seen:
                    raise DjangoValidationError({"categories": [f"Duplicated names in payload: {n}"]})
                names_seen.add(n)

        # 4) Cargar existentes del torneo
        existing_qs = TournamentCategory.objects.select_related("category").filter(tournament_id=tournament_id)
        existing = list(existing_qs)
        existing_by_id = {tc.id: tc for tc in existing} # type: ignore

        to_update: List[TournamentCategory] = []
        to_create: List[TournamentCategory] = []
        payload_ids: set[int] = set()

        # 5) Preparar updates/creates
        for item in categories_payload:
            cid = item.get("id")
            if cid:
                # UPDATE
                if cid not in existing_by_id:
                    raise DjangoValidationError({"categories": [f"Category id {cid} does not belong to this tournament."]})
                tc = existing_by_id[cid]

                # Aplicar sólo campos presentes
                if "name" in item and item["name"] is not None:
                    tc.name = (item["name"] or "").strip()
                if "price" in item:
                    tc.price = item["price"] if item["price"] is not None else tc.price
                if "is_active" in item:
                    tc.is_active = item["is_active"]
                if "comment" in item:
                    tc.comment = item["comment"]
                if "category" in item:
                    tc.category = item["category"]  # puede ser None

                tc.full_clean()
                to_update.append(tc)
                payload_ids.add(cid)
            else:
                # CREATE (requiere name; el serializer ya lo valida)
                name = (item.get("name") or "").strip()
                inst = TournamentCategory(
                    tournament=instance,
                    name=name,
                    price=item.get("price", 0),
                    is_active=item.get("is_active", True),
                    comment=item.get("comment"),
                    category=item.get("category"),
                )
                inst.full_clean()
                to_create.append(inst)

        # 6) DELETE: categorías existentes no referenciadas en el payload
        to_delete_ids = [tc.id for tc in existing if tc.id not in payload_ids] # type: ignore

        # 7) Persistir cambios
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

        # 8) Devolver instancia fresquita con prefetch (usamos el repo)
        return self.get(instance.id) # type: ignore

    def delete(self, tournament_id: int) -> None:
        ok = self.repository.delete_tournament(tournament_id)
        if not ok:
            raise DjangoValidationError({"detail": "Tournament not found."})
