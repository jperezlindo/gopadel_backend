# users/schemas/user_serializer.py
from typing import Any, Dict, Optional
from django.contrib.auth import get_user_model
from rest_framework import serializers

from facilities.models import Facility
from cities.models import City
from roles.models import Rol

from players.schemas.player_serializer import PlayerMiniSerializer

# Nota: uso get_user_model() para evitar acoplarme al nombre del modelo.
User = get_user_model()


# =========================
# Read Serializer (show/list)
# =========================
class UserSerializer(serializers.ModelSerializer):
    """
    Defino el serializer de lectura para exponer al front solo la información
    necesaria y en un formato cómodo. La idea es que el cliente no tenga que
    resolver relaciones y pueda trabajar con IDs simples.
    """
    # Exposición de FKs como *_id para consumo simple desde el front.
    facility_id = serializers.IntegerField(source='facility.id', read_only=True)
    city_id = serializers.IntegerField(source='city.id', read_only=True)
    rol_id = serializers.IntegerField(source='rol.id', read_only=True)

    # is_staff lo dejo explícitamente read-only (evito que el front lo toque).
    is_staff = serializers.BooleanField(read_only=True)

    # Relación con Player: uso mini serializer para no cargar todo el objeto.
    player = PlayerMiniSerializer(read_only=True)

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
        # Mantengo campos de solo lectura para proteger integridad/seguridad.
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "facility_id",
            "city_id",
            "rol_id",
            "is_deleted",   # protejo soft-delete desde lectura general
            "is_staff",     # protejo privilegios
            "email",        # ante posibles cambios, lo controlo por endpoint específico
        ]


# =========================
# Create Serializer
# =========================
class CreateUserSerializer(serializers.ModelSerializer):
    """
    Defino el serializer de creación de usuarios. La responsabilidad es:
    - Validar unicidad y normalización de email.
    - Hashear password delegando en create_user del manager.
    - Aceptar FKs por ID (facility_id, city_id, rol_id) para simplicidad del front.
    - Proteger flags sensibles (is_staff, is_deleted) como read-only.
    """
    # El password va write_only y aplico un mínimo razonable.
    password = serializers.CharField(write_only=True, min_length=6)

    # Acepto IDs y DRF los mapea a las FKs (nombres *_id en payload → source='*').
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

    # Flags: expongo is_active opcional; marco is_deleted/is_staff como read-only por seguridad.
    is_active = serializers.BooleanField(required=False, default=True)

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
            # Los siguientes dos quedan intencionalmente fuera de escritura pública.
            # Si hiciera falta, más adelante expongo un serializer/admin endpoint.
            # "is_deleted",
            # "is_staff",
            "facility_id",
            "city_id",
            "rol_id",
        ]
        read_only_fields = [
            "is_deleted",
            "is_staff",
        ]

    def validate_email(self, value: str) -> str:
        """
        Normalizo el email (trim + lower) y valido unicidad case-insensitive.
        Con esto evito duplicados por mayúsculas/minúsculas.
        """
        v = (value or "").strip().lower()
        if User.objects.filter(email__iexact=v).exists():
            # Mensaje claro para la UI
            raise serializers.ValidationError("Este email ya está registrado.")
        return v

    def create(self, validated_data: Dict[str, Any]) -> User:  # type: ignore
        """
        Creo el usuario delegando en create_user del manager:
        - Se encarga de hashear el password y setear defaults coherentes.
        """
        password = validated_data.pop("password")
        # create_user hashea el password y respeta flags por defecto seguros.
        user = User.objects.create_user(password=password, **validated_data)
        return user


# =========================
# Update/Patch Serializer
# =========================
class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Defino el serializer de actualización (PUT/PATCH). El objetivo es:
    - Permitir cambios parciales sin forzar todos los campos.
    - Proteger campos sensibles (is_staff, is_deleted) como solo lectura aquí.
    - Aceptar FKs por ID mediante *_id write_only mapeando a las relaciones.
    """
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
            # Protejo estos flags para que no se modifiquen desde este endpoint general.
            # Si se necesita administrar roles/borrados, lo manejo en servicios/serializers dedicados.
            # "is_deleted",
            # "is_staff",
            "facility_id",
            "city_id",
            "rol_id",
        ]
        # Todos opcionales para PATCH/PUT (la vista decide partial).
        extra_kwargs = {f: {"required": False} for f in fields}
        read_only_fields = [
            "is_deleted",
            "is_staff",
        ]

    def validate_email(self, value: Optional[str]) -> Optional[str]:
        """
        Si el email se envía, lo normalizo y valido que no colisione con otro usuario.
        Excluyo el propio PK en caso de update para permitir mantener el mismo email.
        """
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
        """
        Aplico las actualizaciones campo por campo.
        Nota: el cambio de password se maneja por un endpoint/serializer específico.
        """
        for field, val in validated_data.items():
            setattr(instance, field, val)
        instance.save()
        return instance
