# players/schemas/player_serializer.py
from typing import Any, Dict, Optional
from rest_framework import serializers
from players.models.player import Player
from users.models.user import CustomUser
from categories.models.category import Category


class PlayerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)

    class Meta:
        model = Player
        fields = [
            'id',
            'nick_name',
            'position',
            'level',
            'points',
            'is_active',
            'created_at',
            'updated_at',
            'user_id',
            'category_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_id', 'category_id']


class CreatePlayerSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_active=True),
        source='user',
        write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True,
    )

    class Meta:
        model = Player
        fields = [
            'nick_name',
            'position',
            'level',
            'points',
            'is_active',
            'user_id',
            'category_id'
        ]

    def validate_nick_name(self, value: str) -> str:
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nick name no puede estar vacío.")
        if len(v) > 50:
            raise serializers.ValidationError("El nick name debe tener como máximo 50 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        position = attrs.get('position')
        # Mantengo tus opciones tal como las venís usando
        if position not in ['DRIVE', 'REVEZ']:
            raise serializers.ValidationError("La posición debe ser: 'DRIVE' o 'REVEZ'.")
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Player:
        # validated_data ya trae 'user' y 'category' por el source de los campos
        return Player.objects.create(**validated_data)


class UpdatePlayerSerializer(serializers.ModelSerializer):
    # Si querés permitir cambiar user/category en update, dejá estos; si no, podés quitarlos.
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_active=True),
        source='user',
        write_only=True,
        required=False
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True,
        required=False
    )

    class Meta:
        model = Player
        fields = [
            'nick_name',
            'position',
            'level',
            'points',
            'is_active',
            'user_id',
            'category_id'
        ]

    def validate_nick_name(self, value: str) -> str:
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nick name no puede estar vacío.")
        if len(v) > 50:
            raise serializers.ValidationError("El nick name debe tener como máximo 50 caracteres.")
        return v

    def update(self, instance: Player, validated_data: Dict[str, Any]) -> Player:
        instance.nick_name = validated_data.get('nick_name', instance.nick_name)
        instance.position = validated_data.get('position', instance.position)
        instance.level = validated_data.get('level', instance.level)
        instance.points = validated_data.get('points', instance.points)
        instance.is_active = validated_data.get('is_active', instance.is_active)

        # Opcional: permitir actualizar relaciones si vinieron en el payload
        if 'user' in validated_data:
            instance.user = validated_data['user']
        if 'category' in validated_data:
            instance.category = validated_data['category']

        instance.save()
        return instance


# === Nuevo: Serializer para /players/search ===
class PlayerSearchSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Player
        fields = [
            'id',
            'nick_name',
            'position',
            'level',
            'points',
            'is_active',
            'user_id',
            'user_name',
            'user_last_name',
            'user_email',
        ]
