# tournament_categories/admin.py
from django.contrib import admin
from django.db.models import QuerySet
from tournament_categories.models.tournament_category import TournamentCategory


@admin.register(TournamentCategory)
class TournamentCategoryAdmin(admin.ModelAdmin):
    # Yo muestro columnas clave y un precio formateado
    list_display = ("id", "tournament", "name", "category", "price_display", "is_active", "created_at")
    list_filter  = ("is_active", "tournament", "category")
    search_fields = ("name", "tournament__name", "category__name", "comment")
    ordering = ("tournament", "name")
    autocomplete_fields = ("tournament", "category")
    readonly_fields = ("created_at", "updated_at")

    # QoL en el admin
    save_on_top = True
    date_hierarchy = "created_at"
    list_select_related = ("tournament", "category")

    # Acciones masivas: yo agrego activar/desactivar de forma rápida
    actions = ("mark_active", "mark_inactive")

    def get_queryset(self, request):
        # Yo optimizo el queryset base para evitar N+1 al listar
        qs = super().get_queryset(request)
        return qs.select_related("tournament", "category")

    def price_display(self, obj: TournamentCategory) -> str:
        # Yo muestro el precio con 2 decimales, sin forzar símbolo de moneda
        return f"{obj.price:.2f}"
    price_display.short_description = "Price"

    def mark_active(self, request, queryset: QuerySet[TournamentCategory]):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} categorías activadas.")
    mark_active.short_description = "Activar seleccionadas"

    def mark_inactive(self, request, queryset: QuerySet[TournamentCategory]):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} categorías desactivadas.")
    mark_inactive.short_description = "Desactivar seleccionadas"
