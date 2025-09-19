# roles/admin.py
from django.contrib import admin
# Yo prefiero importar explícito el modelo concreto
from roles.models import Rol  # si tenés roles/models/rol.py: from roles.models.rol import Rol


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    """
    Yo optimizo el admin de Roles para operar rápido:
    - columnas clave (id, name, activo, borrado)
    - búsqueda por nombre
    - filtros por flags
    - acciones masivas activar/desactivar/borrar lógico/restaurar
    - orden y paginación razonables
    """
    list_display = ("id", "name", "is_active", "is_deleted")
    search_fields = ("name",)
    list_filter = ("is_active", "is_deleted")
    ordering = ("name",)       # yo ordeno alfabéticamente para ubicar rápido
    list_per_page = 50
    save_on_top = True

    actions = ("mark_active", "mark_inactive", "mark_deleted", "mark_undeleted")

    def get_queryset(self, request):
        # Yo traigo solo los campos usados en la lista (micro-optimización)
        qs = super().get_queryset(request)
        return qs.only("id", "name", "is_active", "is_deleted")

    # ---- Acciones masivas ----
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} roles activados.")
    mark_active.short_description = "Activar seleccionados"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} roles desactivados.")
    mark_inactive.short_description = "Desactivar seleccionados"

    def mark_deleted(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f"{updated} roles marcados como eliminados.")
    mark_deleted.short_description = "Marcar como eliminados"

    def mark_undeleted(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f"{updated} roles restaurados.")
    mark_undeleted.short_description = "Restaurar seleccionados"
