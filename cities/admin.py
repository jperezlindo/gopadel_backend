# cities/admin.py
from django.contrib import admin
# Yo prefiero importar el modelo concreto para no depender de __init__.py
from cities.models import City  # si tenés cities/models/city.py, podés hacer: from cities.models.city import City


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """
    Yo optimizo el admin de ciudades para operar más rápido:
    - columnas clave
    - filtros y búsqueda
    - acciones masivas activar/desactivar/restaurar/borrar lógico (si aplica)
    - orden y paginación razonables
    """
    list_display = ("id", "name", "cod", "is_active", "is_deleted")
    search_fields = ("name", "cod")
    list_filter = ("is_active", "is_deleted")
    ordering = ("name",)          # orden alfabético estable
    list_per_page = 50
    save_on_top = True

    # Si tu City tiene FKs (ej. province, country) podés habilitar:
    # list_select_related = ("province", "country")
    # autocomplete_fields = ("province", "country")
    # y agregarlas a list_display/list_filter si las usás.

    actions = ("mark_active", "mark_inactive", "mark_deleted", "mark_undeleted")

    def get_queryset(self, request):
        # Yo traigo solo los campos que uso en la lista para evitar sobrecargar
        qs = super().get_queryset(request)
        return qs.only("id", "name", "cod", "is_active", "is_deleted")

    # ---- Acciones masivas ----
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} ciudades activadas.")
    mark_active.short_description = "Activar seleccionadas"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} ciudades desactivadas.")
    mark_inactive.short_description = "Desactivar seleccionadas"

    def mark_deleted(self, request, queryset):
        # Yo asumo borrado lógico con flag is_deleted
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f"{updated} ciudades marcadas como eliminadas.")
    mark_deleted.short_description = "Marcar como eliminadas"

    def mark_undeleted(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f"{updated} ciudades restauradas.")
    mark_undeleted.short_description = "Restaurar seleccionadas"
