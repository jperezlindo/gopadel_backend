# users/schemas/change_password_serializer.py
from typing import Any, Dict
from rest_framework import serializers

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=6, required=False, allow_blank=False)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        actor = self.context.get("actor")            # request.user
        target_user = self.context.get("target_user")  # instancia a modificar

        require_old = not getattr(actor, "is_staff", False) and not getattr(actor, "is_superuser", False)
        old_pwd = attrs.get("old_password")
        new_pwd = attrs.get("new_password")

        if require_old and not old_pwd:
            raise serializers.ValidationError({"old_password": "Old password is required."})

        if old_pwd and target_user and not target_user.check_password(old_pwd):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        if old_pwd and new_pwd and old_pwd == new_pwd:
            raise serializers.ValidationError({"new_password": "New password must be different from old password."})

        return attrs
