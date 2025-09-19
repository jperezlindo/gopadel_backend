# categories/schemas/category_serializers.py
"""
Serializers de Categories.

Yo separo lectura de escritura para no romper el contrato del front:
- CategoryReadSerializer: solo lectura (list/get).
- CategoryCreateSerializer: validación de entrada para crear.
- CategoryUpdateSerializer: validación de entrada para actualizar parcial/total.
"""

from rest_framework import serializers
from categories.models.category import Category


class CategoryReadSerializer(serializers.ModelSerializer):
    """
    Serializer de **lectura** (read-only) usado para listar y mostrar categorías.
    """
    class Meta:
        model = Category
        fields = ("id", "name", "is_active")
        read_only_fields = ("id", "name", "is_active")


class CategoryCreateSerializer(serializers.Serializer):
    """
    Yo uso este serializer para crear categorías. Mantengo el payload minimal:
    - name: requerido, string no vacío (hago strip).
    - is_active: opcional (default=True).
    """
    name = serializers.CharField(max_length=20)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_name(self, value: str) -> str:
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("Name is required.")
        return v

    def create(self, validated_data):
        # No creo en el serializer; delego en el service (single source of truth).
        # DRF requiere este método, pero lo dejamos sin uso.
        raise NotImplementedError("Use CategoryService to create categories.")


class CategoryUpdateSerializer(serializers.Serializer):
    """
    Yo uso este serializer para actualizar categorías. Todo es opcional,
    pero si mandan `name`, lo valido como en create.
    """
    name = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def validate_name(self, value: str) -> str:
        # Permito null/blank en PATCH; si llega string, hago strip.
        if value is None:
            return value
        v = value.strip()
        # Si alguien manda "", lo interpreto como vacío explícito -> error;
        # si preferís permitirlo y tratarlo como None, cambiamos esto.
        if v == "":
            raise serializers.ValidationError("Name cannot be empty.")
        return v

    def update(self, instance, validated_data):
        # Igual que en create: no persisto acá; delego al service.
        raise NotImplementedError("Use CategoryService to update categories.")


__all__ = ["CategoryReadSerializer", "CategoryCreateSerializer", "CategoryUpdateSerializer"]
