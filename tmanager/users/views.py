import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import UserSettings
from .serializers import (
    ChangePasswordSerializer,
    ErrorSerializer,
    LoginRequestSerializer,
    MessageSerializer,
    ResendVerificationRequestSerializer,
    TokenResponseSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
    VerifyEmailRequestSerializer,
)
from .utils import send_verification_email

User = get_user_model()

logger = logging.getLogger(__name__)


class PublicAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class VerifyEmailView(PublicAPIView):
    @extend_schema(
        tags=['Auth'],
        summary='Verify email address',
        request=VerifyEmailRequestSerializer,
        responses={200: MessageSerializer, 400: ErrorSerializer},
    )
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (AttributeError, TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        return Response(
            {'Error': 'This link is invalid or has expired.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CustomLoginView(PublicAPIView):
    @extend_schema(
        tags=['Auth'],
        summary='Log in and get an API token',
        request=LoginRequestSerializer,
        responses={200: TokenResponseSerializer, 400: ErrorSerializer, 403: ErrorSerializer},
    )
    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(
                {'Error': 'Incorrect username or password.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data['user']

        if not user.is_email_verified:
            return Response(
                {'code': 'email_not_verified', 'Error': 'Email is not verified.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'message': 'Logged in successfully.'}, status=status.HTTP_200_OK)


class ResendVerificationEmail(PublicAPIView):
    throttle_scope = 'resend'

    @extend_schema(
        tags=['Auth'],
        summary='Resend the verification email',
        request=ResendVerificationRequestSerializer,
        responses={200: MessageSerializer, 400: ErrorSerializer, 503: ErrorSerializer},
    )
    def post(self, request):
        email = (request.data.get('email') or '').strip()

        if not email:
            return Response({'Error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()

        if user is not None and not user.is_email_verified:
            try:
                send_verification_email(user)
            except Exception:
                logger.exception('Failed to resend verification email to user %s', user.pk)
                return Response(
                    {'Error': 'Could not send the email. Please try again later.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(
            {'message': 'If this email belongs to an unverified account, a verification link has been sent.'},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['Account'], summary='Get the current profile', responses=UserProfileSerializer)
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    @extend_schema(
        tags=['Account'],
        summary='Update the current profile',
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
    )
    def patch(self, request):
        old_email = request.user.email
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email != old_email:
            user.is_email_verified = False
            user.save(update_fields=['is_email_verified'])
            try:
                send_verification_email(user)
            except Exception:
                logger.exception('Failed to send verification email to user %s', user.pk)
        return Response(UserProfileSerializer(user).data)


class UserSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request):
        obj, _ = UserSettings.objects.get_or_create(user=request.user)
        return obj

    @extend_schema(tags=['Account'], summary='Get user settings', responses=UserSettingsSerializer)
    def get(self, request):
        return Response(UserSettingsSerializer(self.get_object(request)).data)

    @extend_schema(
        tags=['Account'],
        summary='Update user settings',
        request=UserSettingsSerializer,
        responses=UserSettingsSerializer,
    )
    def patch(self, request):
        serializer = UserSettingsSerializer(self.get_object(request), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Account'],
        summary='Change password (issues a new token)',
        request=ChangePasswordSerializer,
        responses={200: TokenResponseSerializer},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'message': 'Password changed successfully.'})