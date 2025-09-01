# registrations/urls/registration_urls.py
from django.urls import path
from registrations.views.registration_view import ( 
    RegistrationListCreateView,
    RegistrationDetailView,
)

urlpatterns = [
    path("", RegistrationListCreateView.as_view(), name="registration_list_create"),
    path("<int:pk>/", RegistrationDetailView.as_view(), name="registration_detail"),
]
