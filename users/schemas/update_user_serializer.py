# users/schemas/update_user_serializer.py

from rest_framework import serializers


class UpdateUserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    birth_day = serializers.DateField(required=False)
    avatar = serializers.URLField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    facility_id = serializers.IntegerField(required=False, allow_null=True)
    city_id = serializers.IntegerField(required=False, allow_null=True)
    rol_id = serializers.IntegerField(required=False, allow_null=True)
