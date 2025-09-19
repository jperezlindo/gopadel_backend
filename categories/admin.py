# categories/admin.py
from django.contrib import admin
# Yo prefiero importar el modelo concreto para evitar depender de __all__ en __init__.py
from categories.models.category import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Yo optimizo el admin de categorías para operar rápido:
    - columnas clave (id, name, is_active)
    - búsqueda por name
    - filtros por activo
    - acciones masivas para activar/desactivar
    """
    list_display = ("id", "name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)           # orden alfabético estable
    list_per_page = 50             # paginación razonable
    save_on_top = True             # botones arriba también

    actions = ("mark_active", "mark_inactive")

    def get_queryset(self, request):
        # Yo traigo solo los campos que uso en la lista (micro-optimización)
        qs = super().get_queryset(request)
        return qs.only("id", "name", "is_active")

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} categorías activadas.")
    mark_active.short_description = "Activar seleccionadas"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} categorías desactivadas.")
    mark_inactive.short_description = "Desactivar seleccionadas"
