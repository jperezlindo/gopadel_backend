from rest_framework import serializers

class ChangePasswordSerializer(serializers.Serializer):
    # El admin puede omitir old_password; el usuario común debe enviarlo
    old_password = serializers.CharField(write_only=True, min_length=6, required=False, allow_blank=False)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        old_pwd = attrs.get("old_password")
        new_pwd = attrs["new_password"]

        if old_pwd and old_pwd == new_pwd:
            raise serializers.ValidationError({"new_password": "New password must be different from old password."})

        return attrs
