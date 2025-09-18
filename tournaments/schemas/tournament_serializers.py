# tournaments/schemas/tournament_serializers.py
from typing import Any, Dict, Optional, cast
from rest_framework import serializers

# Serializadores inline de categorías por torneo (se implementan en esa app)
from tournament_categories.schemas.tournament_category_serializer import (
    TournamentCategoryInlineInSerializer,
    TournamentCategoryInlineOutSerializer,
    TournamentCategoryInlineUpdateSerializer,  # edición parcial
)

from tournaments.models.tournament import Tournament
from facilities.models import Facility  # mantenemos este import para ser coherentes con el resto del proyecto


# --------- Facility (brief) para anidar en lectura ---------
class FacilityBriefSerializer(serializers.ModelSerializer):
    """
    Payload breve de Facility para embebido en lectura de torneos,
    evitando sobrecargar la red/UI.
    """
    class Meta:
        model = Facility
        fields = ["id", "name", "address", "courts", "maps", "logo", "is_active"]
        read_only_fields = fields


# --------- Read Serializer (show/list) ---------
class TournamentSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura:
    - facility_id: ID plano para consumo simple.
    - facility: objeto breve embebido (solo lectura).
    - categories: arreglo de categorías del torneo (solo lectura).
    """
    facility_id = serializers.IntegerField(read_only=True)  # usa <fk>_id del modelo
    facility = FacilityBriefSerializer(read_only=True)
    categories = TournamentCategoryInlineOutSerializer(
        source="tournament_categories",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Tournament
        fields = [
            "id",
            "name",
            "date_start",
            "date_end",
            "is_active",
            "created_at",
            "updated_at",
            "facility_id",
            "facility",
            "categories",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "facility_id",
            "facility",
            "categories",
        ]


# --------- Create Serializer ---------
class CreateTournamentSerializer(serializers.ModelSerializer):
    """
    Serializer de creación:
    - facility_id: FK requerida; DRF la mapea a 'facility' vía source.
    - categories: creación inline (opcional); se procesa en service al persistir.
    """
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        write_only=True,
    )
    categories = TournamentCategoryInlineInSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Tournament
        fields = [
            "name",
            "date_start",
            "date_end",
            "is_active",
            "facility_id",
            "categories",
        ]

    def validate_name(self, value: str) -> str:
        """
        Alineo con el modelo: mínimo 5, máximo 100, y trim.
        """
        v = (value or "").strip()
        if len(v) < 5:
            raise serializers.ValidationError("El nombre debe tener al menos 5 caracteres.")
        if len(v) > 100:
            raise serializers.ValidationError("El nombre debe tener como máximo 100 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reglas cruzadas:
        - date_end >= date_start
        - normalizo name (trim)
        """
        if "name" in attrs and isinstance(attrs["name"], str):
            attrs["name"] = attrs["name"].strip()

        date_start = attrs.get("date_start")
        date_end = attrs.get("date_end")
        if date_end and date_start and date_end < date_start:
            raise serializers.ValidationError(
                {"date_end": "La fecha de finalización no puede ser anterior a la fecha de inicio."}
            )
        return attrs


# --------- Update/Patch Serializer ---------
class UpdateTournamentSerializer(serializers.ModelSerializer):
    """
    Serializer de actualización:
    - Todos los campos son opcionales (la vista decide PUT vs PATCH).
    - facility_id opcional (si se permite mover el torneo de facility).
    - categories: edición inline (opcional); el service aplica upserts/bajas.
    """
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        required=False,
        write_only=True,
    )
    categories = TournamentCategoryInlineUpdateSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Tournament
        fields = [
            "name",
            "date_start",
            "date_end",
            "is_active",
            "facility_id",
            "categories",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "date_start": {"required": False},
            "date_end": {"required": False},
            "is_active": {"required": False},
        }

    def validate_name(self, value: str) -> str:
        """
        Misma normalización/reglas que en create.
        """
        v = (value or "").strip()
        if len(v) < 5:
            raise serializers.ValidationError("El nombre debe tener al menos 5 caracteres.")
        if len(v) > 100:
            raise serializers.ValidationError("El nombre debe tener como máximo 100 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valido fechas tomando en cuenta valores actuales de la instancia
        (útil para PATCH donde puede venir solo uno de los campos).
        """
        instance = cast(Optional[Tournament], getattr(self, "instance", None))

        if "name" in attrs and isinstance(attrs["name"], str):
            attrs["name"] = attrs["name"].strip()

        date_start = attrs.get("date_start", getattr(instance, "date_start", None))
        date_end = attrs.get("date_end", getattr(instance, "date_end", None))
        if date_end and date_start and date_end < date_start:
            raise serializers.ValidationError(
                {"date_end": "La fecha de finalización no puede ser anterior a la fecha de inicio."}
            )
        return attrs
