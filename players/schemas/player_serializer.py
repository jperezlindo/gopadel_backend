# players/schemas/player_serializer.py
from typing import Any, Dict, Optional
from rest_framework import serializers
from players.models.player import Player
from users.models.user import CustomUser
from categories.models.category import Category


# ------------------------------------------------------------
# Mini para anidar (lo usa Users). Mantengo el payload liviano.
# ------------------------------------------------------------
class PlayerMiniSerializer(serializers.ModelSerializer):
    """
    Serializer mínimo del Player para anidar en otros recursos sin sobrecargar.
    """
    class Meta:
        model = Player
        fields = ["id", "nick_name", "position", "level", "points"]
        read_only_fields = fields


# ------------------------------------------------------------
# Lectura (list/show)
# ------------------------------------------------------------
class PlayerSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura. Expongo IDs de relaciones como *_id para consumo simple.
    """
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


# ------------------------------------------------------------
# Creación
# ------------------------------------------------------------
class CreatePlayerSerializer(serializers.ModelSerializer):
    """
    Serializer de creación. Acepto user/category por *_id y DRF los mapea
    a las FKs reales vía source='*'. Aplico validaciones de negocio.
    """
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_active=True),
        source='user',
        write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True,
        required=False,
        allow_null=True,
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
        """
        Normalizo y valido longitud en línea con el modelo (max_length=30).
        """
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nick name no puede estar vacío.")
        if len(v) > 30:
            raise serializers.ValidationError("El nick name debe tener como máximo 30 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valido 'position' contra las choices del modelo (case-insensitive).
        """
        pos = attrs.get('position')
        if pos is not None:
            allowed = {c[0] for c in Player.position_choices}  # {'REVES','DRIVE'}
            if str(pos).upper() not in allowed:
                raise serializers.ValidationError({"position": "La posición debe ser: 'REVES' o 'DRIVE'."})
            attrs['position'] = str(pos).upper()
        # Trim básico de nick
        if 'nick_name' in attrs:
            attrs['nick_name'] = attrs['nick_name'].strip()
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Player:
        """
        Creo el Player. El modelo hace full_clean() en save() para reforzar reglas.
        """
        return Player.objects.create(**validated_data)


# ------------------------------------------------------------
# Actualización (PUT/PATCH)
# ------------------------------------------------------------
class UpdatePlayerSerializer(serializers.ModelSerializer):
    """
    Serializer de actualización. Permito (opcional) cambiar user/category;
    si se quiere bloquear, basta con quitar estos campos.
    """
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
        required=False,
        allow_null=True,
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
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate_nick_name(self, value: str) -> str:
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nick name no puede estar vacío.")
        if len(v) > 30:
            raise serializers.ValidationError("El nick name debe tener como máximo 30 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Normalizo/corrijo case de position si viene
        pos = attrs.get('position')
        if pos is not None:
            allowed = {c[0] for c in Player.position_choices}  # {'REVES','DRIVE'}
            if str(pos).upper() not in allowed:
                raise serializers.ValidationError({"position": "La posición debe ser: 'REVES' o 'DRIVE'."})
            attrs['position'] = str(pos).upper()
        if 'nick_name' in attrs and isinstance(attrs['nick_name'], str):
            attrs['nick_name'] = attrs['nick_name'].strip()
        return attrs

    def update(self, instance: Player, validated_data: Dict[str, Any]) -> Player:
        """
        Aplico cambios campo a campo. El save() del modelo dispara full_clean().
        """
        for field in ['nick_name', 'position', 'level', 'points', 'is_active', 'user', 'category']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


# ------------------------------------------------------------
# Búsqueda (payload liviano con datos del user)
# ------------------------------------------------------------
class PlayerSearchSerializer(serializers.ModelSerializer):
    """
    Serializer específico para endpoints de búsqueda.
    Incluye datos básicos del usuario para mostrar resultados útiles en UI.
    """
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
        read_only_fields = fields
