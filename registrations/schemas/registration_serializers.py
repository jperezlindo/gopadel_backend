# registrations/schemas/registration_serializers.py
from rest_framework import serializers
from registrations.models.registration import Registration
from tournament_categories.models import TournamentCategory  # ajusta si tu app se llama distinto


class RegistrationReadSerializer(serializers.ModelSerializer):
    tournament_category_id = serializers.IntegerField(source="tournament_category.id", read_only=True)
    player_id = serializers.IntegerField(source="player.id", read_only=True)
    partner_id = serializers.IntegerField(source="partner.id", read_only=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "tournament_category_id",
            "player_id",
            "partner_id",
            "paid_amount",
            "payment_reference",
            "comment",
            "is_active",         # 👈 agregado
            "payment_status",    # 👈 agregado
            "created_at",
            "updated_at",        # 👈 agregado (solo lectura)
        ]
        read_only_fields = [
            "id",
            "tournament_category_id",
            "player_id",
            "partner_id",
            "created_at",
            "updated_at",
        ]


class RegistrationWriteSerializer(serializers.ModelSerializer):
    # Escritura estricta con PKs
    tournament_category = serializers.PrimaryKeyRelatedField(
        queryset=TournamentCategory.objects.all()
    )
    player = serializers.PrimaryKeyRelatedField(
        queryset=Registration._meta.get_field("player").remote_field.model.objects.all()
    )
    partner = serializers.PrimaryKeyRelatedField(
        queryset=Registration._meta.get_field("partner").remote_field.model.objects.all()
    )

    # Campos nuevos habilitados para escritura
    is_active = serializers.BooleanField(required=False)
    payment_status = serializers.CharField(required=False, allow_blank=True, max_length=50)

    class Meta:
        model = Registration
        fields = [
            "tournament_category",
            "player",
            "partner",
            "paid_amount",
            "payment_reference",
            "comment",
            "is_active",        # 👈 nuevo
            "payment_status",   # 👈 nuevo
        ]

    def validate(self, attrs):
        tc = attrs.get("tournament_category")
        player = attrs.get("player")
        partner = attrs.get("partner")
        paid_amount = attrs.get("paid_amount")

        # 1) player != partner (en DB ya hay CheckConstraint; validamos también acá para UX)
        if player == partner:
            raise serializers.ValidationError("El jugador y el partner no pueden ser la misma persona.")

        # 2) paid_amount == tc.price
        tc_price = getattr(tc, "price", None)
        if tc_price is None:
            raise serializers.ValidationError("La categoría del torneo no tiene precio configurado.")
        if paid_amount != tc_price:
            raise serializers.ValidationError("El monto pagado debe coincidir exactamente con el precio de la categoría.")

        return attrs
