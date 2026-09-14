from django.urls import path
from .views import VerifyEmailView
urlpatterns = [
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
]