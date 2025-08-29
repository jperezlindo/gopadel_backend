# gopadel_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/v1/', admin.site.urls),

    # Swagger/OpenAPI schema y UI
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Users API
    path('api/v1/users/', include('users.urls.user_urls')),

    # Tournaments API
    path('api/v1/tournaments/', include('tournaments.urls.tournament_urls')),

    # Players API
    path('api/v1/players/', include('players.urls.player_urls')),

    # ⚠️ REMOVIDO: Tournament Categories API (ahora es interno, no público)
    # path('api/v1/tournament-categories/', include('tournament_categories.urls.tournament_categories_urls')),
]
