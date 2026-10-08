from django.urls import path

from .views import ChangePasswordView, MeView, UserSettingsView, VerifyEmailView

urlpatterns = [
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('me/', MeView.as_view(), name='me'),
    path('settings/', UserSettingsView.as_view(), name='user_settings'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]