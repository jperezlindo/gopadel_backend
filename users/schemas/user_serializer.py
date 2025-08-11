from rest_framework import serializers
from users.models.user import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'name',
            'last_name',
            'email',
            'birth_day',
            'avatar',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'facility_id',
            'city_id',
            'rol_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted']


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            'name',
            'last_name',
            'email',
            'password',
            'birth_day',
            'avatar',
            'facility_id',
            'city_id',
            'rol_id'
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
    def create(self, validated_data):
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        user = CustomUser.objects.create_user(**validated_data)
        return user
