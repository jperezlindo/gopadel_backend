# roles/schemas/rol_serializer.py
from rest_framework import serializers
from roles.models import Rol

class RolMiniSerializer(serializers.ModelSerializer):
    """
    Expongo un serializer mínimo de Rol para usar en anidaciones
    (por ejemplo, cuando un endpoint de otra entidad necesita mostrar el rol).
    La idea es no sobrecargar la red ni la UI con campos innecesarios.
    """
    class Meta:
        model = Rol
        fields = ["id", "name"]
        read_only_fields = fields  # solo lectura: los roles son predefinidos


class RolSerializer(serializers.ModelSerializer):
    """
    Defino el serializer de lectura completo para listar/detallar roles.
    Mantengo solo lectura porque los roles están congelados (ADMIN, EMPLOYEE, PLAYER).
    """
    class Meta:
        model = Rol
        fields = [
            "id",
            "name",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields  # solo lectura para evitar modificaciones por API
