# facilities/admin.py
from django.contrib import admin
# Yo prefiero importar el modelo concreto para no depender del __init__.py
from facilities.models import Facility  # si tienes facilities/models/facility.py, usa: from facilities.models.facility import Facility
# Si Facility tiene FK a City u otras, puedo activar autocomplete más abajo.


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """
    Yo optimizo el admin de instalaciones para backoffice:
    - columnas clave y orden estable
    - filtros y búsqueda
    - acciones masivas (activar/desactivar/borrar lógico/restaurar)
    - micro-optimizaciones del queryset
    """
    list_display = ("id", "name", "address", "courts", "is_active", "is_deleted")
    search_fields = ("name", "address")
    list_filter = ("is_active", "is_deleted")
    ordering = ("name",)
    list_per_page = 50
    save_on_top = True
    readonly_fields = ()  # agrego ("created_at", "updated_at") si existen en el modelo

    # Si Facility tiene FKs grandes (por ejemplo city, owner), yo habilito:
    # list_select_related = ("city", "owner")
    # autocomplete_fields = ("city", "owner")

    actions = ("mark_active", "mark_inactive", "mark_deleted", "mark_undeleted")

    def get_queryset(self, request):
        # Yo traigo solo los campos que uso en la lista para evitar sobrecargar
        qs = super().get_queryset(request)
        return qs.only("id", "name", "address", "courts", "is_active", "is_deleted")

    # ---- Acciones masivas ----
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} instalaciones activadas.")
    mark_active.short_description = "Activar seleccionadas"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} instalaciones desactivadas.")
    mark_inactive.short_description = "Desactivar seleccionadas"

    def mark_deleted(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f"{updated} instalaciones marcadas como eliminadas.")
    mark_deleted.short_description = "Marcar como eliminadas"

    def mark_undeleted(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f"{updated} instalaciones restauradas.")
    mark_undeleted.short_description = "Restaurar seleccionadas"
