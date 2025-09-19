# players/admin.py
from django.contrib import admin
from .models.player import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """
    Yo optimizo el admin de jugadores para backoffice:
    - columnas clave
    - filtros por posición y nivel
    - búsqueda por nick y posición
    - acciones masivas útiles
    """
    list_display = (
        "id",
        "nick_name",
        "position",
        "level",
        "points",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("position", "level", "is_active")
    search_fields = ("nick_name", "position")
    ordering = ("-created_at",)
    list_per_page = 50
    save_on_top = True
    date_hierarchy = "created_at"

    # Si Player tiene FKs grandes (ej. user, city, club), habilito:
    # list_select_related = ("user", "city")
    # autocomplete_fields = ("user", "city")

    actions = ("mark_active", "mark_inactive", "reset_points")

    def get_queryset(self, request):
        # Yo traigo solo los campos usados en la lista (micro-optimización)
        qs = super().get_queryset(request)
        return qs.only(
            "id", "nick_name", "position", "level", "points", "is_active", "created_at", "updated_at"
        )

    # ---- Acciones masivas ----
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} jugadores activados.")
    mark_active.short_description = "Activar seleccionados"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} jugadores desactivados.")
    mark_inactive.short_description = "Desactivar seleccionados"

    def reset_points(self, request, queryset):
        # Yo reseteo puntos a 0 (adaptá si usás otra métrica de base)
        updated = queryset.update(points=0)
        self.message_user(request, f"Puntos reseteados en {updated} jugadores.")
    reset_points.short_description = "Resetear puntos a 0"
