# users/schemas/change_password_serializer.py
from typing import Any, Dict
from rest_framework import serializers

class ChangePasswordSerializer(serializers.Serializer):
    """
    Valido el payload para cambio de contraseña.

    Reglas clave:
    - Admin (is_staff / is_superuser): no requiere old_password.
    - Usuario final: requiere old_password y debe ser correcto.
    - old_password y new_password no pueden ser iguales.
    - La verificación de si el actor puede cambiar la password de otro usuario
      se realiza en la capa de services (regla de negocio).
    """
    # Mantengo min_length=6 para compatibilidad con el resto del sistema.
    old_password = serializers.CharField(
        write_only=True,
        min_length=6,
        required=False,
        allow_blank=False,
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=6,
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplico validaciones cruzadas con contexto:
        - actor: request.user
        - target_user: usuario al que se le cambia la contraseña
        """
        actor = self.context.get("actor")          # request.user
        target_user = self.context.get("target_user")  # instancia objetivo

        # Si no es admin, se exige old_password (el service además verifica self vs other).
        require_old = not getattr(actor, "is_staff", False) and not getattr(actor, "is_superuser", False)

        old_pwd = attrs.get("old_password")
        new_pwd = attrs.get("new_password")

        # Exijo old_password para usuarios no admin.
        if require_old and not old_pwd:
            raise serializers.ValidationError({"old_password": "Old password is required."})

        # Verifico old_password contra el hash del target.
        if old_pwd and target_user and not target_user.check_password(old_pwd):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        # Impido reutilizar la misma contraseña.
        if old_pwd and new_pwd and old_pwd == new_pwd:
            raise serializers.ValidationError({"new_password": "New password must be different from old password."})

        return attrs
