from django.urls import path
from .views import VerifyEmailView, CustomLoginView

urlpatterns = [
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),

]