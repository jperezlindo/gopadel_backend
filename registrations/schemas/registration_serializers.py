# registrations/schemas/registration_serializers.py
from typing import List, Dict, Any
from django.db import transaction
from rest_framework import serializers

from registrations.models import Registration, RegistrationUnavailability
from tournament_categories.models import TournamentCategory  # ajustar si cambia el nombre de la app


# ===============================
#  Serializer hijo (unavailability)
# ===============================
class RegistrationUnavailabilitySerializer(serializers.ModelSerializer):
    """
    Defino la forma de (day_of_week, start_time, end_time) para lectura/escritura.
    - day_of_week: 0..4 (lunes a viernes). Si en el futuro se quiere permitir sábados/domingos,
      se puede ampliar a 0..6 sin tocar el modelo, solo esta validación.
    - start_time < end_time: ya hay CheckConstraint en BD; acá refuerzo UX.
    - No valido solapes contra BD; eso lo resuelve el service con mayor contexto.
    """

    class Meta:
        model = RegistrationUnavailability
        fields = ["day_of_week", "start_time", "end_time"]

    def validate_day_of_week(self, value: int) -> int:
        # Restrinjo a días hábiles (0=lunes ... 4=viernes)
        if value < 0 or value > 4:
            raise serializers.ValidationError("El día debe estar entre 0 (lunes) y 4 (viernes).")
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        start = attrs.get("start_time")
        end = attrs.get("end_time")
        if start and end and not (start < end):
            raise serializers.ValidationError("La hora de inicio debe ser menor que la hora de fin.")
        return attrs


# ===============================
#  READ
# ===============================
class RegistrationReadSerializer(serializers.ModelSerializer):
    """
    Expongo IDs de FK y la lista de indisponibilidades horarias asociadas.
    Mantengo nombres *_id para consistencia con el front.
    """
    tournament_category_id = serializers.IntegerField(source="tournament_category.id", read_only=True)
    player_id = serializers.IntegerField(source="player.id", read_only=True)
    partner_id = serializers.IntegerField(source="partner.id", read_only=True)

    # Lista anidada de indisponibilidades
    unavailability = RegistrationUnavailabilitySerializer(many=True, read_only=True)

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
            "is_active",
            "payment_status",
            "unavailability",  # 👈 agregado
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tournament_category_id",
            "player_id",
            "partner_id",
            "created_at",
            "updated_at",
        ]


