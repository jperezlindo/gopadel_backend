# users/urls/user_urls.py
from django.urls import path
from users.views.user_view import (
    UserListCreateView,
    UserDetailView,
    UserChangePasswordView,
)

# Defino app_name para namespacing en el proyecto (permite usar 'users:user_detail', etc.).
app_name = "users"

urlpatterns = [
    # Listado paginado + creación
    # GET  -> /api/v1/users/
    # POST -> /api/v1/users/
    path("", UserListCreateView.as_view(), name="user_list_create"),

    # Detalle / actualización / borrado lógico
    # GET    -> /api/v1/users/<id>/
    # PUT    -> /api/v1/users/<id>/
    # PATCH  -> /api/v1/users/<id>/
    # DELETE -> /api/v1/users/<id>/
    path("<int:pk>/", UserDetailView.as_view(), name="user_detail"),

    # Cambio de password
    # POST -> /api/v1/users/<id>/change-password/
    path("<int:pk>/change-password/", UserChangePasswordView.as_view(), name="user_change_password"),
]
