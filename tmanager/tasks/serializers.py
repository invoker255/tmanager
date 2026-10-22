from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Task

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    days_left = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'category', 'created_at', 'deadline', 'days_left', 'user',
        ]

    def validate_deadline(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError('Deadline date cannot be in the past!')
        return value

    @extend_schema_field({'type': 'string', 'nullable': True, 'example': 'Days left: 3'})
    def get_days_left(self, obj):
        if not obj.deadline:
            return None
        delta = obj.deadline - timezone.now()
        if delta.total_seconds() < 0:
            return 'Missed'
        return f'Days left: {delta.days}'

    def update(self, instance, validated_data):
        if 'deadline' in validated_data and validated_data['deadline'] != instance.deadline:
            instance.reminder_sent = False
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate(self, attrs):
        candidate = User(username=attrs.get('username', ''), email=attrs.get('email', ''))
        try:
            validate_password(attrs['password'], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email', '')
        return User.objects.create_user(email=email, password=password, **validated_data)


class RegisteredUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class RegisterResponseSerializer(serializers.Serializer):
    user = RegisteredUserSerializer()
    email_sent = serializers.BooleanField()
    message = serializers.CharField()