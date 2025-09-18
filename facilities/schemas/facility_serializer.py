# facilities/schemas/facility_serializer.py
from typing import Any, Dict
from rest_framework import serializers
from facilities.models import Facility


class FacilitySerializer(serializers.ModelSerializer):
    """
    Serializer de lectura (list/show).
    Expongo los campos necesarios para UI, sin lógica extra.
    """
    class Meta:
        model = Facility
        fields = [
            "id",
            "name",
            "address",
            "courts",
            "maps",
            "logo",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]


class CreateFacilitySerializer(serializers.ModelSerializer):
    """
    Serializer de creación.
    Responsabilidades:
    - Validar campos básicos y formatos (URL ya se valida en model.clean()).
    - Dejar is_active opcional (default True).
    - No expongo is_deleted: lo maneja el soft-delete del controller.
    """
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Facility
        fields = [
            "name",
            "address",
            "courts",
            "maps",
            "logo",
            "is_active",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Trim básicos para evitar duplicados por espacios (refuerzo del clean())
        for k in ["name", "address", "maps", "logo"]:
            if k in attrs and isinstance(attrs[k], str):
                attrs[k] = attrs[k].strip()
        return attrs


class UpdateFacilitySerializer(serializers.ModelSerializer):
    """
    Serializer de actualización (PUT/PATCH).
    - Todos los campos opcionales (la vista decide partial).
    - No manejo is_deleted acá (soft-delete va por DELETE).
    """
    class Meta:
        model = Facility
        fields = [
            "name",
            "address",
            "courts",
            "maps",
            "logo",
            "is_active",
            # "is_deleted" NO se expone acá
        ]
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        for k in ["name", "address", "maps", "logo"]:
            if k in attrs and isinstance(attrs[k], str):
                attrs[k] = attrs[k].strip()
        return attrs
