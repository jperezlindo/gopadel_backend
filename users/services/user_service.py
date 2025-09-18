# users/services/user_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from users.models.user import CustomUser
from users.repositories.user_repository import UserRepository


class UserService:
    """
    Orquesto reglas de negocio para Users, manteniendo a los controllers
    libres de lógica y al repositorio enfocado en el ORM.

    Decisiones:
    - Cuando un recurso no existe, levanto DjangoValidationError con code="not_found"
      para que el custom_exception_handler lo mapee a 404 (vía error_mapper).
    - En operaciones de escritura uso transaction.atomic() para garantizar atomicidad.
    - No manejo password en update() general: expongo change_password() como flujo dedicado.
    """

    def __init__(self, repository: Optional[UserRepository] = None):
        # Permito inyectar un repo para tests; por defecto uso el real.
        self.repository = repository or UserRepository()

    # =========================
    # Lectura
    # =========================
    def list(self) -> Any:
        """
        Devuelvo un QuerySet listo para ser paginado/filtrado por la vista.
        El repositorio ya excluye soft-deleted y superusers para UI operativa.
        """
        return self.repository.get_all_users()

    def get(self, user_id: int) -> CustomUser:
        """
        Obtengo un usuario por PK respetando soft-delete.
        Si no existe, levanto ValidationError con code='not_found' para 404.
        """
        instance = self.repository.get_user_by_id(user_id)
        if not instance:
            raise DjangoValidationError({"detail": ["User not found."]}, code="not_found")
        return instance

    # =========================
    # Escritura
    # =========================
    def create(self, data: Dict) -> CustomUser:
        """
        Creo un usuario delegando en el repo (que a su vez usa el manager).
        - El serializer ya normaliza/valida email y mapea *_id → FK reales.
        - Hago full_clean() para reforzar validaciones de modelo antes de persistir.
        """
        with transaction.atomic():
            instance = self.repository.create_user(data)
            instance.full_clean()
            instance.save()
            return instance

    def update(self, user_id: int, data: Dict) -> CustomUser:
        """
        Actualizo campos simples del usuario sin tocar password (flujo dedicado).
        Si el usuario no existe, levanto not_found.
        """
        with transaction.atomic():
            instance = self.repository.update_user(user_id, data)
            if not instance:
                raise DjangoValidationError({"detail": ["User not found."]}, code="not_found")
            instance.full_clean()
            instance.save()
            return instance

    def delete(self, user_id: int) -> None:
        """
        Soft-delete del usuario (is_deleted=True, is_active=False).
        Si no existe, levanto not_found.
        """
        ok = self.repository.delete_user(user_id)
        if not ok:
            raise DjangoValidationError({"detail": ["User not found."]}, code="not_found")

    # =========================
    # Password
    # =========================
    def change_password(
        self,
        actor: CustomUser,
        target_user_id: int,
        *,
        old_password: Optional[str],
        new_password: str,
    ) -> CustomUser:
        """
        Cambio de password con reglas:
        - Admin (superuser/staff): puede cambiar la contraseña de cualquiera sin old_password.
        - Usuario final: solo puede cambiar la propia y debe enviar old_password correcto.
        - Old y new no pueden ser iguales.
        - Si el target no existe, levanto not_found.
        """
        with transaction.atomic():
            user = self.repository.get_user_by_id(target_user_id)
            if not user:
                raise DjangoValidationError({"detail": ["User not found."]}, code="not_found")

            is_admin = bool(actor.is_superuser or actor.is_staff)
            is_self = actor.pk == user.pk

            if not is_admin:
                if not is_self:
                    # Mensaje claro para UI en flujos no administradores
                    raise DjangoValidationError({"detail": ["You are not allowed to change this password."]})
                if not old_password:
                    raise DjangoValidationError({"old_password": ["This field is required."]})
                if not user.check_password(old_password):
                    raise DjangoValidationError({"old_password": ["Incorrect password."]})

            if old_password and old_password == new_password:
                raise DjangoValidationError({"new_password": ["New password must be different from old password."]})

            user.set_password(new_password)
            user.save(update_fields=["password", "updated_at"])
            return user
