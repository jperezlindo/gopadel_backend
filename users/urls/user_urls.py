# users/urls.py
from django.urls import path
from users.views.user_view import UserListCreateView, UserDetailView, UserChangePasswordView

urlpatterns = [
    path("", UserListCreateView.as_view(), name="user_list_create"),
    path("<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("<int:pk>/change-password/", UserChangePasswordView.as_view(), name="user_change_password"),
]
