# players/schemas/player_serializer.py
from typing import Any, Dict, Optional
from rest_framework import serializers
from players.models.player import Player

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
            'is_active',
            'created_at',
            'updated_at',
            'user_id',
            'category_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_id', 'category_id']

class CreatePlayerSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        source='user',
        write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Player
        fields = [
            'nick_name',
            'position',
            'level',
            'is_active',
            'user_id',
            'category_id'
        ]

    def validate_nick_name(self, value: str) -> str:
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nick name no puede estar vacío.")
        if len(v) > 30:
            raise serializers.ValidationError("El nick name debe tener como máximo 50 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        position = attrs.get('position')
        if position not in ['DRIVE', 'REVEZ']:
            raise serializers.ValidationError("La posición debe ser: 'DRIVE' o 'REVEZ'.")
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Player:
        # validated_data ya trae 'user' y 'category' (no 'user_id' ni 'category_id') por el source del field
        return Player.objects.create(**validated_data)

class UpdatePlayerSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        source='user',
        write_only=True
    )
    
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Player
        fields = [
            'nick_name',
            'position',
            'level',
            'is_active',
            'user_id',
            'category_id'
        ]
        read_only_fields = ['user_id', 'category_id']

    def validate_nick_name(self, value: str) -> str:
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nick name no puede estar vacío.")
        if len(v) > 30:
            raise serializers.ValidationError("El nick name debe tener como máximo 30 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        position = attrs.get('position')
        if position not in ['DRIVE', 'REVEZ']:
            raise serializers.ValidationError("La posición debe ser: 'DRIVE' o 'REVEZ'.")
        return attrs

    def update(self, instance: Player, validated_data: Dict[str, Any]) -> Player:
        instance.nick_name = validated_data.get('nick_name', instance.nick_name)
        instance.position = validated_data.get('position', instance.position)
        instance.level = validated_data.get('level', instance.level)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance