# tournaments/schemas/tournament_serializers.py
from typing import Any, Dict, Optional, cast
from rest_framework import serializers
from tournaments.models.tournament import Tournament
from facilities.models import Facility  # ajusta el import si tu app es distinta


# --------- Read Serializer (show/list) ---------
class TournamentSerializer(serializers.ModelSerializer):
    # Exponemos el entero facility_id (Django provee <fk>_id)
    facility_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tournament
        fields = [
            'id',
            'name',
            'date_start',
            'date_end',
            'is_active',
            'created_at',
            'updated_at',
            'facility_id',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'facility_id']


# --------- Create Serializer ---------
class CreateTournamentSerializer(serializers.ModelSerializer):
    # aceptamos facility_id como entrada (write), mapeando al FK "facility"
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source='facility',
        write_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            'name',
            'date_start',
            'date_end',
            'is_active',
            'facility_id',
        ]

    def validate_name(self, value: str) -> str:
        # Garantiza longitud <= 5 y no vacío (ya lo valida el modelo, pero explícito aquí)
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        if len(v) > 100:
            raise serializers.ValidationError("El nombre debe tener como máximo 100 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        date_start = attrs.get('date_start')
        date_end = attrs.get('date_end')
        if date_end and date_start and date_end < date_start:
            raise serializers.ValidationError({
                'date_end': 'La fecha de finalización no puede ser anterior a la fecha de inicio.'
            })
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Tournament:
        # validated_data ya trae 'facility' (no 'facility_id') por el source del field
        return Tournament.objects.create(**validated_data)


# --------- Update/Patch Serializer ---------
class UpdateTournamentSerializer(serializers.ModelSerializer):
    # facility_id opcional en update
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source='facility',
        required=False,
        write_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            'name',
            'date_start',
            'date_end',
            'is_active',
            'facility_id',
        ]
        extra_kwargs = {
            'name': {'required': False},
            'date_start': {'required': False},
            'date_end': {'required': False},
            'is_active': {'required': False},
        }

    def validate_name(self, value: str) -> str:
        v = (value or '').strip()
        if len(v) == 0:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        if len(v) > 100:
            raise serializers.ValidationError("El nombre debe tener como máximo 100 caracteres.")
        return v

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Al ser parcial, tomamos valores actuales si no vienen en attrs
        instance =  cast(Optional[Tournament], getattr(self, 'instance', None))
        date_start = attrs.get('date_start', getattr(instance, 'date_start', None))
        date_end = attrs.get('date_end', getattr(instance, 'date_end', None))
        if date_end and date_start and date_end < date_start:
            raise serializers.ValidationError({
                'date_end': 'La fecha de finalización no puede ser anterior a la fecha de inicio.'
            })
        return attrs

    def update(self, instance: Tournament, validated_data: Dict[str, Any]) -> Tournament:
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
