# tournaments/admin.py
from django.contrib import admin
from .models.tournament import Tournament
from tournament_categories.models.tournament_category import TournamentCategory


class TournamentCategoryInline(admin.TabularInline):
    """
    Yo uso un inline para crear/editar categorías del torneo
    directamente desde la pantalla del torneo.
    """
    model = TournamentCategory
    extra = 1
    fields = ("name", "category", "price", "is_active", "comment")
    autocomplete_fields = ("category",)
    show_change_link = True


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """
    Versión robusta sin campos “extra” de DB.
    Si después confirmamos más campos (facility, date_start, etc.),
    los agrego sin drama.
    """
    list_display = (
        "id",
        "name",
        "is_active",
        "categories_count",  # solo usa el related_name, no columna en DB
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("id",)
    list_per_page = 50
    save_on_top = True
    inlines = [TournamentCategoryInline]

    # Si tu modelo tiene estos campos, los puedo habilitar:
    # list_display += ("facility",)
    # list_display += ("date_start", "date_end",)
    # list_filter += ("facility",)
    # autocomplete_fields = ("facility",)
    # list_select_related = ("facility",)
    # readonly_fields = ("created_at", "updated_at")

    def categories_count(self, obj):
        # Yo cuento por related_name (no es una columna de DB)
        return obj.tournament_categories.count()
    categories_count.short_description = "Categories"
