from rest_framework import serializers
from registrations.models.registration import Registration
from tournament_categories.models.tournament_category import TournamentCategory
from players.models.player import Player


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Read serializer
    """
    class Meta:
        model = Registration
        fields = [
            "id",
            "tournament_category",
            "player",
            "partner",
            "status",
            "payment_status",
            "paid_amount",
            "payment_reference",
            "comment",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CreateRegistrationSerializer(serializers.ModelSerializer):
    """
    Create serializer
    - partner es obligatorio (tu requerimiento).
    - Normaliza el orden (player < partner) para respetar el CheckConstraint del modelo.
    """
    tournament_category = serializers.PrimaryKeyRelatedField(
        queryset=TournamentCategory.objects.all()
    )
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    partner = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())

    class Meta:
        model = Registration
        fields = [
            "tournament_category",
            "player",
            "partner",
            "status",
            "payment_status",
            "paid_amount",
            "payment_reference",
            "comment",
            "is_active",
        ]

    def validate(self, attrs):
        p1 = attrs.get("player")
        p2 = attrs.get("partner")
        if p1 == p2:
            raise serializers.ValidationError("Player and partner must be different.")
        # Orden canónico: player < partner
        if p1.id > p2.id:
            attrs["player"], attrs["partner"] = p2, p1
        return attrs


class UpdateRegistrationSerializer(serializers.ModelSerializer):
    """
    Update/PATCH serializer (partial=True en el controller)
    - Si cambian player/partner, re-normaliza y valida que sean distintos.
    """
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), required=False)
    partner = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), required=False)

    class Meta:
        model = Registration
        fields = [
            "player",
            "partner",
            "status",
            "payment_status",
            "paid_amount",
            "payment_reference",
            "comment",
            "is_active",
        ]

    def validate(self, attrs):
        player = attrs.get("player", getattr(self.instance, "player", None))
        partner = attrs.get("partner", getattr(self.instance, "partner", None))
        if player == partner:
            raise serializers.ValidationError("Player and partner must be different.")
        if player and partner and player.id > partner.id:
            attrs["player"], attrs["partner"] = partner, player
        return attrs


__all__ = [
    "RegistrationSerializer",
    "CreateRegistrationSerializer",
    "UpdateRegistrationSerializer",
]
