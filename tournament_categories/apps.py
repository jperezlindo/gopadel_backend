# tournament_categories/apps.py
from django.apps import AppConfig

class TournamentCategoriesConfig(AppConfig):
    # Yo nombro la app exactamente como en INSTALLED_APPS
    name = "tournament_categories"
    verbose_name = "Tournament Categories"
    default_auto_field = "django.db.models.BigAutoField"
