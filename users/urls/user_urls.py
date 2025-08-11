from django.urls import path
from users.views.user_view import UserListCreateView, UserRetrieveUpdateDestroyView
from users.views.change_password_view import ChangePasswordView

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:user_id>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('<int:user_id>/change-password/', ChangePasswordView.as_view(), name='users_change_password'),
]
