from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import UserSettings
from .serializers import (
    ChangePasswordSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
)
from .utils import send_verification_email

User = get_user_model()


class PublicAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class VerifyEmailView(PublicAPIView):
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save()
            return Response({'message': 'Email успешно подтвержден'}, status=status.HTTP_200_OK)
        return Response({'Error': 'Ссылка недействительна или устарела'}, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(PublicAPIView):
    def post(self, request):
        try:
            serializer = AuthTokenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
        except Exception:
            return Response({'Error': 'Неверный логин или пароль'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_email_verified:
            return Response({'message': 'Email не подтвержден'}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'message': 'Вход успешен'}, status=status.HTTP_200_OK)


class ResendVerificationEmail(PublicAPIView):
    throttle_scope = 'resend'

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'Error': 'Email не указан'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'Error': 'Пользователь с таким email не найден'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_email_verified:
            return Response({'message': 'Email уже подтвержден'}, status=status.HTTP_200_OK)

        send_verification_email(user)
        return Response({'message': 'Письмо с подтверждением отправлено повторно'}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        old_email = request.user.email
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email != old_email:
            user.is_email_verified = False
            user.save(update_fields=['is_email_verified'])
            send_verification_email(user)
        return Response(UserProfileSerializer(user).data)


class UserSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request):
        obj, _ = UserSettings.objects.get_or_create(user=request.user)
        return obj

    def get(self, request):
        return Response(UserSettingsSerializer(self.get_object(request)).data)

    def patch(self, request):
        serializer = UserSettingsSerializer(self.get_object(request), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'message': 'Пароль изменён'})