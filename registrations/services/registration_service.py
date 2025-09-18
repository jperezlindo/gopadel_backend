# registrations/services/registration_service.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction

from registrations.repositories.registration_repository import RegistrationRepository
from registrations.models.registration import Registration


class RegistrationService:
    """
    Como criterio de arquitectura, centralizo la lógica de negocio acá y dejo al
    repositorio todo el acceso ORM. Mantengo las validaciones de dominio (duplicados,
    reglas de pareja y de horarios) y uso solo ValidationError para comunicar fallos.
    """

    def __init__(self, repo: RegistrationRepository | None = None):
        self.repo = repo or RegistrationRepository()

    # =========================
    #  Query methods
    # =========================
    def list(self, tournament_category_id: int | None = None):
        # Devuelvo la lista desde el repositorio; si en el futuro necesito filtros
        # adicionales, los agrego en este nivel para no contaminar el controller.
        return self.repo.list(tournament_category_id)

    def get(self, reg_id: int):
        reg = self.repo.get_by_id(reg_id)
        if not reg:
            # Prefiero no filtrar el mensaje para que sea claro para el front y para logs
            raise ValidationError("Registration no encontrada.")
        return reg

    # =========================
    #  Create
    # =========================
    @transaction.atomic
    def create(
        self,
        *,
        tournament_category,
        player,
        partner,
        paid_amount,
        payment_reference: str = "",
        comment: str = "",
        is_active: bool | None = None,
        payment_status: str | None = None,
        unavailability: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Creo una inscripción y guardo, si vienen, sus indisponibilidades horarias de lunes a viernes.
        Reglas de negocio aplicadas:
          - Un jugador no puede duplicarse en la misma TC.
          - Un partner no puede duplicarse en la misma TC.
          - Una pareja (player, partner) no puede repetirse en la misma TC (ni en orden inverso).
          - Validación de payload de indisponibilidades:
              * day_of_week en 0..4 (lunes-viernes).
              * start_time < end_time.
              * sin duplicados exactos.
              * sin solapes intradía.
          - Validación de modelo con full_clean antes de persistir.
        Nota: solapes frente a slots existentes no aplica en create (no hay existentes). En update
        será donde cruce con los ya guardados.
        """
        # Normalizo IDs por si vienen instancias o enteros
        tc_id = tournament_category.id if hasattr(tournament_category, "id") else int(tournament_category)
        player_id = player.id if hasattr(player, "id") else int(player)
        partner_id = partner.id if hasattr(partner, "id") else int(partner)

        # Reglas de duplicidad a nivel dominio
        if self.repo.exists_player_in_tc(tc_id, player_id):
            raise ValidationError("El jugador ya está inscripto en esta categoría de torneo.")
        if self.repo.exists_partner_in_tc(tc_id, partner_id):
            raise ValidationError("El partner ya está inscripto en esta categoría de torneo.")
        if self.repo.exists_pair_in_tc(tc_id, player_id, partner_id):
            # Importante: el repositorio debe considerar orden inverso
            raise ValidationError("Esta pareja ya está inscripta en esta categoría (o en orden inverso).")

        # Valido y normalizo bloques de indisponibilidad (lunes a viernes)
        slots: List[Dict[str, Any]] = self._validate_and_normalize_unavailability(unavailability)

        # Construyo el payload de creación
        data = {
            "tournament_category": tournament_category,
            "player": player,
            "partner": partner,
            "paid_amount": paid_amount,
            "payment_reference": (payment_reference or "").strip(),
            "comment": (comment or "").strip(),
            "is_active": True if is_active is None else bool(is_active),
            "payment_status": (payment_status or ""),
        }

        # Valido modelo con reglas de Django antes de persistir
        tmp = Registration(**data)
        tmp.full_clean()

        # Persiste inscripción + slots bajo transacción
        reg = self.repo.create(**data)

        if slots:
            # Delego en el repositorio la persistencia masiva de slots
            # Requisito: implementar repo.add_unavailability(reg, slots: List[dict])
            self.repo.add_unavailability(reg, slots) # type: ignore

        return reg

    # =========================
    #  Delete
    # =========================
    def delete(self, reg_id: int):
        reg = self.get(reg_id)
        self.repo.delete(reg)
        return True

    # =========================
    #  Helpers (privados)
    # =========================
    def _validate_and_normalize_unavailability(
        self, unavailability: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Valido estructura y reglas básicas de los bloques de indisponibilidad y devuelvo
        una versión normalizada lista para persistir por el repositorio.

        Formato esperado por bloque:
          { "day_of_week": int(0..4), "start_time": "HH:MM[:SS]", "end_time": "HH:MM[:SS]" }

        Aclaro: no transformo strings a time aquí para no acoplarme al parser; DRF ya valida
        tipos en el serializer. Acá asumo que vienen objetos dateutil/py; si llegaran strings,
        el repositorio/serializer debe convertirlos.
        """
        if not unavailability:
            return []

        # a) Validación de dominio básica y construcción de estructura por DOW
        by_dow: Dict[int, List[Tuple[Any, Any]]] = {}
        seen_exact: set[Tuple[int, Any, Any]] = set()
        normalized: List[Dict[str, Any]] = []

        for idx, blk in enumerate(unavailability):
            # Obtengo campos
            try:
                dow = int(blk.get("day_of_week")) # type: ignore
                start = blk.get("start_time")
                end = blk.get("end_time")
            except Exception:
                raise ValidationError(f"Bloque de indisponibilidad inválido en la posición {idx}.")

            # day_of_week en lunes..viernes
            if dow < 0 or dow > 4:
                raise ValidationError("El día debe estar entre 0 (lunes) y 4 (viernes).")

            # start < end (comparo objetos time; si fueran strings, DRF ya fallaría antes)
            if not (start and end and start < end):
                raise ValidationError("La hora de inicio debe ser menor que la hora de fin.")

            # duplicado exacto
            key = (dow, start, end)
            if key in seen_exact:
                raise ValidationError("Hay bloques de indisponibilidad duplicados.")
            seen_exact.add(key)

            by_dow.setdefault(dow, []).append((start, end))
            normalized.append({"day_of_week": dow, "start_time": start, "end_time": end})

        # b) Detección de solapes intradía (simple y clara)
        for dow, ranges in by_dow.items():
            ranges.sort(key=lambda r: r[0])  # ordeno por start_time
            prev_start, prev_end = None, None
            for start, end in ranges:
                if prev_start is None:
                    prev_start, prev_end = start, end
                    continue
                if start < prev_end:
                    raise ValidationError(f"Se detectó solape de horarios en el día {dow}.")
                prev_start, prev_end = start, end

        return normalized