# ===============================
#  WRITE (create / update)
# ===============================
class RegistrationWriteSerializer(serializers.ModelSerializer):
    """
    Acepto PKs para las FKs y una lista `unavailability` con bloques (day_of_week, start_time, end_time).
    En create:
      - Creo la Registration y luego bulk_create de las indisponibilidades.
    En update:
      - Si viene la clave 'unavailability', reemplazo completamente (delete + bulk_create).
      - Si NO viene, no toco las indisponibilidades actuales.
    """
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

    # Lista opcional de bloques de indisponibilidad (lunes a viernes)
    unavailability = RegistrationUnavailabilitySerializer(many=True, required=False)

    class Meta:
        model = Registration
        fields = [
            "tournament_category",
            "player",
            "partner",
            "paid_amount",
            "payment_reference",
            "comment",
            "is_active",
            "payment_status",
            "unavailability",  # 👈 nuevo
        ]

    # --------------------
    # Validaciones de nivel serializer (UX)
    # --------------------
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mantengo validaciones de UX rápidas:
          - player != partner
          - paid_amount == tc.price
          - estructura básica de unavailability (sin solapes pesados)
        """
        tc = attrs.get("tournament_category", getattr(self.instance, "tournament_category", None))
        player = attrs.get("player", getattr(self.instance, "player", None))
        partner = attrs.get("partner", getattr(self.instance, "partner", None))
        paid_amount = attrs.get("paid_amount", getattr(self.instance, "paid_amount", None))

        # 1) player != partner
        if player and partner and player == partner:
            raise serializers.ValidationError("El jugador y el partner no pueden ser la misma persona.")

        # 2) paid_amount == tc.price
        if tc is None:
            raise serializers.ValidationError("Debe seleccionar una categoría de torneo válida.")
        tc_price = getattr(tc, "price", None)
        if tc_price is None:
            raise serializers.ValidationError("La categoría del torneo no tiene precio configurado.")
        if paid_amount is not None and paid_amount != tc_price:
            raise serializers.ValidationError("El monto pagado debe coincidir exactamente con el precio de la categoría.")

        # 3) Validación ligera de `unavailability` (si viene en el payload)
        unav: List[Dict[str, Any]] | None = attrs.get("unavailability")
        if unav is not None:
            # a) Validar duplicados exactos en el payload (para UX)
            seen = set()
            for blk in unav:
                dow = blk.get("day_of_week")
                st = blk.get("start_time")
                en = blk.get("end_time")
                key = (dow, st, en)
                if key in seen:
                    raise serializers.ValidationError("Hay bloques de indisponibilidad duplicados en la solicitud.")
                seen.add(key)

            # b) Validación básica de traslape dentro del mismo payload (misma DOW)
            #    Nota: uso comparación simple; reglas más complejas (márgenes, fusos)
            #    se manejarán en el service.
            by_dow: Dict[int, List[tuple]] = {}
            for blk in unav:
                dow = blk["day_of_week"]
                by_dow.setdefault(dow, []).append((blk["start_time"], blk["end_time"]))

            for dow, ranges in by_dow.items():
                # Ordeno por start_time para detectar solapes contiguos
                ranges.sort(key=lambda r: r[0])
                prev_start, prev_end = None, None
                for start, end in ranges:
                    if prev_start is None:
                        prev_start, prev_end = start, end
                        continue
                    # Solape si el inicio actual es menor a fin previo
                    if start < prev_end:
                        raise serializers.ValidationError(
                            f"Se detectó solape de horarios en el día {dow}."
                        )
                    prev_start, prev_end = start, end

        return attrs

    # --------------------
    # create / update
    # --------------------
    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> Registration:
        """
        Creo la Registration y luego inserto las indisponibilidades si vienen en el payload.
        Aprovecho bulk_create para eficiencia y consistencia bajo transacción.
        """
        unav_data = validated_data.pop("unavailability", None)

        reg = Registration.objects.create(**validated_data)

        if unav_data:
            slots = [
                RegistrationUnavailability(
                    registration=reg,
                    day_of_week=blk["day_of_week"],
                    start_time=blk["start_time"],
                    end_time=blk["end_time"],
                )
                for blk in unav_data
            ]
            RegistrationUnavailability.objects.bulk_create(slots, ignore_conflicts=False)

        return reg

    @transaction.atomic
    def update(self, instance: Registration, validated_data: Dict[str, Any]) -> Registration:
        """
        Actualizo campos simples; si 'unavailability' está presente en el payload:
          - Si es lista vacía -> elimino todas las indisponibilidades.
          - Si tiene elementos -> reemplazo por completo (delete + bulk_create).
        Esto facilita un PATCH que re-sincroniza bloques desde el front con una sola llamada.
        """
        unav_present = "unavailability" in validated_data
        unav_data = validated_data.pop("unavailability", None)

        # Actualizo primitivos/FKs
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean(exclude=None)  # mantengo limpieza a nivel modelo
        instance.save()

        if unav_present:
            # Reemplazo total
            RegistrationUnavailability.objects.filter(registration=instance).delete()
            if unav_data:
                slots = [
                    RegistrationUnavailability(
                        registration=instance,
                        day_of_week=blk["day_of_week"],
                        start_time=blk["start_time"],
                        end_time=blk["end_time"],
                    )
                    for blk in unav_data
                ]
                RegistrationUnavailability.objects.bulk_create(slots, ignore_conflicts=False)

        return instance
