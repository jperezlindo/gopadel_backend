# cities/schemas/city_serializer.py
from typing import Any, Dict
from rest_framework import serializers
from cities.models import City


class CitySerializer(serializers.ModelSerializer):
    """
    Serializer de lectura (list/show).
    Exponer datos limpios y coherentes con la UI.
    """
    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "cod",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]


class CreateCitySerializer(serializers.ModelSerializer):
    """
    Serializer de creación.
    Responsabilidades:
    - Normalizar name/cod (trim y cod en mayúsculas).
    - Dejar is_active opcional (default True).
    - No expongo is_deleted (soft-delete lo maneja DELETE).
    """
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = City
        fields = [
            "name",
            "cod",
            "is_active",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Normalizo entradas de texto (refuerzo de clean() en el modelo)
        if "name" in attrs and isinstance(attrs["name"], str):
            attrs["name"] = attrs["name"].strip()
        if "cod" in attrs and isinstance(attrs["cod"], str):
            attrs["cod"] = attrs["cod"].strip().upper()
        return attrs


class UpdateCitySerializer(serializers.ModelSerializer):
    """
    Serializer de actualización (PUT/PATCH).
    - Todos los campos opcionales (la vista decide partial).
    - No manejo is_deleted aquí (soft-delete va por DELETE).
    """
    class Meta:
        model = City
        fields = [
            "name",
            "cod",
            "is_active",
            # "is_deleted" NO se expone acá
        ]
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if "name" in attrs and isinstance(attrs["name"], str):
            attrs["name"] = attrs["name"].strip()
        if "cod" in attrs and isinstance(attrs["cod"], str):
            attrs["cod"] = attrs["cod"].strip().upper()
        return attrs
