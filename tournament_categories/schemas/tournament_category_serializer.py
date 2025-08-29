# tournament_categories/schemas/tournament_category_serializer.py
from typing import Any, Dict
from rest_framework import serializers
from categories.models.category import Category  # Import explícito, igual que en el modelo


class TournamentCategoryInlineInSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para categorías inline dentro del POST de Tournament.
    """
    name = serializers.CharField(max_length=30)  # match con el modelo
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    is_active = serializers.BooleanField(required=False, default=True)
    comment = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )

    def validate_name(self, value: str) -> str:
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("Name is required.")
        return v


class TournamentCategoryInlineUpdateSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para UPDATE/PATCH:
    - Si viene 'id': se ACTUALIZA esa categoría del torneo.
    - Si NO viene 'id': se CREA una nueva categoría (requiere 'name').
    Campos son opcionales para permitir parches parciales por item.
    """
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=30, required=False)  # requerido sólo si no hay id (creación)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    is_active = serializers.BooleanField(required=False)
    comment = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Si no hay id (creación), exigimos name
        if not attrs.get("id") and not (attrs.get("name") or "").strip():
            raise serializers.ValidationError({"name": "Name is required when creating a new category."})
        # Normalizamos name si viene
        if "name" in attrs and attrs["name"] is not None:
            attrs["name"] = attrs["name"].strip()
        return attrs


class TournamentCategoryInlineOutSerializer(serializers.Serializer):
    """
    Serializer de SALIDA para devolver categorías del torneo en las respuestas de Tournament.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField()
    comment = serializers.CharField(allow_null=True)
    category_id = serializers.IntegerField(allow_null=True)
