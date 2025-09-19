# gopadel_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Import explícito de módulos concretos (evita recorrer packages de urls)
from users.urls import user_urls as users_urls
from tournaments.urls import tournament_urls as tournaments_urls
from players.urls import player_urls as players_urls
from registrations.urls import registration_urls as registrations_urls
from categories.urls import category_urls as categories_urls

urlpatterns = [
    # Admin
    path("admin/v1/", admin.site.urls),

    # OpenAPI / Swagger
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # JWT
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # === APIs versionadas ===
    # Users
    path(
        "api/v1/users/",
        include((users_urls.urlpatterns, users_urls.app_name), namespace="users"),
    ),

    # Tournaments
    path(
        "api/v1/tournaments/",
        include((tournaments_urls.urlpatterns, getattr(tournaments_urls, "app_name", "tournaments")), namespace="tournaments"),
    ),

    # Players
    path(
        "api/v1/players/",
        include((players_urls.urlpatterns, getattr(players_urls, "app_name", "players")), namespace="players"),
    ),

    # Registrations (aunque el módulo no declare app_name, lo forzamos acá)
    path(
        "api/v1/registrations/",
        include((registrations_urls.urlpatterns, getattr(registrations_urls, "app_name", "registrations")), namespace="registrations"),
    ),

    # # Categories
    # path(
    #     "api/v1/categories/",
    #     include((categories_urls.urlpatterns, getattr(categories_urls, "app_name", "categories")), namespace="categories"),
    # ),

    # Tournament Categories: interno (sin endpoint público)
    # path("api/v1/tournament-categories/", include(("tournament_categories.urls.tournament_categories_urls", "tournament_categories"), namespace="tournament_categories")),
]
