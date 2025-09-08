# users/schemas/user_serializer.py
from typing import Any, Dict, Optional
from django.contrib.auth import get_user_model
from rest_framework import serializers

from facilities.models import Facility
from cities.models import City
from roles.models import Rol

from players.schemas.player_serializer import PlayerMiniSerializer

User = get_user_model()


# ---------- Read Serializer (show/list) ----------
class UserSerializer(serializers.ModelSerializer):
    facility_id = serializers.IntegerField(source='facility.id', read_only=True)
    city_id = serializers.IntegerField(source='city.id', read_only=True)
    rol_id = serializers.IntegerField(source='rol.id', read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    player = PlayerMiniSerializer(read_only=True)  # mini para no cargar todo Player

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "last_name",
            "email",
            "birth_day",
            "avatar",
            "is_active",
            "is_deleted",
            "is_staff",
            "created_at",
            "updated_at",
            "facility_id",
            "city_id",
            "rol_id",
            "player",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "facility_id",
            "city_id",
            "rol_id",
            "is_deleted",
            "is_staff",
        ]


# ---------- Create Serializer ----------
class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    # Aceptamos IDs y DRF los mapea a las FKs (nombres *_id en payload)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        required=False,
        allow_null=True,
        write_only=True,
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source="city",
        required=False,
        allow_null=True,
        write_only=True,
    )
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        source="rol",
        required=False,
        allow_null=True,
        write_only=True,
    )

    # Flags permitidos en creación (el front puede enviarlos)
    is_active = serializers.BooleanField(required=False, default=True)
    is_deleted = serializers.BooleanField(required=False, default=False)
    is_staff = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = User
        fields = [
            "name",
            "last_name",
            "email",
            "password",
            "birth_day",
            "avatar",
            "is_active",
            "is_deleted",
            "is_staff",
            "facility_id",
            "city_id",
            "rol_id",
        ]

    def validate_email(self, value: str) -> str:
        v = (value or "").strip().lower()
        if User.objects.filter(email__iexact=v).exists():
            # Mensaje claro para la UI
            raise serializers.ValidationError("Este email ya está registrado.")
        return v

    def create(self, validated_data: Dict[str, Any]) -> User:  # type: ignore
        password = validated_data.pop("password")
        # create_user hashea password y setea defaults coherentes
        user = User.objects.create_user(password=password, **validated_data)
        return user


# ---------- Update/Patch Serializer ----------
class UpdateUserSerializer(serializers.ModelSerializer):
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        required=False,
        allow_null=True,
        write_only=True,
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source="city",
        required=False,
        allow_null=True,
        write_only=True,
    )
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        source="rol",
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "name",
            "last_name",
            "email",
            "birth_day",
            "avatar",
            "is_active",
            "is_deleted",
            "is_staff",
            "facility_id",
            "city_id",
            "rol_id",
        ]
        # Todos opcionales para PATCH/PUT (la vista decide partial)
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate_email(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        v = value.strip().lower()
        qs = User.objects.filter(email__iexact=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return v

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:  # type: ignore
        # No manejamos password acá (endpoint aparte)
        for field, val in validated_data.items():
            setattr(instance, field, val)
        instance.save()
        return instance
