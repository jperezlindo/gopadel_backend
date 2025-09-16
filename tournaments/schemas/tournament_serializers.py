# tournaments/schemas/tournament_serializers.py
from typing import Any, Dict, Optional, cast
from rest_framework import serializers
from tournament_categories.schemas.tournament_category_serializer import (
    TournamentCategoryInlineInSerializer,
    TournamentCategoryInlineOutSerializer,
    TournamentCategoryInlineUpdateSerializer,  # 👈 nuevo import
)
from tournaments.models.tournament import Tournament
from facilities.models import Facility  # ajusta el import si tu app es distinta

# --------- Facility (brief) para anidar en lectura ---------
class FacilityBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "name", "address", "courts", "maps", "logo", "is_active"]

# --------- Read Serializer (show/list) ---------
class TournamentSerializer(serializers.ModelSerializer):
    facility_id = serializers.IntegerField(read_only=True)  # usa attr <fk>_id del modelo
    facility = FacilityBriefSerializer(read_only=True)      # 👈 anidado
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
            "facility",     # 👈 agregado
            "categories",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "facility_id", "facility", "categories"]

# --------- Create Serializer ---------
class CreateTournamentSerializer(serializers.ModelSerializer):
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
        v = (value or "").strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        if len(v) > 100:
            raise serializers.ValidationError("El nombre debe tener como máximo 100 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        date_start = attrs.get("date_start")
        date_end = attrs.get("date_end")
        if date_end and date_start and date_end < date_start:
            raise serializers.ValidationError(
                {"date_end": "La fecha de finalización no puede ser anterior a la fecha de inicio."}
            )
        return attrs

# --------- Update/Patch Serializer ---------
class UpdateTournamentSerializer(serializers.ModelSerializer):
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        required=False,
        write_only=True,
    )
    # 👇 edición de categorías
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
            "categories",  # 👈 agregado
        ]
        extra_kwargs = {
            "name": {"required": False},
            "date_start": {"required": False},
            "date_end": {"required": False},
            "is_active": {"required": False},
        }

    def validate_name(self, value: str) -> str:
        v = (value or "").strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        if len(v) > 100:
            raise serializers.ValidationError("El nombre debe tener como máximo 100 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        instance = cast(Optional[Tournament], getattr(self, "instance", None))
        date_start = attrs.get("date_start", getattr(instance, "date_start", None))
        date_end = attrs.get("date_end", getattr(instance, "date_end", None))
        if date_end and date_start and date_end < date_start:
            raise serializers.ValidationError(
                {"date_end": "La fecha de finalización no puede ser anterior a la fecha de inicio."}
            )
        return attrs
